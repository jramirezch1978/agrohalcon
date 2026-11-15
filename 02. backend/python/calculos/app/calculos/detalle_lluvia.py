"""Detalle de la lluvia de UN mes ("¿Funciona?" → clic en una barra): mm por día, total por semana,
día y semana más lluviosos. Sale de GPM IMERG diario (Final hasta 2025-09, Late después) en los puntos
de Piura; fuera de Piura, de NASA POWER diario (PRECTOTCORR). Nunca se rellena: sin dato = null.

Semanas del mes: 1-7, 8-14, 15-21, 22-28 y 29-fin (la 5.ª es corta).
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any

import pandas as pd

from app.fuentes.nasa_power import ClienteNasaPower, NasaPowerError
from app.fuentes.piura import punto_cercano
from app.fuentes.precalculado import imerg_diario_piura, imerg_piura


def dias_imerg(lat: float, lon: float, anio: int, mes: int) -> tuple[list[float | None], dict] | None:
    """mm/día de cada día del mes en el punto de Piura más cercano (o None si no aplica)."""
    datos = imerg_diario_piura()
    cercano = punto_cercano(lat, lon)
    if not datos or not cercano:
        return None
    punto, km = cercano
    serie = datos["mm_dia"].get(punto["id"])
    if serie is None:
        return None
    f0 = date.fromisoformat(datos["inicio"])
    n_dias = calendar.monthrange(anio, mes)[1]
    vals: list[float | None] = []
    for d in range(1, n_dias + 1):
        k = (date(anio, mes, d) - f0).days
        vals.append(serie[k] if 0 <= k < len(serie) else None)
    if all(v is None for v in vals):
        return None
    fin_final = date.fromisoformat(datos["fin_final"])
    producto = ("GPM_3IMERGDF V07 (Final, diario)" if date(anio, mes, n_dias) <= fin_final
                else "GPM_3IMERGDL V07 (Late, diario)")
    ref = {"id": punto["id"], "lat": punto["lat"], "lon": punto["lon"], "km": round(km, 1)}
    return vals, {"fuente": "GPM IMERG", "producto": producto, "punto": ref}


async def dias_power(lat: float, lon: float, anio: int, mes: int,
                     cliente: ClienteNasaPower) -> tuple[list[float | None], dict] | None:
    n_dias = calendar.monthrange(anio, mes)[1]
    fin = min(date(anio, mes, n_dias), date.today() - timedelta(days=1))
    if fin < date(anio, mes, 1):
        return None
    try:
        df = await cliente.diario(lat, lon, date(anio, mes, 1), fin, parametros=["PRECTOTCORR"])
    except NasaPowerError:
        return None
    s = df["PRECTOTCORR"]
    vals: list[float | None] = []
    for d in range(1, n_dias + 1):
        v = s.get(pd.Timestamp(anio, mes, d))
        vals.append(None if v is None or pd.isna(v) or v < 0 else round(float(v), 2))
    if all(v is None for v in vals):
        return None
    return vals, {"fuente": "NASA POWER", "producto": "NASA POWER PRECTOTCORR diario", "punto": None}


def normal_mes(lat: float, lon: float, mes: int) -> float | None:
    """Normal mensual 2001-2020 de IMERG Final (mm/mes) en el punto de Piura más cercano."""
    datos = imerg_piura()
    cercano = punto_cercano(lat, lon)
    if not datos or not cercano:
        return None
    return datos["climatologia"]["mm_mes"][cercano[0]["id"]][mes - 1]


async def calcular_detalle(anio: int, mes: int, lat: float, lon: float,
                           cliente: ClienteNasaPower) -> dict[str, Any] | None:
    r = dias_imerg(lat, lon, anio, mes) or await dias_power(lat, lon, anio, mes, cliente)
    if r is None:
        return None
    vals, info = r
    n_dias = len(vals)
    normal = normal_mes(lat, lon, mes) if info["fuente"] == "GPM IMERG" else None
    normal_dia = round(normal / n_dias, 2) if normal is not None else None
    dias = [{"fecha": date(anio, mes, d + 1).isoformat(), "mm": v} for d, v in enumerate(vals)]
    con_dato = [d for d in dias if d["mm"] is not None]
    semanas = []
    for i, ini in enumerate(range(1, n_dias + 1, 7)):
        fin = min(ini + 6, n_dias)
        tramo = vals[ini - 1:fin]
        ok = [v for v in tramo if v is not None]
        semanas.append({
            "semana": i + 1, "desde": date(anio, mes, ini).isoformat(), "hasta": date(anio, mes, fin).isoformat(),
            "mm": round(sum(ok), 1) if ok else None, "diasConDato": len(ok), "dias": len(tramo),
            "normal": round(normal_dia * len(tramo), 1) if normal_dia is not None else None,
        })
    total = round(sum(d["mm"] for d in con_dato), 1)
    sem_ok = [s for s in semanas if s["mm"] is not None]
    return {
        "anio": anio, "mes": mes, "lat": lat, "lon": lon, "unidad": "mm/día", **info,
        "dias": dias, "semanas": semanas,
        "total": total, "normalMes": normal, "normalDia": normal_dia,
        "veces": round(total / normal, 2) if normal else None,
        "diaMaximo": max(con_dato, key=lambda d: d["mm"]),
        "semanaMaxima": max(sem_ok, key=lambda s: s["mm"])["semana"] if sem_ok else None,
        "diasConLluvia": sum(1 for d in con_dato if d["mm"] >= 1.0),
        "parcial": len(con_dato) < n_dias, "hasta": con_dato[-1]["fecha"],
    }
