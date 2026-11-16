"""Cálculo 3: puntaje de rotaciones de cultivos temporales (sin IA, reglas en config/umbrales.yaml).

Una rotación = dos cultivos seguidos: el primero se siembra en mesSiembra y el segundo el mes siguiente a su
cosecha. Cada rotación empieza con 100 puntos y resta:
- agua: algún cultivo de uso de agua ALTO con la humedad del suelo o la lluvia ACTUAL en déficit
  alto → -40, medio → -20 (una vez por rotación; cita el indicador decisivo y su fuente real).
- temperatura: -10 por cada mes de la campaña con la temperatura fuera del rango del cultivo (máx. -30).
- riesgo alto: -10 por cada mes de la campaña con riesgo alto.
- siembra: -15 por cada cultivo sembrado fuera de sus meses recomendados.
- El Niño extraordinario (mar ≥ +3 °C en la costa norte, con dato real): -35 a TODAS las rotaciones (ninguna siembra es segura).
Mínimo 0. Riesgo: >= 70 bajo, 45-69 medio, < 45 alto. Ese es el puntaje CLIMÁTICO ("riesgoClimatico").

Puntaje FINAL ("puntaje") = clima·w + suelo·w + agua·w, con los pesos de la prioridad del agricultor
(config/umbrales.yaml → prioridades). La rotación recomendada es la de mayor puntaje final.
"""
from __future__ import annotations

from itertools import permutations
from typing import Any

import pandas as pd

from app.calculos.campana import NIVELES, armar_ciclo, en_zona_costera, riesgo_mes, senal_nino
from app.catalogo import Cultivo
from app.calculos.salud_suelo import puntaje_suelo, meses_suelo_desnudo
from app.textos.plantillas import signo, texto

FUENTE_CATALOGO = "catálogo de cultivos"


def deficit_actual(indicadores: dict) -> tuple[str, str, dict] | None:
    """Peor déficit actual entre humedad del suelo y lluvia: (nivel, clave, indicador) o None."""
    candidatos = [
        (ind["nivel"], clave, ind)
        for clave in ("humedadSuelo", "lluvia")
        if (ind := indicadores.get(clave)) and ind.get("nivel") in ("medio", "alto") and ind.get("direccion") == "deficit"
    ]
    return max(candidatos, key=lambda c: NIVELES.index(c[0])) if candidatos else None


def nino_extremo(indicador_nino: dict | None, lat: float, lon: float, u: dict) -> dict | None:
    """El indicador de El Niño si es EXTRAORDINARIO (≥ el_nino_extremo_c) y aplica: costa norte de Perú y sur de Ecuador, con dato real."""
    umbral = u["rotaciones"].get("el_nino_extremo_c")
    if umbral is None or not indicador_nino or indicador_nino.get("valor") is None or not en_zona_costera(lat, lon):
        return None
    return indicador_nino if indicador_nino["valor"] >= umbral else None


def descuentos_rotacion(cultivos: list[Cultivo], siembras: list[pd.Period], meses: list[dict],
                        indicadores: dict, u: dict, extremo: dict | None = None) -> list[dict]:
    ur = u["rotaciones"]
    desc: list[dict] = []

    # 0) El Niño extraordinario: lluvias e inundaciones fuera de lo normal → ninguna rotación es segura
    if extremo:
        desc.append({"indicador": "elNino", "puntos": ur["el_nino_extremo_puntos"], "fuente": extremo["fuente"],
                     "regla": "el_nino_extremo", "valor": extremo["valor"]})

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

    # 3b) Meses con riesgo medio (resta poco, pero cada cambio de la barra de meses se ve en el puntaje)
    medios = [m for m in meses if m["riesgo"] == "medio"]
    if medios and ur.get("mes_riesgo_medio"):
        fuentes = sorted({m["fuente"] for m in medios}, key=len)
        desc.append({"indicador": "campana", "puntos": ur["mes_riesgo_medio"] * len(medios), "fuente": fuentes[-1],
                     "regla": "riesgo_medio", "meses": len(medios)})

    # 4) Siembra fuera de los meses recomendados (cada cultivo)
    for c, mes in zip(cultivos, siembras):
        if c.meses_siembra and mes.month not in c.meses_siembra:
            desc.append({"indicador": "campana", "puntos": ur["siembra_fuera_de_meses"], "fuente": FUENTE_CATALOGO,
                         "regla": "siembra", "cultivo": c.id})
    return desc


