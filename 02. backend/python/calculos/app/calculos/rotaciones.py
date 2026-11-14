"""Cálculo 3: puntaje de rotaciones de cultivos temporales (sin IA, reglas en config/umbrales.yaml).

Una rotación = dos cultivos seguidos: el primero se siembra en mesSiembra y el segundo el mes siguiente a su
cosecha. Cada rotación empieza con 100 puntos y resta:
- agua: algún cultivo de uso de agua ALTO con la humedad del suelo o la lluvia ACTUAL en déficit
  alto → -40, medio → -20 (una vez por rotación; cita el indicador decisivo y su fuente real).
- temperatura: -10 por cada mes de la campaña con la temperatura fuera del rango del cultivo (máx. -30).
- riesgo alto: -10 por cada mes de la campaña con riesgo alto.
- siembra: -15 por cada cultivo sembrado fuera de sus meses recomendados.
Mínimo 0. Riesgo: >= 70 bajo, 45-69 medio, < 45 alto.
"""
from __future__ import annotations

from itertools import permutations
from typing import Any

import pandas as pd

from app.calculos.campana import NIVELES, armar_ciclo, en_zona_costera, riesgo_mes, senal_nino
from app.catalogo import Cultivo
from app.textos.plantillas import texto

FUENTE_CATALOGO = "catálogo de cultivos"


def deficit_actual(indicadores: dict) -> tuple[str, str, dict] | None:
    """Peor déficit actual entre humedad del suelo y lluvia: (nivel, clave, indicador) o None."""
    candidatos = [
        (ind["nivel"], clave, ind)
        for clave in ("humedadSuelo", "lluvia")
        if (ind := indicadores.get(clave)) and ind.get("nivel") in ("medio", "alto") and ind.get("direccion") == "deficit"
    ]
    return max(candidatos, key=lambda c: NIVELES.index(c[0])) if candidatos else None


def descuentos_rotacion(cultivos: list[Cultivo], siembras: list[pd.Period], meses: list[dict],
                        indicadores: dict, u: dict) -> list[dict]:
    ur = u["rotaciones"]
    desc: list[dict] = []

    # 1) Agua alta vs déficit actual
    if any(c.agua == "alto" for c in cultivos) and (d := deficit_actual(indicadores)):
        nivel, clave, ind = d
        puntos = ur["agua_alto_deficit_alto"] if nivel == "alto" else ur["agua_alto_deficit_medio"]
        desc.append({"indicador": clave, "puntos": puntos, "fuente": ind["fuente"], "regla": "agua",
                     "valor": ind.get("anomalia")})

    # 2) Temperatura fuera de rango (calor o frío) en algún mes
    n_temp = sum(1 for m in meses if NIVELES.index(peor_temp(m)) >= 1)
    if n_temp:
        puntos = max(ur["temperatura_maximo"], ur["temperatura_por_mes"] * n_temp)
        desc.append({"indicador": "calor", "puntos": puntos, "fuente": "NASA POWER", "regla": "temperatura", "meses": n_temp})

    # 3) Meses con riesgo alto
    altos = [m for m in meses if m["riesgo"] == "alto"]
    if altos:
        fuentes = sorted({m["fuente"] for m in altos}, key=len)
        desc.append({"indicador": "campana", "puntos": ur["mes_riesgo_alto"] * len(altos), "fuente": fuentes[-1],
                     "regla": "riesgo_alto", "meses": len(altos)})

    # 4) Siembra fuera de los meses recomendados (cada cultivo)
    for c, mes in zip(cultivos, siembras):
        if c.meses_siembra and mes.month not in c.meses_siembra:
            desc.append({"indicador": "campana", "puntos": ur["siembra_fuera_de_meses"], "fuente": FUENTE_CATALOGO,
                         "regla": "siembra", "cultivo": c.id})
    return desc


def peor_temp(mes: dict) -> str:
    comp = mes["componentes"]
    return max(comp["calor"], comp["frio"], key=NIVELES.index)


