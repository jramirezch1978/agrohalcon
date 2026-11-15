"""Cálculo 6: validación histórica ("máquina del tiempo"), p. ej. El Niño costero 2017.

Todo sale de datos reales; nada se escribe a mano salvo el resumen de la realidad (INDECI) de 2017.
- Lluvia: GPM IMERG Final mensual en Piura (punto más cercano a < 25 km); fuera, NASA POWER mensual.
- Humedad del suelo y NDVI: null y "sin dato" hasta integrar SMAP y MODIS.
- Alerta: entre diciembre del año anterior y abril, con las MISMAS reglas y umbrales de hoy:
  * con serie MUR SST que cubra la ventana: primera semana con El Niño en nivel medio o alto;
  * si no: primer mes con lluvia en nivel alto por exceso (IMERG o POWER), fechado al ÚLTIMO día del mes
    (antes no se conoce el total del mes) y con una nota.
- semanasAnticipacion = semanas completas entre la alerta y el inicio del mes de lluvia máxima del año
  (0 si la alerta llegó después; null si no hubo alerta).
"""
from __future__ import annotations

import calendar
from datetime import date
from typing import Any

import pandas as pd

from app.calculos.detalle_lluvia import dias_imerg
from app.calculos.el_nino import primera_alerta
from app.calculos.reglas import nivel_lluvia
from app.config import umbrales
from app.fuentes.nasa_power import ClienteNasaPower, NasaPowerError
from app.fuentes.piura import punto_cercano
from app.fuentes.precalculado import imerg_piura, serie_mur
from app.fuentes.selector import lluvia_mensual_imerg
from app.textos.plantillas import nombre_mes, signo, texto

SIN_DATO = "sin dato"


def _serie_vacia(unidad: str) -> dict:
    return {"unidad": unidad, "fuente": SIN_DATO, "valores": [None] * 12, "normal": [None] * 12}


def _mes_en_curso(serie: dict, anio: int, lat: float, lon: float) -> None:
    """El mes que aún no termina no tiene total mensual: se muestra la suma de los días que ya tienen dato
    (IMERG Late diario), marcada como parcial. No se usa para la alerta ni para el mes de lluvia máxima."""
    hoy = date.today()
    for m in range(12, 0, -1):
        if serie["valores"][m - 1] is not None:
            break
        if (anio, m) > (hoy.year, hoy.month):
            continue
        d = dias_imerg(lat, lon, anio, m)
        if d is not None:
            fechas = [date(anio, m, i + 1) for i, v in enumerate(d[0]) if v is not None]
            serie["valores"][m - 1] = round(sum(v for v in d[0] if v is not None), 1)
            serie["parcial"] = {"mes": m, "hasta": fechas[-1].isoformat(), "dias": len(fechas)}
        break


async def serie_lluvia(anio: int, lat: float, lon: float, cliente: ClienteNasaPower) -> tuple[dict, float | None]:
    """(serie de lluvia del año en mm/mes, lluvia de diciembre del año anterior)."""
    imerg = lluvia_mensual_imerg(lat, lon, anio)
    if imerg:
        previo = lluvia_mensual_imerg(lat, lon, anio - 1)
        serie = {"unidad": "mm/mes", "fuente": imerg["fuente"], "valores": imerg["valores"], "normal": imerg["normal"],
                 "producto": imerg["producto"], "punto": imerg["punto"], "normalPeriodo": "2001-2020", "parcial": None}
        _mes_en_curso(serie, anio, lat, lon)
        return serie, (previo["valores"][11] if previo else None)

    try:
        mensual = await cliente.mensual(lat, lon, anio - 1, anio, parametros=["PRECTOTCORR"])
        clim = await cliente.climatologia(lat, lon, parametros=["PRECTOTCORR"])
    except NasaPowerError:
        return _serie_vacia("mm/mes"), None
    a_mm_mes = mensual["PRECTOTCORR"] * mensual.index.days_in_month
    valores = [None if pd.isna(v) else round(float(v), 1)
               for v in a_mm_mes.reindex(pd.period_range(f"{anio}-01", f"{anio}-12", freq="M"))]
    normal = [round(float(clim.loc[m, "PRECTOTCORR"]) * calendar.monthrange(2001, m)[1], 1) for m in range(1, 13)]
    dic = a_mm_mes.get(pd.Period(f"{anio - 1}-12", freq="M"))
    serie = {"unidad": "mm/mes", "fuente": "NASA POWER", "valores": valores, "normal": normal,
             "producto": "NASA POWER PRECTOTCORR mensual (fuera del piloto de Piura)", "normalPeriodo": "2001-2025"}
    return serie, (None if dic is None or pd.isna(dic) else round(float(dic), 1))