def peor_temp(mes: dict) -> str:
    comp = mes["componentes"]
    return max(comp["calor"], comp["frio"], comp.get("helada", "bajo"), key=NIVELES.index)


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
        if regla == "el_nino_extremo":
            razon = texto(lang, "r_nino_extremo", signo=signo(mayor["valor"]), anom=abs(mayor["valor"]))
        elif regla == "agua":
            razon = texto(lang, "r_agua", ind=texto(lang, f"ind_{mayor['indicador']}"))
        elif regla == "temperatura":
            razon = texto(lang, "r_temp", n=mayor["meses"])
        elif regla == "riesgo_alto":
            razon = texto(lang, "r_alto", n=mayor["meses"])
        elif regla == "riesgo_medio":
            razon = texto(lang, "r_medio", n=mayor["meses"])
        else:
            c = next(c for c in cultivos if c.id == mayor["cultivo"])
            razon = texto(lang, "r_siembra", cultivo=c.nombre_en(lang).lower())
        frase = texto(lang, "r_pierde", p=total, razon=razon)
    return frase + (texto(lang, "r_tradicional") if tradicional else "")


def calificacion(puntaje: int, u: dict) -> str:
    """Lo que el agricultor lee en lugar del número: buena / regular / riesgosa (mismos cortes que el riesgo)."""
    return {"bajo": "buena", "medio": "regular", "alto": "riesgosa"}[nivel_puntaje(puntaje, u)]


def _lista(lang: str, partes: list[str]) -> str:
    y = " and " if lang == "en" else " y "
    return partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + y + partes[-1]


def explicacion_tradicional(cultivos: list[Cultivo], desc: list[dict], desc_suelo: list[dict], uso: str,
                            calif: str, lang: str) -> str:
    """Para la rotación de siempre (p. ej. Arroz - Arroz), en UNA frase y en palabras de campo: por qué sale así.
    Junta las causas de los tres puntajes (clima, suelo y agua), no solo la del clima."""
    razones = []
    if (n := next((d for d in desc if d["regla"] == "el_nino_extremo"), None)):
        razones.append(texto(lang, "t_nino", anom=abs(n["valor"])))
    if uso == "alto":
        razones.append(texto(lang, "t_agua"))
    if any(d["regla"] in ("monocultivo", "misma_familia") for d in desc_suelo):
        razones.append(texto(lang, "t_repetir", cultivo=cultivos[0].nombre_en(lang).lower()))
    if any(d["regla"] == "siembra" for d in desc):
        razones.append(texto(lang, "t_epoca"))
    if not razones:
        return explicacion(cultivos, desc, True, lang)
    return texto(lang, f"t_{calif}", razones=_lista(lang, razones)) + texto(lang, "r_tradicional")


def evaluar_rotacion(cultivos: list[Cultivo], mes_siembra: str, clima: pd.DataFrame, indicadores: dict,
                     lat: float, lon: float, lang: str, u: dict, tradicional: bool = False,
                     salinidad: str | None = None, prioridad: str | None = None, tipo_suelo: str | None = None,
                     fuente_suelo: str | None = None, agua_disponible: str | None = None) -> dict[str, Any]:
    nino_ind = indicadores.get("elNino")
    nino = senal_nino(nino_ind, lat, lon)
    sin_dato_costa = en_zona_costera(lat, lon) and (not nino_ind or nino_ind.get("valor") is None)
    meses, siembras, inicio = [], [], pd.Period(mes_siembra, freq="M")
    for c in cultivos:
        siembras.append(inicio)
        for i in range(c.duracion_meses or 4):
            meses.append(riesgo_mes(c, inicio + i, clima, nino, sin_dato_costa, lang, u, lat))
        inicio = inicio + (c.duracion_meses or 4)

    desc = descuentos_rotacion(cultivos, siembras, meses, indicadores, u, extremo=nino_extremo(nino_ind, lat, lon, u))
    clima_p = max(0, 100 + sum(d["puntos"] for d in desc))
    uso = max((c.usoAgua or c.agua for c in cultivos), key=NIVELES.index)
    suelo, desc_suelo = puntaje_suelo(cultivos, u, lang, salinidad, tipo_suelo, fuente_suelo)
    tabla_agua = u["prioridades"].get("puntaje_agua_disponible", {}).get(agua_disponible or "", u["prioridades"]["puntaje_agua"])
    agua_p = tabla_agua[uso]
    final = puntaje_final(clima_p, suelo, agua_p, prioridad, u)
    calif = calificacion(final, u)
    texto_rot = (explicacion_tradicional(cultivos, desc, desc_suelo, uso, calif, lang) if tradicional
                 else explicacion(cultivos, desc, tradicional, lang))
    return {
        "nombre": " - ".join(c.nombre_en(lang) for c in cultivos),
        "cultivos": [c.id for c in cultivos],
        "puntaje": final, "calificacion": calif, "riesgo": nivel_puntaje(clima_p, u), "usoAgua": uso,
        "riesgoClimatico": clima_p, "saludSuelo": suelo, "puntajeAgua": agua_p, "descuentosSuelo": desc_suelo,
        "explicacion": texto_rot,
        "descuentos": desc, "tradicional": tradicional,
        "ciclo": armar_ciclo(meses),
        "mesesSueloDesnudo": meses_suelo_desnudo(cultivos),
    }