def nivel_puntaje(p: int, u: dict) -> str:
    if p >= u["rotaciones"]["riesgo_bajo_desde"]:
        return "bajo"
    if p >= u["rotaciones"]["riesgo_medio_desde"]:
        return "medio"
    return "alto"


def explicacion(cultivos: list[Cultivo], desc: list[dict], tradicional: bool, lang: str) -> str:
    if not desc:
        frase = texto(lang, "r_ok")
    else:
        total = -sum(d["puntos"] for d in desc)
        mayor = min(desc, key=lambda d: d["puntos"])
        regla = mayor["regla"]
        if regla == "agua":
            razon = texto(lang, "r_agua", ind=texto(lang, f"ind_{mayor['indicador']}"))
        elif regla == "temperatura":
            razon = texto(lang, "r_temp", n=mayor["meses"])
        elif regla == "riesgo_alto":
            razon = texto(lang, "r_alto", n=mayor["meses"])
        else:
            c = next(c for c in cultivos if c.id == mayor["cultivo"])
            razon = texto(lang, "r_siembra", cultivo=c.nombre_en(lang).lower())
        frase = texto(lang, "r_pierde", p=total, razon=razon)
    return frase + (texto(lang, "r_tradicional") if tradicional else "")


def evaluar_rotacion(cultivos: list[Cultivo], mes_siembra: str, clima: pd.DataFrame, indicadores: dict,
                     lat: float, lon: float, lang: str, u: dict, tradicional: bool = False) -> dict[str, Any]:
    nino_ind = indicadores.get("elNino")
    nino = senal_nino(nino_ind, lat, lon)
    sin_dato_costa = en_zona_costera(lat, lon) and (not nino_ind or nino_ind.get("valor") is None)
    meses, siembras, inicio = [], [], pd.Period(mes_siembra, freq="M")
    for c in cultivos:
        siembras.append(inicio)
        for i in range(c.duracion_meses or 4):
            meses.append(riesgo_mes(c, inicio + i, clima, nino, sin_dato_costa, lang, u))
        inicio = inicio + (c.duracion_meses or 4)

    desc = descuentos_rotacion(cultivos, siembras, meses, indicadores, u)
    puntaje = max(0, 100 + sum(d["puntos"] for d in desc))
    uso = max((c.usoAgua or c.agua for c in cultivos), key=NIVELES.index)
    return {
        "nombre": " - ".join(c.nombre_en(lang) for c in cultivos),
        "cultivos": [c.id for c in cultivos],
        "puntaje": puntaje, "riesgo": nivel_puntaje(puntaje, u), "usoAgua": uso,
        "explicacion": explicacion(cultivos, desc, tradicional, lang),
        "descuentos": desc, "tradicional": tradicional,
        "ciclo": armar_ciclo(meses),
    }


def generar_rotaciones(catalogo: list[Cultivo], mes_siembra: str, clima: pd.DataFrame, indicadores: dict,
                       lat: float, lon: float, lang: str, u: dict, n: int = 3) -> list[dict]:
    """La tradicional de la zona (p. ej. Arroz - Arroz) + las mejores combinaciones de dos cultivos distintos."""
    temporales = [c for c in catalogo if c.tipo == "temporal"]
    tradicional = next((c for c in temporales if c.tradicional), None)

    candidatas = [evaluar_rotacion([a, b], mes_siembra, clima, indicadores, lat, lon, lang, u)
                  for a, b in permutations(temporales, 2)]
    candidatas.sort(key=lambda r: -r["puntaje"])
    elegidas = candidatas[: n - 1 if tradicional else n]
    if tradicional:
        elegidas.append(evaluar_rotacion([tradicional, tradicional], mes_siembra, clima, indicadores, lat, lon,
                                         lang, u, tradicional=True))
    elegidas.sort(key=lambda r: -r["puntaje"])
    for i, r in enumerate(elegidas, start=1):
        r["id"] = i
    return elegidas