def alerta_mur(anio: int, lang: str, u: dict) -> dict | None:
    mur = serie_mur()
    desde, hasta = f"{anio - 1}-12-01", f"{anio}-04-30"
    if mur is None or mur.semanas.index.min() > pd.Timestamp(desde) or mur.semanas.index.max() < pd.Timestamp(hasta):
        return None  # no hay serie o no cubre la ventana completa
    a = primera_alerta(mur, desde, hasta, u, nivel="medio")
    if a is None:
        return {"sinAlerta": True, "fuente": "MUR SST"}
    drenaje = primera_alerta(mur, desde, hasta, u, nivel="alto")
    accion = "v_accion_drenaje" if a["nivel"] == "alto" else "v_accion_mur"
    return {
        "fecha": a["semana"], "accion": texto(lang, accion),
        "motivo": texto(lang, "v_motivo_mur", signo=signo(a["anomalia"]), anom=abs(a["anomalia"]), semana=a["semana"]),
        "indicador": "elNino", "nivel": a["nivel"], "valor": a["anomalia"], "fuente": "MUR SST",
        "alertaDrenaje": ({"fecha": drenaje["semana"], "valor": drenaje["anomalia"], "fuente": "MUR SST"}
                          if drenaje else None),
    }


def alerta_lluvia(anio: int, lluvia: dict, dic_previo: float | None, lang: str, u: dict) -> dict | None:
    meses = [(anio - 1, 12, dic_previo, lluvia["normal"][11])] + [
        (anio, m, lluvia["valores"][m - 1], lluvia["normal"][m - 1]) for m in range(1, 5)]
    for y, m, valor, normal in meses:
        if valor is None or normal is None:
            continue
        dias = calendar.monthrange(y, m)[1]
        nivel, _, direccion = nivel_lluvia(valor / dias, normal / dias, u["lluvia"])
        if nivel == "alto" and direccion == "exceso":
            return {
                "fecha": date(y, m, dias).isoformat(), "accion": texto(lang, "v_accion_lluvia"),
                "motivo": texto(lang, "v_motivo_lluvia", mes=f"{nombre_mes(lang, m)} {y}", veces=valor / normal),
                "indicador": "lluvia", "nivel": nivel, "valor": valor, "fuente": lluvia["fuente"],
                "nota": texto(lang, "v_nota_lluvia"),
            }
    return None


def anios_disponibles(lat: float, lon: float, hoy: date | None = None) -> dict[str, Any]:
    """Años con datos REALES de lluvia para la coordenada (y en cuáles MUR SST cubre dic.-abr. para la alerta).

    - Piura (< 25 km de un punto): años con enero-abril de IMERG (Final hasta 2025-09; luego Late sumado por mes).
    - Resto: NASA POWER mensual, de 2001 al año anterior (el mensual de POWER llega hasta el año pasado).
    """
    hoy = hoy or date.today()
    anios: list[int] = []
    fuente = "NASA POWER"
    datos = imerg_piura()
    cercano = punto_cercano(lat, lon)
    if datos and cercano:
        serie = dict(zip(datos["mensual"]["meses"], datos["mensual"]["mm_mes"][cercano[0]["id"]]))
        # Basta la temporada de lluvias de Piura (enero-abril): es la ventana de la alerta de El Niño.
        # Así entran 2025 y el año en curso; los meses sin dato quedan vacíos (null), nunca se rellenan.
        anios = [a for a in range(1998, hoy.year + 1)
                 if all(serie.get(f"{a}-{m:02d}") is not None for m in range(1, 5))]
        fuente = "GPM IMERG"
    if not anios:
        anios, fuente = list(range(2001, hoy.year)), "NASA POWER"

    mur = serie_mur()
    con_mur = []
    if mur is not None and not mur.semanas.empty:
        ini, fin = mur.semanas.index.min(), mur.semanas.index.max()
        con_mur = [a for a in anios if ini <= pd.Timestamp(f"{a - 1}-12-01") and fin >= pd.Timestamp(f"{a}-04-30")]
    return {"anios": anios, "fuente": fuente, "conMurSst": con_mur}


