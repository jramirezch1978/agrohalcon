"""Señal de El Niño costero: anomalía de MUR SST en la caja Niño 1+2 (0°-10° S, 90°-80° O).

- Indicador "elNino": anomalía de la última semana disponible del precalculado. Es la misma señal para
  cualquier coordenada (es un índice del océano), pero solo AJUSTA el riesgo en la costa norte de Perú
  y sur de Ecuador (`en_zona_costera`). Fuera de ahí solo se informa.
- `primera_alerta`: recorre las semanas y devuelve la primera que dispara la MISMA regla que usa hoy
  "qué hacer esta quincena" (regla 1: elNino alto en la zona costera → "preparar drenaje").
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.calculos.reglas import nivel_el_nino
from app.fuentes.precalculado import SerieMur, serie_mur
from app.textos.plantillas import UNIDADES, dir_mar, signo, texto

FUENTE_MUR = "MUR SST"
SIN_DATO = "sin dato"

# Costa norte de Perú y sur de Ecuador, donde El Niño costero trae lluvias extremas
ZONA_COSTERA = {"lat": (-7.0, -2.0), "lon": (-82.0, -79.0)}
# Si el último dato tiene más días que esto, se avisa (el script de actualización no se corrió)
DIAS_DESACTUALIZADO = 21


def en_zona_costera(lat: float, lon: float) -> bool:
    (la0, la1), (lo0, lo1) = ZONA_COSTERA["lat"], ZONA_COSTERA["lon"]
    return la0 <= lat <= la1 and lo0 <= lon <= lo1


def indicador_el_nino(lat: float, lon: float, lang: str, u: dict, hoy: date,
                      serie: SerieMur | None = None) -> dict[str, Any]:
    serie = serie if serie is not None else serie_mur()
    unidad = UNIDADES.get(lang, UNIDADES["es"])["elNino"]
    validas = serie.semanas.dropna(subset=["anomalia"]) if serie else None

    if validas is None or validas.empty:
        return {
            "valor": None, "normal": 0.0, "unidad": unidad, "anomalia": None, "unidadAnomalia": "°C",
            "direccion": None, "nivel": None, "fuente": SIN_DATO, "disponible": False,
            "detalle": texto(lang, "elnino_sin_datos"),
        }

    semana, fila = validas.index[-1], validas.iloc[-1]
    anom = float(fila["anomalia"])
    fin_semana = (semana + pd.Timedelta(days=6)).date()
    return {
        "valor": round(anom, 2), "normal": 0.0, "unidad": unidad,
        "anomalia": round(anom, 2), "unidadAnomalia": "°C", "direccion": "exceso" if anom >= 0 else "deficit",
        "nivel": nivel_el_nino(anom, u["el_nino"]), "fuente": FUENTE_MUR,
        "parametro": "sstAnom (caja Niño 1+2, promedio semanal)",
        "sst": None if pd.isna(fila["sst"]) else round(float(fila["sst"]), 2),
        "semana": semana.date().isoformat(),
        "desactualizado": (hoy - fin_semana).days > DIAS_DESACTUALIZADO,
        "aplicaAjusteCosta": en_zona_costera(lat, lon),
        "disponible": True,
        "detalle": texto(lang, "elnino", signo=signo(anom), valor=abs(anom), dir=dir_mar(lang, anom),
                         semana=semana.date().isoformat()),
    }


def primera_alerta(serie: SerieMur, desde: str, hasta: str, u: dict, nivel: str = "alto") -> dict | None:
    """Primera semana entre `desde` y `hasta` cuya anomalía alcanza `nivel` con los umbrales actuales."""
    tramo = serie.semanas.loc[desde:hasta].dropna(subset=["anomalia"])
    orden = {"bajo": 0, "medio": 1, "alto": 2}
    for semana, fila in tramo.iterrows():
        if orden[nivel_el_nino(float(fila["anomalia"]), u["el_nino"])] >= orden[nivel]:
            return {"semana": semana.date().isoformat(), "anomalia": round(float(fila["anomalia"]), 2),
                    "nivel": nivel_el_nino(float(fila["anomalia"]), u["el_nino"]), "fuente": FUENTE_MUR}
    return None
