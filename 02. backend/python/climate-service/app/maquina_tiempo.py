"""Máquina del tiempo: qué habría dicho AllpaShift en un año pasado, con las reglas de hoy y solo con datos que ya existían ese día.

Tres fuentes de aviso, de la más temprana a la más tardía:
  1. El mar (El Niño): MUR SST semanal (NASA) desde 2016; antes, el índice mensual de NOAA CPC (no es NASA). Nivel medio ≥ +0,5 °C, alto ≥ +1,5 °C.
  2. La lluvia del mes: más de 3 veces su normal y más de 30 mm (GPM IMERG en Piura; NASA POWER en el resto). Solo se conoce al terminar el mes.
  3. (el desastre) el mes más lluvioso del año.
`semanasAnticipacion` = semanas completas entre el primer aviso y el INICIO del mes más lluvioso (0 si el aviso llegó después).
Un aviso de nivel medio pide vigilar; solo el nivel alto pide preparar el drenaje. En años sin inundación el nivel medio también puede activarse
(falsa alarma): por eso el texto lo dice y no se pide drenar con él.
"""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any

from . import historico

MES_NOMBRE = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
ACCION_ALTO = "Preparar drenaje y no sembrar en zonas bajas"
ACCION_MEDIO = "Vigilar la señal de El Niño y esperar antes de sembrar en zonas bajas"


def en_costa_del_pacifico(lat: float, lon: float) -> bool:
    """La señal de El Niño costero solo aplica a la costa del Pacífico (mismo recorte que nasa_cliente.sst_anomalia)."""
    return -20 <= lat <= 5 and lon <= -78


def _dias_del_mes(anio: int) -> list[int]:
    return [calendar.monthrange(anio, m)[1] for m in range(1, 13)]


def serie_power(power: dict, clim: dict, anio: int) -> tuple[list[float | None], list[float]]:
    """mm/mes del año y su normal, desde NASA POWER (mm/día × días del mes)."""
    dias = _dias_del_mes(anio)
    valores = [None if v is None else round(v * dias[m], 1) for m, v in enumerate(power["PRECTOTCORR"])]
    normal = [round(clim["PRECTOTCORR"][m] * dias[m], 1) for m in range(12)]
    return valores, normal


def alerta_lluvia(anio: int, valores: list[float | None], normal: list[float], fuente: str) -> dict[str, Any] | None:
    """Primer mes con lluvia > 3 veces la normal y > 30 mm. Fechada el ÚLTIMO día del mes: antes no se conocía el total."""
    for m, (v, n) in enumerate(zip(valores, normal, strict=True)):
        if v is not None and v > max(3 * n, 30):
            return {
                "fecha": date(anio, m + 1, calendar.monthrange(anio, m + 1)[1]).isoformat(), "accion": ACCION_ALTO,
                "motivo": f"En {MES_NOMBRE[m]} llovieron {v:.0f} mm frente a {n:.0f} mm normales ({v / max(n, 1):.1f} veces)",
                "indicador": "lluvia", "nivel": "alto", "valor": v, "fuente": fuente,
                "nota": f"Alerta calculada con la lluvia mensual ({fuente}): el total del mes solo se conoce al terminar",
            }  # fmt: skip
    return None


def _motivo_nino(e: dict[str, Any], fuente: str) -> str:
    cuando = f"la semana del {e['semana']}" if "semana" in e else f"{MES_NOMBRE[int(e['mes'][5:7]) - 1]} de {e['mes'][:4]} (promedio mensual)"
    return f"El mar frente a Perú (Niño 1+2) estaba {e['valor']:+.1f} °C sobre lo normal {cuando} ({fuente})"


def alertas_nino(anio: int, lat: float, lon: float) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """(primer aviso de nivel medio o alto, primer aviso de nivel alto) por la señal del mar; (None, None) si no aplica o no hay serie."""
    if not en_costa_del_pacifico(lat, lon) or (n := historico.alertas_nino(anio)) is None:
        return None, None

    def armar(e: dict[str, Any] | None) -> dict[str, Any] | None:
        if e is None:
            return None
        alto = e["nivel"] == "alto"
        nota = ("Señal calculada con MUR SST semanal (NASA JPL): promedio de la caja Niño 1+2, no del punto" if n["fuente"] == "MUR SST" else
                "Sin MUR SST para esa época: índice mensual de NOAA CPC (no es NASA), que solo se conoce al terminar el mes")  # fmt: skip
        return {"fecha": e["fecha"], "accion": ACCION_ALTO if alto else ACCION_MEDIO, "motivo": _motivo_nino(e, n["fuente"]), "indicador": "elNino",
                "nivel": e["nivel"], "valor": e["valor"], "fuente": n["fuente"], "nota": nota}  # fmt: skip

    return armar(n["medio"]), armar(n["alto"])


