"""Cálculo 2: riesgo de la campaña, mes a mes, de la siembra a la cosecha.

ESTO NO ES UN PRONÓSTICO EXACTO. Es un riesgo estimado con el clima histórico (climatología NASA POWER
2001-2025 en la coordenada) frente a lo que tolera el cultivo, más una señal temprana (El Niño costero,
MUR SST) que solo se aplica en la costa norte de Perú y sur de Ecuador.

Cada mes tiene dos componentes y el riesgo del mes es el peor de ellos:
- temperatura: media de las máximas diarias del mes vs temp_max del cultivo (calor) y media de las mínimas
  vs temp_min (frío). Salir del rango → medio; salir por más de 3 °C → alto.
- lluvia: lluvia normal del mes vs necesidad de agua del cultivo. Exceso (inundación) → medio/alto.
  Déficit → medio ("depende del riego"; nunca alto, la costa de Piura es agricultura bajo riego).
Umbrales en config/umbrales.yaml (sección campana).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.calculos.el_nino import en_zona_costera
from app.catalogo import Cultivo
from app.textos.plantillas import nombre_mes, signo, texto

NIVELES = ["bajo", "medio", "alto"]
FUENTE_POWER = "NASA POWER"
METODO = "climatologia NASA POWER + señal El Niño"


def peor(*niveles: str) -> str:
    return max(niveles, key=NIVELES.index)


def subir(nivel: str) -> str:
    return NIVELES[min(NIVELES.index(nivel) + 1, 2)]


def nivel_temperatura(exceso_c: float, u: dict) -> str:
    """exceso_c = cuántos °C se sale del rango del cultivo (<= 0 = dentro)."""
    if exceso_c > u["alto"]:
        return "alto"
    if exceso_c > u["medio"]:
        return "medio"
    return "bajo"


def niveles_lluvia(lluvia_mm_mes: float, necesidad_mm_mes: float, u: dict) -> tuple[str, str]:
    """(nivel de exceso, nivel de déficit) de la lluvia normal del mes frente a la necesidad del cultivo."""
    ratio = lluvia_mm_mes / necesidad_mm_mes
    if ratio > u["exceso_alto"]["ratio"] and lluvia_mm_mes > u["exceso_alto"]["mm"]:
        exceso = "alto"
    elif ratio > u["exceso_medio"]["ratio"] and lluvia_mm_mes > u["exceso_medio"]["mm"]:
        exceso = "medio"
    else:
        exceso = "bajo"
    deficit = "medio" if ratio < u["deficit_ratio_medio"] else "bajo"
    return exceso, deficit


def senal_nino(indicador_nino: dict | None, lat: float, lon: float) -> dict | None:
    """La señal solo ajusta si hay dato de MUR SST, nivel medio/alto y la coordenada es costa norte."""
    if not indicador_nino or indicador_nino.get("valor") is None:
        return None
    if indicador_nino.get("nivel") in ("medio", "alto") and en_zona_costera(lat, lon):
        return indicador_nino
    return None


def riesgo_mes(cultivo: Cultivo, mes: pd.Period, clima: pd.DataFrame, nino: dict | None,
               nino_sin_dato_costa: bool, lang: str, u: dict) -> dict[str, Any]:
    c = clima.loc[mes.month]
    uc = u["campana"]
    nombre = cultivo.nombre_en(lang).lower()
    mes_txt = nombre_mes(lang, mes.month)

    calor = nivel_temperatura(c["tmax"] - cultivo.temp_max, uc["temperatura"])
    frio = nivel_temperatura(cultivo.temp_min - c["tmin"], uc["temperatura"])
    necesidad = uc["necesidad_agua_mm_mes"][cultivo.agua]
    exceso, deficit = niveles_lluvia(c["lluvia_mm_mes"], necesidad, uc)

    fuente = FUENTE_POWER
    notas = []
    por_nino = False
    if mes.month in uc["meses_nino"]:
        if nino:
            exceso, por_nino = subir(exceso), True
            fuente = f"{FUENTE_POWER} + MUR SST"
        elif nino_sin_dato_costa:
            notas.append(texto(lang, "c_sin_nino"))

    componentes = {"calor": calor, "frio": frio, "lluvia_exceso": exceso, "deficit": deficit}
    riesgo = peor(*componentes.values())

    # El motivo cita el componente decisivo con su número
    if riesgo == "bajo":
        motivo = texto(lang, "c_ok", mes=mes_txt, cultivo=nombre)
    elif riesgo == exceso and por_nino:
        motivo = texto(lang, "c_exceso_nino", mes=mes_txt, mm=c["lluvia_mm_mes"], signo=signo(nino["valor"]),
                       anom=abs(nino["valor"]))
    elif riesgo == exceso:
        motivo = texto(lang, "c_exceso", mes=mes_txt, mm=c["lluvia_mm_mes"], veces=c["lluvia_mm_mes"] / necesidad,
                       cultivo=nombre)
    elif riesgo == calor:
        motivo = texto(lang, "c_calor", mes=mes_txt, t=c["tmax"], lim=cultivo.temp_max, cultivo=nombre)
    elif riesgo == frio:
        motivo = texto(lang, "c_frio", mes=mes_txt, t=c["tmin"], lim=cultivo.temp_min, cultivo=nombre)
    else:
        motivo = texto(lang, "c_deficit", mes=mes_txt, mm=c["lluvia_mm_mes"], nec=necesidad, cultivo=nombre)
    if por_nino and riesgo != exceso:
        notas.append(texto(lang, "c_nino", signo=signo(nino["valor"]), anom=abs(nino["valor"])))
    if notas:
        motivo = f"{motivo} {' '.join(notas)}"
    motivo = motivo[0].upper() + motivo[1:]

    return {"mes": str(mes), "riesgo": riesgo, "motivo": motivo, "fuente": fuente,
            "cultivo": cultivo.id, "componentes": componentes}


def riesgo_campana(cultivo: Cultivo, mes_siembra: str | pd.Period, clima: pd.DataFrame, indicador_nino: dict | None,
                   lat: float, lon: float, lang: str, u: dict, duracion: int | None = None) -> dict[str, Any]:
    """Ciclo de un cultivo: {siembra, cosecha, duracionMeses, meses, mesMasRiesgoso, metodo}."""
    inicio = pd.Period(mes_siembra, freq="M")
    n = duracion or cultivo.duracion_meses or 12
    nino = senal_nino(indicador_nino, lat, lon)
    sin_dato_costa = en_zona_costera(lat, lon) and (not indicador_nino or indicador_nino.get("valor") is None)
    meses = [riesgo_mes(cultivo, inicio + i, clima, nino, sin_dato_costa, lang, u) for i in range(n)]
    return armar_ciclo(meses)


def armar_ciclo(meses: list[dict]) -> dict[str, Any]:
    peor_nivel = peor(*(m["riesgo"] for m in meses))
    mas_riesgoso = next(m["mes"] for m in meses if m["riesgo"] == peor_nivel) if peor_nivel != "bajo" else None
    return {
        "siembra": meses[0]["mes"], "cosecha": meses[-1]["mes"], "duracionMeses": len(meses),
        "meses": meses, "mesMasRiesgoso": mas_riesgoso, "metodo": METODO,
    }
