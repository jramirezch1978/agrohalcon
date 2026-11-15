"""POST /calcular completo: indicadores + rotaciones (temporal) o plan (permanente) + qué hacer esta quincena."""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from app.calculos.campana import escenario_lluvia
from app.calculos.indicadores import calcular_indicadores, clima_mensual, obtener_datos_power
from app.calculos.permanentes import plan_permanente
from app.calculos.que_hacer import que_hacer
from app.calculos.rotaciones import generar_rotaciones, prioridad_o_defecto
from app.catalogo import buscar, cargar_catalogo
from app.config import umbrales
from app.fuentes.nasa_power import ClienteNasaPower
from app.modelos import PeticionCalculo


async def calcular_recomendacion(p: PeticionCalculo, cliente: ClienteNasaPower, hoy: date | None = None) -> dict[str, Any]:
    hoy = hoy or date.today()
    u = umbrales()
    catalogo = cargar_catalogo(p.catalogo)

    datos = await obtener_datos_power(p.lat, p.lon, cliente, hoy, int(u["ventana_dias"]))
    base = await calcular_indicadores(p.lat, p.lon, p.lang, cliente, hoy, datos=datos)
    indicadores = base["indicadores"]
    clima = clima_mensual(datos)

    if p.tipoCultivo == "permanente":
        cultivo = buscar(catalogo, p.cultivo or "mango")
        if cultivo is None or cultivo.tipo != "permanente":
            raise ValueError(f"Cultivo permanente '{p.cultivo}' no está en el catálogo")
        plan = plan_permanente(cultivo, hoy, clima, indicadores, p.lat, p.lon, p.lang, u)
        qh = que_hacer(indicadores, p.lat, p.lon, p.lang, hoy, "permanente", permanente=cultivo,
                       etapa_actual=plan["etapaActual"])
        return {**base, "tipoCultivo": "permanente", "rotaciones": [], "plan": plan, "queHacer": qh,
                "catalogo": "java" if p.catalogo else "ejemplo"}

    mes_siembra = p.mesSiembra or str(pd.Period(hoy, freq="M") + 1)
    # "¿Y si el año viene seco o lluvioso?": escenario hipotético sobre la lluvia normal (solo rotaciones)
    escenario = p.escenario or "normal"
    clima = escenario_lluvia(clima, u["escenarios"][escenario])
    rotaciones = generar_rotaciones(catalogo, mes_siembra, clima, indicadores, p.lat, p.lon, p.lang, u,
                                    prioridad=p.prioridad, salinidad=p.salinidad, tipo_suelo=p.tipoSuelo,
                                    fuente_suelo=p.fuenteSuelo, agua_disponible=p.aguaDisponible)
    mejor = rotaciones[0] if rotaciones else None
    primer = buscar(catalogo, mejor["cultivos"][0]) if mejor else None
    qh = que_hacer(indicadores, p.lat, p.lon, p.lang, hoy, "temporal", mejor_rotacion=mejor, primer_cultivo=primer)
    prioridad = prioridad_o_defecto(p.prioridad, u)
    perfil = {"prioridad": prioridad, "pesos": u["prioridades"]["pesos"][prioridad],
              "tipoSuelo": p.tipoSuelo, "salinidad": p.salinidad, "fuenteSuelo": p.fuenteSuelo,
              "aguaDisponible": p.aguaDisponible, "escenario": escenario, "factorLluvia": u["escenarios"][escenario]}
    return {**base, "tipoCultivo": "temporal", "mesSiembra": mes_siembra, "rotaciones": rotaciones, "queHacer": qh,
            "perfil": perfil,
            "catalogo": "java" if p.catalogo else "ejemplo"}
