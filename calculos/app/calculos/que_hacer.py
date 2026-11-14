"""Cálculo 4: qué hacer esta quincena. Reglas en orden de prioridad (la primera que se cumple decide):

1) El Niño alto (con dato real de MUR SST) y la coordenada en la costa norte → "preparar drenaje".
2) Humedad del suelo o lluvia en DÉFICIT alto y es mes de siembra → "esperar" (temporal) / "regar" (permanente,
   el cultivo ya está en el campo; para un cultivo en campo se aplica aunque no sea mes de siembra).
3) Calor alto → "proteger".
4) Resto: si es mes de siembra → "sembrar" la rotación con mayor puntaje; si no → "esperar" al próximo mes
   recomendado. Para permanentes: seguir el manejo normal de la etapa actual.
El motivo cita el indicador decisivo con su número; "fuente" es la fuente real de ese indicador.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from app.calculos.el_nino import en_zona_costera
from app.calculos.rotaciones import deficit_actual
from app.catalogo import Cultivo
from app.textos.plantillas import nombre_mes, signo, texto


def proximo_mes_siembra(cultivo: Cultivo, hoy: date) -> int | None:
    if not cultivo.meses_siembra:
        return None
    return min(cultivo.meses_siembra, key=lambda m: (m - hoy.month) % 12 or 12)


def que_hacer(indicadores: dict, lat: float, lon: float, lang: str, hoy: date, tipo_cultivo: str,
              mejor_rotacion: dict | None = None, primer_cultivo: Cultivo | None = None,
              permanente: Cultivo | None = None, etapa_actual: str | None = None) -> dict[str, Any]:
    nino = indicadores.get("elNino") or {}
    es_mes_siembra = bool(primer_cultivo and hoy.month in primer_cultivo.meses_siembra)

    # 1) El Niño alto en la costa (solo con dato real)
    if nino.get("valor") is not None and nino.get("nivel") == "alto" and en_zona_costera(lat, lon):
        return {"tipo": "preparar drenaje", "accion": texto(lang, "q_drenaje"),
                "motivo": texto(lang, "q_drenaje_m", signo=signo(nino["valor"]), anom=abs(nino["valor"]),
                                semana=nino.get("semana", "?")),
                "fuente": nino["fuente"], "indicador": "elNino"}

    # 2) Déficit alto de humedad del suelo o de lluvia
    deficit = deficit_actual(indicadores)
    if deficit and deficit[0] == "alto" and (es_mes_siembra or tipo_cultivo == "permanente"):
        _, clave, ind = deficit
        motivo = texto(lang, "q_seco_m", ind=texto(lang, f"ind_{clave}").capitalize(), abs=abs(ind["anomalia"]))
        if tipo_cultivo == "permanente" and permanente:
            accion = texto(lang, "q_regar", cultivo=permanente.nombre_en(lang).lower())
            tipo = "regar"
        else:
            accion, tipo = texto(lang, "q_esperar_seco"), "esperar"
        return {"tipo": tipo, "accion": accion, "motivo": motivo, "fuente": ind["fuente"], "indicador": clave}

    # 3) Calor alto
    calor = indicadores.get("calor") or {}
    if calor.get("nivel") == "alto":
        return {"tipo": "proteger", "accion": texto(lang, "q_proteger"),
                "motivo": texto(lang, "q_proteger_m", signo=signo(calor["anomalia"]), dif=abs(calor["anomalia"]),
                                valor=calor["valor"]),
                "fuente": calor["fuente"], "indicador": "calor"}

    # 4) Resto
    if tipo_cultivo == "permanente":
        return {"accion": texto(lang, "q_plan", etapa=etapa_actual or "?"), "motivo": texto(lang, "q_plan_m"),
                "fuente": "NASA POWER", "indicador": None}
    if mejor_rotacion and primer_cultivo:
        nombre_cultivo = primer_cultivo.nombre_en(lang).lower()
        if es_mes_siembra:
            return {"tipo": "sembrar",
                    "accion": texto(lang, "q_sembrar", rotacion=mejor_rotacion["nombre"], p=mejor_rotacion["puntaje"]),
                    "motivo": texto(lang, "q_sembrar_m", mes=nombre_mes(lang, hoy.month), cultivo=nombre_cultivo),
                    "fuente": "NASA POWER", "indicador": None}
        prox = proximo_mes_siembra(primer_cultivo, hoy)
        mes_hoy = nombre_mes(lang, hoy.month)
        return {"tipo": "esperar",
                "accion": texto(lang, "q_esperar_mes", mes=nombre_mes(lang, prox) if prox else "?",
                                rotacion=mejor_rotacion["nombre"]),
                "motivo": texto(lang, "q_esperar_mes_m", mes_hoy=mes_hoy[0].upper() + mes_hoy[1:], cultivo=nombre_cultivo),
                "fuente": "NASA POWER", "indicador": None}
    return {"accion": texto(lang, "q_plan_m"), "motivo": texto(lang, "q_plan_m"), "fuente": "NASA POWER",
            "indicador": None}
