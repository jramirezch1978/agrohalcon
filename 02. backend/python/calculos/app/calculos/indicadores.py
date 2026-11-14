"""Cálculo 1: indicadores del estado actual.

Método (igual para cualquier coordenada del mundo):
- "Actual" = promedio de los últimos `ventana_dias` días con datos de NASA POWER (diaria).
- "Normal" = climatología NASA POWER 2001-2025 del mismo mes. Si la ventana cruza dos meses,
  la normal es el promedio de las normales mensuales ponderado por los días de cada mes.
- Nivel = reglas de config/umbrales.yaml.

Las funciones `nivel_*` son puras (sin red) para poder probarlas con datos fijos.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import pandas as pd

from app.config import umbrales
from app.fuentes.nasa_power import ANIOS_NORMAL, ClienteNasaPower
from app.textos.plantillas import UNIDADES, signo, texto

FUENTE_POWER = "NASA POWER"

# Reglas puras (reexportadas para los tests y otros cálculos)
from app.calculos.reglas import (  # noqa: E402,F401
    anomalia_pct, nivel_calor, nivel_el_nino, nivel_humedad, nivel_lluvia, nivel_por_corte,
)
from app.calculos.el_nino import indicador_el_nino  # noqa: E402
from app.fuentes.piura import punto_cercano  # noqa: E402
from app.fuentes.selector import humedad_actual_smap, lluvia_actual_imerg, ultimo_dato_imerg, vegetacion_ndvi  # noqa: E402


# ---------- Ayudas de series ----------

def ventana_reciente(diario: pd.DataFrame, columnas: list[str], dias: int) -> pd.DataFrame:
    """Últimos `dias` días calendario que terminan en el último día con TODAS las columnas válidas."""
    validos = diario[columnas].dropna()
    if validos.empty:
        raise ValueError("NASA POWER no devolvió días válidos para esta coordenada")
    fin = validos.index.max()
    inicio = fin - pd.Timedelta(days=dias - 1)
    return diario.loc[inicio:fin, columnas]


def normal_ponderada(clim_mensual: pd.Series, fechas: pd.DatetimeIndex) -> float:
    """Promedio de la climatología del mes de cada día de la ventana (= ponderado por días)."""
    return float(clim_mensual.loc[fechas.month].mean())


def normal_misma_ventana(historica: pd.Series, fechas: pd.DatetimeIndex) -> float:
    """Promedio de la serie histórica en los mismos días del año que la ventana (todos los años)."""
    dias = set(zip(fechas.month, fechas.day))
    mascara = [(m, d) in dias for m, d in zip(historica.index.month, historica.index.day)]
    return float(historica[mascara].mean())


def _r(x: float, nd: int) -> float:
    return round(float(x), nd)


# ---------- Datos de NASA POWER (compartidos por indicadores y campaña) ----------

DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


@dataclass
class DatosPower:
    diario: pd.DataFrame      # últimos ~50 días
    clim: pd.DataFrame        # climatología mensual 2001-2025 (índice 1..12)
    hist: pd.DataFrame        # serie diaria 2001-2025 de T2M_MAX y T2M_MIN


async def obtener_datos_power(lat: float, lon: float, cliente: ClienteNasaPower, hoy: date, dias: int) -> DatosPower:
    # Se piden 20 días extra para cubrir la latencia (~3 días) de la serie diaria.
    # Las tres peticiones van en paralelo; después quedan en caché 24 h.
    a0, a1 = ANIOS_NORMAL
    diario, clim, hist = await asyncio.gather(
        cliente.diario(lat, lon, hoy - timedelta(days=dias + 20), hoy),
        cliente.climatologia(lat, lon),
        cliente.diario(lat, lon, date(a0, 1, 1), date(a1, 12, 31), parametros=["T2M_MAX", "T2M_MIN"]),
    )
    return DatosPower(diario, clim, hist)


def clima_mensual(datos: DatosPower) -> pd.DataFrame:
    """Clima normal de cada mes (índice 1..12) en la coordenada, para la campaña:
    lluvia (mm/día y mm/mes), y media de las máximas y de las mínimas DIARIAS (no los extremos)."""
    lluvia_dia = datos.clim["PRECTOTCORR"]
    por_mes = datos.hist.groupby(datos.hist.index.month)
    return pd.DataFrame({
        "lluvia_mm_dia": lluvia_dia,
        "lluvia_mm_mes": lluvia_dia * pd.Series(DIAS_MES, index=range(1, 13)),
        "tmax": por_mes["T2M_MAX"].mean(),
        "tmin": por_mes["T2M_MIN"].mean(),
    })


# ---------- Orquestación ----------

async def calcular_indicadores(lat: float, lon: float, lang: str, cliente: ClienteNasaPower,
                               hoy: date | None = None, datos: DatosPower | None = None) -> dict[str, Any]:
    u = umbrales()
    dias = int(u["ventana_dias"])
    hoy = hoy or date.today()
    unidades = UNIDADES.get(lang, UNIDADES["es"])

    datos = datos or await obtener_datos_power(lat, lon, cliente, hoy, dias)
    diario, clim, hist_tmax = datos.diario, datos.clim, datos.hist

    v = ventana_reciente(diario, ["PRECTOTCORR", "GWETTOP", "T2M_MAX"], dias)
    fechas = v.index
    periodo = {"inicio": fechas.min().date().isoformat(), "fin": fechas.max().date().isoformat(), "dias": dias}

    # Lluvia: GPM IMERG si la coordenada está en el piloto de Piura y hay datos; si no, NASA POWER
    sat = lluvia_actual_imerg(lat, lon, dias, hoy)
    if sat:
        ll_act, ll_nor = sat["valor"], sat["normal"]
        ll_extra = {"fuente": sat["fuente"], "parametro": sat["parametro"], "periodo": sat["periodo"], "punto": sat["punto"],
                    "ultimoDato": sat["ultimoDato"]}
        if sat["desactualizado"]:
            ll_extra["aviso"] = texto(lang, "aviso_imerg_viejo", fecha=sat["ultimoDato"])
    else:
        ll_act = float(v["PRECTOTCORR"].mean())
        ll_nor = normal_ponderada(clim["PRECTOTCORR"], fechas)
        ll_extra = {"fuente": FUENTE_POWER, "parametro": "PRECTOTCORR"}
        # En Piura NUNCA se cae a NASA POWER en silencio: se dice desde cuándo falta IMERG
        if (ultimo := ultimo_dato_imerg(lat, lon)) is not None:
            ll_extra["aviso"] = texto(lang, "aviso_imerg_sin", fecha=ultimo.isoformat())
    ll_niv, ll_anom, ll_dir = nivel_lluvia(ll_act, ll_nor, u["lluvia"])
    ll_txt = "lluvia_seca" if ll_dir == "estacion_seca" else f"lluvia_{ll_dir}"
    if ll_dir == "exceso" and ll_anom > 200:      # "+5700 %" se lee mal: mejor "58 veces lo normal"
        ll_txt = "lluvia_veces"

    # Humedad del suelo: SMAP (satélite, 9 km) en Piura; si no hay dato, GWETTOP de NASA POWER con aviso
    smap = humedad_actual_smap(lat, lon, hoy)
    if smap:
        hs_act, hs_nor = smap["valor"], smap["normal"]
        hs_extra = {"fuente": smap["fuente"], "parametro": smap["parametro"], "periodo": smap["periodo"],
                    "punto": smap["punto"], "ultimoDato": smap["ultimoDato"]}
    else:
        hs_act = float(v["GWETTOP"].mean())
        hs_nor = normal_ponderada(clim["GWETTOP"], fechas)
        hs_extra = {"fuente": FUENTE_POWER, "parametro": "GWETTOP"}
        if punto_cercano(lat, lon):
            hs_extra["aviso"] = texto(lang, "aviso_smap_sin")
    hs_niv, hs_anom, hs_dir = nivel_humedad(hs_act, hs_nor, u["humedad_suelo"])

    # Vegetación: NDVI de MODIS (250 m). Solo informa el estado del cultivo (no cambia el riesgo climático)
    ndvi = vegetacion_ndvi(lat, lon)

    # Calor: promedio de máximas diarias vs promedio de máximas diarias de los MISMOS días en 2001-2025
    ca_act = float(v["T2M_MAX"].mean())
    ca_nor = normal_misma_ventana(hist_tmax["T2M_MAX"], fechas)
    ca_dif = ca_act - ca_nor
    ca_niv = nivel_calor(ca_dif, u["calor"])

    indicadores = {
        "lluvia": {
            "valor": _r(ll_act, 2), "normal": _r(ll_nor, 2), "unidad": unidades["lluvia"],
            "anomalia": _r(ll_anom, 1), "unidadAnomalia": "%", "direccion": ll_dir,
            "nivel": ll_niv, **ll_extra,
            "detalle": texto(lang, ll_txt, abs=abs(ll_anom), dias=dias, valor=ll_act, normal=ll_nor,
                             veces=ll_act / ll_nor if ll_nor else 0),
        },
        "humedadSuelo": {
            "valor": _r(hs_act, 3), "normal": _r(hs_nor, 3), "unidad": unidades["humedadSuelo"],
            "anomalia": _r(hs_anom, 1), "unidadAnomalia": "%", "direccion": hs_dir,
            "nivel": hs_niv, **hs_extra,
            "detalle": texto(lang, f"humedad_{hs_dir}", abs=abs(hs_anom), dias=dias),
        },
        "calor": {
            "valor": _r(ca_act, 1), "normal": _r(ca_nor, 1), "unidad": unidades["calor"],
            "anomalia": _r(ca_dif, 1), "unidadAnomalia": "°C", "direccion": "exceso" if ca_dif >= 0 else "deficit",
            "nivel": ca_niv, "fuente": FUENTE_POWER, "parametro": "T2M_MAX (mismos días, 2001-2025)",
            "detalle": texto(lang, "calor", signo=signo(ca_dif), diff=abs(ca_dif), valor=ca_act, normal=ca_nor),
        },
        # MUR SST precalculado (data/precalculado/mur_sst_nino12.json); sin archivo → "sin dato"
        "elNino": indicador_el_nino(lat, lon, lang, u, hoy),
    }
    if ndvi:
        anom = (ndvi["valor"] / ndvi["normal"] - 1) * 100 if ndvi["normal"] else 0.0
        nivel_v = "alto" if anom <= -30 else "medio" if anom <= -15 else "bajo"
        indicadores["vegetacion"] = {
            "valor": _r(ndvi["valor"], 3), "normal": _r(ndvi["normal"], 3), "unidad": "NDVI",
            "anomalia": _r(anom, 1), "unidadAnomalia": "%", "direccion": "deficit" if anom < 0 else "exceso",
            "nivel": nivel_v, "fuente": ndvi["fuente"], "parametro": ndvi["parametro"], "punto": ndvi["punto"],
            "ultimoDato": ndvi["fecha"],
            "detalle": texto(lang, "vegetacion_deficit" if anom < 0 else "vegetacion_exceso", abs=abs(anom), valor=ndvi["valor"]),
        }

    # Datos NASA usados (Java los graba en nasa.datos_nasa: regla del doc 29, Python no toca la BD)
    datos_nasa = []
    for clave, ind in indicadores.items():
        if ind.get("valor") is None or ind.get("fuente") in (None, "sin dato"):
            continue
        fecha = ind.get("ultimoDato") or (ind.get("periodo") or periodo)["fin"]
        datos_nasa.append({"lat": lat, "lon": lon, "fecha": str(fecha)[:10], "fuente": ind["fuente"],
                           "variable": f"{ind.get('parametro', clave)}:{clave}"[:200], "valor": ind["valor"]})

    return {
        "lat": lat, "lon": lon, "fecha": hoy.isoformat(), "lang": lang,
        "periodo": periodo,
        "indicadores": indicadores,
        "datosNasa": datos_nasa,
        "metodo": {
            "actual": f"Promedio de los últimos {dias} días con datos (NASA POWER diaria, comunidad AG)",
            "normal": "Lluvia y humedad: climatología NASA POWER 2001-2025 del mismo mes, ponderada por días. "
                      "Calor: promedio de T2M_MAX diario en los mismos días del año, 2001-2025",
            "nota": "NASA POWER es un modelo/reanálisis (MERRA-2, GEOS-IT, CERES) con celdas de ~50 km, "
                    "no una medición en la parcela.",
        },
    }
