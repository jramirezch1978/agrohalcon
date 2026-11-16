"""POST /calcular completo: indicadores + rotaciones (temporal) o plan (permanente) + qué hacer esta quincena."""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.calculos.campana import escenario_lluvia
from app.calculos.indicadores import calcular_indicadores, clima_mensual, obtener_datos_power
from app.calculos.permanentes import plan_permanente
from app.calculos.que_hacer import que_hacer
from app.calculos.reglas import nivel_el_nino
from app.calculos.rotaciones import agua_con_escenario, generar_rotaciones, prioridad_o_defecto
from app.catalogo import buscar, cargar_catalogo
from app.config import umbrales
from app.fuentes.nasa_power import ClienteNasaPower
from app.modelos import PeticionCalculo
from app.textos.plantillas import dir_mar, signo, texto

FUENTE_HIPOTETICA = "hipotético"


def con_nino_hipotetico(indicadores: dict, anomalia: float | None, lang: str, u: dict) -> dict:
    """Copia de los indicadores con El Niño reemplazado por una anomalía HIPOTÉTICA (simulador "¿y si el mar sube?").
    Las reglas son las mismas de siempre; la fuente dice "hipotético" para que nunca se confunda con el dato real."""
    if anomalia is None:
        return indicadores
    real = indicadores.get("elNino") or {}
    nino = {**real, "valor": round(anomalia, 2), "anomalia": round(anomalia, 2),
            "direccion": "exceso" if anomalia >= 0 else "deficit", "nivel": nivel_el_nino(anomalia, u["el_nino"]),
            "fuente": FUENTE_HIPOTETICA, "hipotetico": True, "disponible": True, "semana": real.get("semana") or "?",
            "detalle": texto(lang, "elnino_hipotetico", signo=signo(anomalia), valor=abs(anomalia),
                              dir=dir_mar(lang, anomalia))}
    return {**indicadores, "elNino": nino}


def _firma(rotaciones: list[dict]) -> list[tuple]:
    """Lo que el agricultor ve de cada rotación: nombre, puntaje y el riesgo de cada mes."""
    return [(r["nombre"], r["puntaje"], tuple(m["riesgo"] for m in r["ciclo"]["meses"])) for r in rotaciones]


async def calcular_recomendacion(p: PeticionCalculo, cliente: ClienteNasaPower, hoy: date | None = None) -> dict[str, Any]:
    hoy = hoy or date.today()
    u = umbrales()
    catalogo = cargar_catalogo(p.catalogo)

    datos = await obtener_datos_power(p.lat, p.lon, cliente, hoy, int(u["ventana_dias"]))
    base = await calcular_indicadores(p.lat, p.lon, p.lang, cliente, hoy, datos=datos)
    # Los indicadores que se MUESTRAN son siempre los reales; el simulador solo cambia los que deciden.
    indicadores = con_nino_hipotetico(base["indicadores"], p.ninoHipotetico, p.lang, u)
    clima = clima_mensual(datos)

    if p.tipoCultivo == "permanente":
        cultivo = buscar(catalogo, p.cultivo or "mango")
        if cultivo is None or cultivo.tipo != "permanente":
            raise ValueError(f"Cultivo permanente '{p.cultivo}' no está en el catálogo")
        plan = plan_permanente(cultivo, hoy, clima, indicadores, p.lat, p.lon, p.lang, u)
        qh = que_hacer(indicadores, p.lat, p.lon, p.lang, hoy, "permanente", permanente=cultivo,
                       etapa_actual=plan["etapaActual"])
        return {**base, "tipoCultivo": "permanente", "rotaciones": [], "plan": plan, "queHacer": qh,
                "perfil": {"ninoHipotetico": p.ninoHipotetico},
                "catalogo": "java" if p.catalogo else "ejemplo"}

    mes_siembra = p.mesSiembra or str(pd.Period(hoy, freq="M") + 1)
    escenario = p.escenario or "normal"
    perfil_suelo = {"prioridad": p.prioridad, "salinidad": p.salinidad, "tipo_suelo": p.tipoSuelo,
                    "fuente_suelo": p.fuenteSuelo}

    def rotaciones_de(esc: str) -> list[dict]:
        # "¿Y si el año viene seco o lluvioso?": hipotético sobre la lluvia normal Y sobre el agua de riego
        return generar_rotaciones(catalogo, mes_siembra, escenario_lluvia(clima, u["escenarios"][esc]), indicadores,
                                  p.lat, p.lon, p.lang, u, **perfil_suelo,
                                  agua_disponible=agua_con_escenario(p.aguaDisponible, esc, u))

    rotaciones = rotaciones_de(escenario)
    # Si el escenario no cambia nada de lo que se ve, se dice (en la costa casi no llueve: manda el riego)
    sin_efecto = escenario != "normal" and _firma(rotaciones) == _firma(rotaciones_de("normal"))

    mejor = rotaciones[0] if rotaciones else None
    primer = buscar(catalogo, mejor["cultivos"][0]) if mejor else None
    qh = que_hacer(indicadores, p.lat, p.lon, p.lang, hoy, "temporal", mejor_rotacion=mejor, primer_cultivo=primer)
    prioridad = prioridad_o_defecto(p.prioridad, u)
    perfil = {"prioridad": prioridad, "pesos": u["prioridades"]["pesos"][prioridad],
              "tipoSuelo": p.tipoSuelo, "salinidad": p.salinidad, "fuenteSuelo": p.fuenteSuelo,
              "aguaDisponible": p.aguaDisponible, "escenario": escenario, "factorLluvia": u["escenarios"][escenario],
              "aguaConEscenario": agua_con_escenario(p.aguaDisponible, escenario, u),
              "escenarioSinEfecto": sin_efecto,
              "notaEscenario": texto(p.lang, "esc_sin_efecto") if sin_efecto else None,
              "ninoHipotetico": p.ninoHipotetico}
    return {**base, "tipoCultivo": "temporal", "mesSiembra": mes_siembra, "rotaciones": rotaciones, "queHacer": qh,
            "perfil": perfil,
            "catalogo": "java" if p.catalogo else "ejemplo"}
