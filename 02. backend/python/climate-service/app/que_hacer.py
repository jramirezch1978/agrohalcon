"""'¿Qué hago esta quincena?': acción, motivo y satélite que respalda el dato. Solo reglas."""

from . import thresholds as T
from .indicators import anomalia, describir
from .rotations import Evaluacion
from .schemas import IndicadoresResponse, QueHacer

# Orden de prioridad cuando varios indicadores tienen el mismo nivel: primero la sequía
# (SMAP, el indicador principal de AgroShift), luego lluvia, calor y El Niño.
PRIORIDAD = ("humedadSuelo", "lluvia", "calor", "elNino")
RANGO_NIVEL = {"bajo": 0, "medio": 1, "alto": 2}


def indicador_dominante(ind: IndicadoresResponse) -> str:
    """El de nivel más alto; en empate, el primero de PRIORIDAD. Es el que explica la recomendación."""
    return max(PRIORIDAD, key=lambda n: (RANGO_NIVEL[getattr(ind, n).nivel], -PRIORIDAD.index(n)))


def construir_que_hacer(
    ind: IndicadoresResponse, mostradas: list[Evaluacion], todas: list[Evaluacion]
) -> QueHacer:
    """`mostradas` = las rotaciones que ve el agricultor. `todas` = todo lo evaluado: el cultivo
    a evitar sale de aquí aunque no aparezca en el comparador."""
    mejor = max(mostradas, key=lambda e: e.resultado.puntaje)
    peor = min(todas, key=lambda e: e.resultado.puntaje)
    nombre = indicador_dominante(ind)
    dominante = getattr(ind, nombre)

    if dominante.nivel == "bajo":
        fuentes = ", ".join(dict.fromkeys(getattr(ind, n).fuente for n in PRIORIDAD))
        return QueHacer(
            accion=f"Puedes sembrar con normalidad; la mejor opción es la rotación {mejor.resultado.nombre}",
            motivo="Los cuatro indicadores están dentro de lo normal",
            fuente=fuentes,
        )

    if anomalia("lluvia", ind.lluvia.valor, ind.lluvia.normal) >= T.LLUVIA_EXCESO_EXTREMO_REL:
        accion = (
            "Riesgo de inundación: no siembres esta quincena y espera a que baje la lluvia. "
            f"Si debes sembrar, la opción menos riesgosa es {mejor.resultado.nombre}. "
            "Consulta con un técnico agrario"
        )
        # En una inundación el dato que respalda la decisión es la lluvia, aunque otro indicador empate
        nombre, dominante = "lluvia", ind.lluvia
    elif ind.elNino.valor >= T.EL_NINO_EXTREMO_C:
        accion = (
            "Señal de El Niño extraordinaria: sigue los avisos de ENFEN y consulta a un técnico agrario antes de sembrar. "
            f"Si debes sembrar, la opción menos riesgosa es {mejor.resultado.nombre}"
        )
        nombre, dominante = "elNino", ind.elNino
    elif mejor.resultado.riesgo == "alto":
        accion = (
            f"Riesgo alto en todas las rotaciones; la menos riesgosa es {mejor.resultado.nombre}. "
            "Consulta con un técnico agrario antes de sembrar"
        )
    elif peor.resultado.riesgo == "alto" and str(peor.cultivo1.id) != str(mejor.cultivo1.id):
        accion = (
            f"No siembres {peor.cultivo1.nombre.lower()} esta quincena; "
            f"elige la rotación {mejor.resultado.nombre}"
        )
    else:
        accion = f"Elige la rotación {mejor.resultado.nombre} esta quincena"

    return QueHacer(accion=accion, motivo=describir(nombre, dominante), fuente=dominante.fuente)
