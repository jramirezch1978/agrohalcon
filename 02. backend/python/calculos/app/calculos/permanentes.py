"""Cálculo 5: cultivos permanentes (mango, limón, banano).

- Etapa actual según el mes y las etapas del catálogo.
- Riesgo de los próximos 12 meses con el MISMO método de la campaña (clima histórico + señal El Niño).
- Acciones del catálogo activadas cuando el componente de riesgo indicado ('calor', 'frio', 'lluvia_exceso',
  'deficit') llega al nivel pedido en un mes de esa etapa. En el mes actual también cuentan los indicadores
  de hoy (p. ej. calor alto ahora mismo).
Las etapas del catálogo de ejemplo siguen el calendario de Piura (hemisferio sur).
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.calculos.campana import NIVELES, peor, riesgo_campana
from app.catalogo import Cultivo
from app.textos.plantillas import nombre_mes, texto


def componentes_actuales(indicadores: dict) -> dict[str, str]:
    """Indicadores de hoy expresados como componentes de riesgo."""
    def nivel(clave: str, direccion: str | None = None) -> str:
        ind = indicadores.get(clave) or {}
        if ind.get("nivel") is None or (direccion and ind.get("direccion") != direccion):
            return "bajo"
        return ind["nivel"]

    return {
        "calor": nivel("calor", "exceso"),
        "frio": "bajo",
        "helada": "bajo",
        "lluvia_exceso": nivel("lluvia", "exceso"),
        "deficit": peor(nivel("humedadSuelo", "deficit"), nivel("lluvia", "deficit")),
    }


def indicador_de(componente: str, indicadores: dict) -> dict | None:
    """Indicador de hoy que corresponde a un componente de riesgo (el peor, si hay dos)."""
    claves = {"calor": ["calor"], "lluvia_exceso": ["lluvia"], "deficit": ["humedadSuelo", "lluvia"]}.get(componente, [])
    candidatos = [indicadores[k] for k in claves if (indicadores.get(k) or {}).get("nivel")]
    return max(candidatos, key=lambda i: NIVELES.index(i["nivel"])) if candidatos else None


def plan_permanente(cultivo: Cultivo, hoy: date, clima: pd.DataFrame, indicadores: dict,
                    lat: float, lon: float, lang: str, u: dict) -> dict[str, Any]:
    ciclo = riesgo_campana(cultivo, pd.Period(hoy, freq="M"), clima, indicadores.get("elNino"), lat, lon, lang, u,
                           duracion=12)
    actuales = componentes_actuales(indicadores)

    meses, acciones, vistas = [], [], set()
    for i, m in enumerate(ciclo["meses"]):
        periodo = pd.Period(m["mes"], freq="M")
        etapa = cultivo.etapa_de_mes(periodo.month)
        etapa_nombre = etapa.nombre.get(lang, etapa.id) if etapa else "—"
        comp = dict(m["componentes"])
        if i == 0:  # mes actual: el peor entre el clima normal y lo que miden los indicadores hoy
            comp = {k: peor(v, actuales[k]) for k, v in comp.items()}
        meses.append({"mes": m["mes"], "etapa": etapa_nombre, "riesgo": peor(m["riesgo"], *comp.values()),
                      "motivo": m["motivo"], "fuente": m["fuente"]})

        for regla in cultivo.acciones:
            if regla.etapa not in ("*", etapa.id if etapa else None):
                continue
            if NIVELES.index(comp[regla.si]) < NIVELES.index(regla.nivel):
                continue
            clave = (regla.etapa, regla.accion.get("es"))
            if clave in vistas:
                continue
            vistas.add(clave)
            razon, fuente = m["motivo"], m["fuente"]
            por_clima = NIVELES.index(m["componentes"][regla.si]) >= NIVELES.index(regla.nivel)
            if i == 0 and not por_clima:  # la activó un indicador de hoy: se cita ese indicador
                ind = indicador_de(regla.si, indicadores)
                if ind:
                    razon, fuente = ind["detalle"], ind["fuente"]
            acciones.append({
                "etapa": etapa_nombre,
                "accion": regla.accion.get(lang) or regla.accion.get("es"),
                "motivo": texto(lang, "p_motivo", etapa=etapa_nombre.capitalize(), mes=nombre_mes(lang, periodo.month),
                                razon=razon),
                "fuente": fuente, "mes": m["mes"],
            })

    actual = cultivo.etapa_de_mes(hoy.month)
    return {
        "cultivo": cultivo.nombre_en(lang),
        "etapaActual": actual.nombre.get(lang, actual.id) if actual else "—",
        "meses": meses,
        "acciones": acciones,
        "mesMasRiesgoso": ciclo["mesMasRiesgoso"],
        "metodo": ciclo["metodo"],
    }