def semanas_anticipacion(fecha_alerta: str | None, anio: int, mes_pico: int | None) -> int | None:
    if not fecha_alerta or not mes_pico:
        return None
    dias = (date(anio, mes_pico, 1) - date.fromisoformat(fecha_alerta)).days
    return max(0, dias // 7)


async def calcular_validacion(anio: int, lat: float, lon: float, lang: str, cliente: ClienteNasaPower) -> dict[str, Any]:
    u = umbrales()
    lluvia, dic_previo = await serie_lluvia(anio, lat, lon, cliente)

    alerta = alerta_mur(anio, lang, u)
    if alerta is None:  # sin MUR SST para esa ventana → solo lluvia
        alerta = alerta_lluvia(anio, lluvia, dic_previo, lang, u)
    elif alerta.get("sinAlerta"):
        alerta = None

    mes_parcial = (lluvia.get("parcial") or {}).get("mes")
    validos = [(v, i + 1) for i, v in enumerate(lluvia["valores"]) if v is not None and i + 1 != mes_parcial]
    mes_pico = max(validos)[1] if validos else None
    semanas = semanas_anticipacion(alerta["fecha"] if alerta else None, anio, mes_pico)

    es_2017 = anio == 2017
    normal_pico = lluvia["normal"][mes_pico - 1] if mes_pico else None
    veces = (lluvia["valores"][mes_pico - 1] / normal_pico) if mes_pico and normal_pico else 0.0
    mes_pico_txt = f"{nombre_mes(lang, mes_pico)} {anio}" if mes_pico else "?"
    if alerta:
        resumen = texto(lang, "v_resumen", mes=mes_pico_txt, veces=veces, fuente=lluvia["fuente"],
                        fecha=alerta["fecha"], semanas=semanas)
    else:
        resumen = texto(lang, "v_resumen_sin_alerta", mes=mes_pico_txt, veces=veces, fuente=lluvia["fuente"])

    recomendacion_previa = (
        {"tipo": "preparar drenaje", "accion": alerta["accion"], "motivo": alerta["motivo"], "fuente": alerta["fuente"]}
        if alerta else {"tipo": "sembrar", "accion": texto(lang, "v_sin_alerta"), "motivo": resumen, "fuente": lluvia["fuente"]}
    )
    return {
        "anio": anio, "lat": lat, "lon": lon,
        "evento": {"nombre": texto(lang, "v_evento_2017"), "inicio": "2017-01", "fin": "2017-04"} if es_2017 else None,
        "series": {
            "lluvia": lluvia,
            "humedadSuelo": _serie_vacia("m³/m³"),   # SMAP pendiente
            "ndvi": _serie_vacia("NDVI"),            # MODIS pendiente
        },
        "alerta": alerta,
        "mesLluviaMaxima": f"{anio}-{mes_pico:02d}" if mes_pico else None,
        "semanasAnticipacion": semanas,
        "realidad": {"resumen": texto(lang, "v_realidad_2017"), "fuente": "INDECI"} if es_2017 else None,
        # Compatibilidad con el contrato actual del frontend (Validacion: serie, recomendacionPrevia, resumen)
        "serie": [{"mes": m, "lluvia": lluvia["valores"][m - 1], "lluviaNormal": lluvia["normal"][m - 1],
                   "lluviaParcial": m == mes_parcial, "ndvi": None, "ndviNormal": None} for m in range(1, 13)],
        "recomendacionPrevia": recomendacion_previa,
        "resumen": resumen,
    }