def semanas_antes(fecha_aviso: str | None, anio: int, mes_pico: int | None) -> int | None:
    if not fecha_aviso or mes_pico is None:
        return None
    return max(0, (date(anio, mes_pico, 1) - date.fromisoformat(fecha_aviso)).days // 7)


def mas_temprana(*alertas: dict[str, Any] | None) -> dict[str, Any] | None:
    return min((a for a in alertas if a), key=lambda a: a["fecha"], default=None)


def combinar(anio: int, valores: list[float | None], normal: list[float], fuente_lluvia: str, lat: float, lon: float) -> dict[str, Any]:
    """Todos los avisos, el primero, el primero que pide drenar y las semanas de anticipación de cada uno."""
    llu = alerta_lluvia(anio, valores, normal, fuente_lluvia)
    nino_medio, nino_alto = alertas_nino(anio, lat, lon)
    alertas = [a for a in (nino_medio, nino_alto, llu) if a]
    primera = mas_temprana(nino_medio, llu)
    drenaje = mas_temprana(nino_alto, llu)  # la lluvia extrema siempre es de nivel alto
    con_dato = [m for m, v in enumerate(valores) if v is not None]
    pico = max(con_dato, key=lambda m: valores[m]) + 1 if con_dato else None  # type: ignore[arg-type,index]
    # "Anticipación" solo tiene sentido si la lluvia extrema realmente ocurrió: sin ella, un aviso del mar no anticipa nada (falsa alarma)
    return {"alertas": alertas, "primera": primera, "drenaje": drenaje, "pico": pico, "lluvia": llu,
            "semanas": semanas_antes(primera["fecha"], anio, pico) if primera and llu else None,
            "semanasDrenaje": semanas_antes(drenaje["fecha"], anio, pico) if drenaje and llu else None}  # fmt: skip


def _semanas(n: int) -> str:
    return f"{n} semana" if n == 1 else f"{n} semanas"


def resumen(anio: int, c: dict[str, Any]) -> str:
    pico = f"{MES_NOMBRE[c['pico'] - 1]} de {anio}" if c["pico"] else "?"
    p, d = c["primera"], c["drenaje"]
    if p is None:
        return "Ese año la lluvia y la temperatura del mar no superaron los umbrales de alerta."
    if c["lluvia"] is None:  # el mar avisó pero no hubo lluvia extrema: no hay nada que anticipar
        pide = "la señal alta del mar pidió preparar el drenaje" if d else "habría pedido vigilar, no preparar drenaje"
        return (f"La señal del mar llegó a nivel {p['nivel']} el {p['fecha']} ({p['valor']:+.1f} °C) pero ese año no hubo lluvia extrema: {pide}. "
                "En años sin inundación el aviso es una falsa alarma; por eso solo la señal alta pide drenar.")
    texto = f"AllpaShift habría dado el primer aviso el {p['fecha']}, {_semanas(c['semanas'])} antes de que empezara el mes más lluvioso ({pico})"
    if d and d["fecha"] != p["fecha"]:
        causa = "señal alta del mar" if d["indicador"] == "elNino" else "lluvia extrema"
        texto += f", y habría pedido preparar el drenaje el {d['fecha']} ({causa}), {_semanas(c['semanasDrenaje'])} antes"
    return texto + "."


def recomendacion_previa(c: dict[str, Any]) -> dict[str, Any]:
    d, p = c["drenaje"], c["primera"]
    if d:
        return {"tipo": "preparar drenaje", "accion": "Preparar drenaje y adelantar la cosecha", "motivo": d["motivo"], "fuente": d["fuente"]}
    if p:
        return {"tipo": "esperar", "accion": "Esperar y vigilar antes de sembrar en zonas bajas", "motivo": p["motivo"], "fuente": p["fuente"]}
    return {"tipo": "sembrar", "accion": "Sembrar con normalidad", "motivo": "La lluvia y la temperatura del mar estuvieron dentro de lo normal", "fuente": "NASA POWER"}