NIVELES_AGUA = ["poca", "normal", "suficiente"]


def agua_con_escenario(agua_disponible: str | None, escenario: str | None, u: dict) -> str | None:
    """Agua de riego que tendría el agricultor si el año viene seco o lluvioso (sin dato se parte de "normal").
    Escenario normal o sin escenario → el dato del agricultor tal cual."""
    paso = u.get("escenarios_agua", {}).get(escenario or "normal", 0)
    if not paso:
        return agua_disponible
    i = NIVELES_AGUA.index(agua_disponible or "normal") + paso
    return NIVELES_AGUA[max(0, min(len(NIVELES_AGUA) - 1, i))]


def prioridad_o_defecto(prioridad: str | None, u: dict) -> str:
    return prioridad if prioridad in u["prioridades"]["pesos"] else u["prioridades"]["por_defecto"]


def puntaje_final(clima_p: int, suelo: int, agua: int, prioridad: str | None, u: dict) -> int:
    w = u["prioridades"]["pesos"][prioridad_o_defecto(prioridad, u)]
    return round(clima_p * w["clima"] + suelo * w["suelo"] + agua * w["agua"])


def motivo_recomendada(r: dict, prioridad: str | None, lang: str, u: dict) -> str:
    p = prioridad_o_defecto(prioridad, u)
    return texto(lang, f"p_{p}", clima=r["riesgoClimatico"], suelo=r["saludSuelo"], agua=texto(lang, f"agua_{r['usoAgua']}"))


def generar_rotaciones(catalogo: list[Cultivo], mes_siembra: str, clima: pd.DataFrame, indicadores: dict,
                       lat: float, lon: float, lang: str, u: dict, n: int = 3, prioridad: str | None = None,
                       salinidad: str | None = None, tipo_suelo: str | None = None,
                       fuente_suelo: str | None = None, agua_disponible: str | None = None) -> list[dict]:
    """La tradicional de la zona (p. ej. Arroz - Arroz) + las mejores combinaciones de dos cultivos distintos,
    ordenadas por el puntaje final según la prioridad del agricultor."""
    temporales = [c for c in catalogo if c.tipo == "temporal"]
    tradicional = next((c for c in temporales if c.tradicional), None)
    perfil = {"prioridad": prioridad, "salinidad": salinidad, "tipo_suelo": tipo_suelo, "fuente_suelo": fuente_suelo,
              "agua_disponible": agua_disponible}

    candidatas = [evaluar_rotacion([a, b], mes_siembra, clima, indicadores, lat, lon, lang, u, **perfil)
                  for a, b in permutations(temporales, 2)]
    candidatas.sort(key=lambda r: -r["puntaje"])
    # Los mismos dos cultivos en otro orden no cuentan como otra opción: queda el mejor orden
    elegidas, vistos = [], set()
    for r in candidatas:
        if (clave := frozenset(r["cultivos"])) in vistos:
            continue
        vistos.add(clave)
        elegidas.append(r)
        if len(elegidas) == (n - 1 if tradicional else n):
            break
    if tradicional:
        elegidas.append(evaluar_rotacion([tradicional, tradicional], mes_siembra, clima, indicadores, lat, lon,
                                         lang, u, tradicional=True, **perfil))
    elegidas.sort(key=lambda r: -r["puntaje"])
    for i, r in enumerate(elegidas, start=1):
        r["id"] = i
    if elegidas and not elegidas[0]["tradicional"]:
        elegidas[0]["motivoRecomendada"] = motivo_recomendada(elegidas[0], prioridad, lang, u)
    return elegidas
