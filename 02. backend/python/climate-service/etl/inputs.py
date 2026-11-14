"""Arma el cuerpo de POST /indicadores (lo que Java le manda a Python) con datos reales de NASA.

Así David puede probar el servicio con datos reales de cualquier punto y fecha, y generar los datos
de respaldo y la validación de El Niño 2017 SIN esperar a la API en Java.

Decisiones (anotadas para que se puedan discutir):
  * "Normal histórico" = promedio del MISMO MES en 1991-2020 (periodo estándar de la OMM), calculado aquí
    con la serie mensual de POWER. No se usa el endpoint 'climatology' de POWER porque no declara su
    periodo base y dio valores distintos (marzo: lluvia 1,69 vs 1,97 mm/día; T2M_MAX 39,1 vs 37,5 °C).
  * "Actual" = promedio de los últimos 14 días con dato (POWER tiene ~2-3 días de rezago).
  * Humedad del suelo y lluvia vienen de POWER (GWETTOP, PRECTOTCORR) mientras no estén SMAP e IMERG;
    se declara en `meta` para que la app NO diga "SMAP" si el dato salió de POWER.
"""

from datetime import date, timedelta
from statistics import mean

from . import mur_sst, nasa_power

BASE_NORMAL = (1991, 2020)


def normales_mensuales(mensual: dict, base: tuple[int, int] = BASE_NORMAL) -> dict[int, dict[str, float]]:
    """{mes: {parametro: promedio}} del periodo base, a partir de la serie mensual de POWER."""
    normales: dict[int, dict[str, float]] = {m: {} for m in range(1, 13)}
    for parametro, serie in mensual.items():
        for mes in range(1, 13):
            valores = [
                v for k, v in serie.items() if int(k[4:6]) == mes and base[0] <= int(k[:4]) <= base[1]
            ]
            if valores:
                normales[mes][parametro] = mean(valores)
    return normales


def construir_entrada(
    lat: float,
    lon: float,
    hasta: date,
    diario: dict,
    normales: dict[int, dict[str, float]],
    sst_anomalia_c: float | None,
    ventana_dias: int = 14,
    variable_calor: str = "T2M_MAX",
    fuente_sst: str = "MUR SST",
    humedad_smap: tuple[float, float] | None = None,
) -> tuple[dict, dict]:
    """Devuelve (cuerpo para POST /indicadores, trazabilidad). La trazabilidad NO se envía al servicio:
    se guarda al lado para saber de qué días salió cada número."""
    ventana = {p: nasa_power.promedio_ventana(diario[p], hasta, ventana_dias) for p in diario}
    faltan = [p for p in ("PRECTOTCORR", "GWETTOP", variable_calor, "T2M_MIN") if not ventana.get(p)]
    if faltan:
        raise ValueError(f"POWER no tiene datos en la ventana para: {faltan} (hasta {hasta})")

    ultimo_dia = max(ventana[p][1] for p in ("PRECTOTCORR", "GWETTOP", variable_calor))
    normal = normales[ultimo_dia.month]
    meta = {
        "lluvia": {"fuente": "NASA POWER (PRECTOTCORR)"},
        "humedadSuelo": {"fuente": "NASA POWER (GWETTOP)", "unidad": "fracción 0-1"},
        "calor": {"fuente": f"NASA POWER ({variable_calor})"},
        "elNino": {"fuente": fuente_sst},
    }
    advertencias = []
    if sst_anomalia_c is None:
        sst_anomalia_c = 0.0
        meta["elNino"] = {"fuente": f"{fuente_sst} (sin dato: se asumió anomalía 0)"}
        advertencias.append(f"{fuente_sst} no disponible: la anomalía del mar se fijó en 0 °C")

    cuerpo = {
        "lat": lat,
        "lon": lon,
        "actual": {
            "lluviaMm": round(ventana["PRECTOTCORR"][0], 3),
            "humedadSuelo": round(ventana["GWETTOP"][0], 3),
            "tempMaxC": round(ventana[variable_calor][0], 2),
            "tempMinC": round(ventana["T2M_MIN"][0], 2),
            "sstAnomaliaC": round(sst_anomalia_c, 2),
        },
        "historico": {
            "lluviaMm": round(normal["PRECTOTCORR"], 3),
            "humedadSuelo": round(normal["GWETTOP"], 3),
            "tempMaxC": round(normal[variable_calor], 2),
            "tempMinC": round(normal["T2M_MIN"], 2),
        },
        "meta": meta,
    }
    if humedad_smap is not None:  # (valor actual, normal) de SMAP m3/m3: reemplaza a GWETTOP de POWER
        cuerpo["actual"]["humedadSuelo"] = round(humedad_smap[0], 4)
        cuerpo["historico"]["humedadSuelo"] = round(humedad_smap[1], 4)
        cuerpo["meta"]["humedadSuelo"] = {"fuente": "SMAP SPL3SMP_E v006", "unidad": "m3/m3"}
    trazabilidad = {
        "ventanaDias": ventana_dias,
        "ultimoDiaConDato": ultimo_dia.isoformat(),
        "baseNormal": list(BASE_NORMAL),
        "mesNormal": ultimo_dia.month,
        "advertencias": advertencias,
    }
    return cuerpo, trazabilidad


def entrada_actual(lat: float, lon: float, hasta: date | None = None) -> tuple[dict, dict]:
    """Todo en una llamada: baja POWER y MUR SST y arma el cuerpo. Necesita internet."""
    hasta = hasta or date.today()
    mensual = nasa_power.mensual(lat, lon, BASE_NORMAL[0], hasta.year)
    diario = nasa_power.diario(lat, lon, hasta - timedelta(days=40), hasta)
    sst = mur_sst.anomalia_sst(hasta)
    return construir_entrada(
        lat, lon, hasta, diario, normales_mensuales(mensual), sst["anomaliaC"] if sst else None
    )
