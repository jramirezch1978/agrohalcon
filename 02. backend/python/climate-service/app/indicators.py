"""Los 4 indicadores de riesgo: lluvia, humedad del suelo, calor y señal de El Niño.

Regla única: anomalía = valor actual frente al normal histórico de esa zona y época;
nivel = bajo / medio / alto según el tamaño de la anomalía (umbrales en thresholds.py).
"""

from . import thresholds as T
from .schemas import Indicador, IndicadoresRequest, IndicadoresResponse, Nivel

ETIQUETA = {"lluvia": "La lluvia", "humedadSuelo": "La humedad del suelo"}


def anomalia(nombre: str, valor: float, normal: float) -> float:
    """Anomalía CON signo. Lluvia y humedad: fracción relativa (-0.4 = 40 % menos). Calor y mar: °C."""
    if nombre == "lluvia":
        return (valor - normal) / max(normal, T.LLUVIA_NORMAL_MIN_MM)
    if nombre == "humedadSuelo":
        return (valor - normal) / normal if normal > 0 else 0.0
    return valor - normal


def _medida_y_umbrales(nombre: str, a: float) -> tuple[float, tuple[float, float]]:
    """Solo cuenta la dirección que daña al cultivo (p. ej. más humedad no es riesgo de sequía)."""
    if nombre == "lluvia":
        return abs(a), T.LLUVIA_REL  # déficit y exceso dañan
    if nombre == "humedadSuelo":
        return max(0.0, -a), T.HUMEDAD_DEFICIT_REL
    if nombre == "calor":
        return max(0.0, a), T.CALOR_ANOMALIA_C
    return max(0.0, a), T.EL_NINO_SST_C  # elNino


def nivel_de(nombre: str, valor: float, normal: float) -> Nivel:
    medida, (medio, alto) = _medida_y_umbrales(nombre, anomalia(nombre, valor, normal))
    if medida >= alto:
        return "alto"
    if medida >= medio:
        return "medio"
    return "bajo"


def describir(nombre: str, ind: Indicador) -> str:
    """Frase verificable con el dato real, p. ej. 'La humedad del suelo está 40 % por debajo de lo normal'."""
    a = anomalia(nombre, ind.valor, ind.normal)
    if nombre in ETIQUETA:
        if ind.nivel == "bajo":
            return f"{ETIQUETA[nombre]} está dentro de lo normal"
        sentido = "por debajo" if a < 0 else "por encima"
        return f"{ETIQUETA[nombre]} está {round(abs(a) * 100)} % {sentido} de lo normal"
    if nombre == "calor":
        if ind.nivel == "bajo":
            return "La temperatura máxima está dentro de lo normal"
        return f"La temperatura máxima está {a:.1f} °C por encima de lo normal"
    if ind.nivel == "bajo":
        return "El mar frente a la costa está dentro de lo normal"
    return f"El mar frente a la costa está {a:.1f} °C más caliente de lo normal (señal de El Niño)"


def _indicador(nombre: str, req: IndicadoresRequest, valor: float, normal: float) -> Indicador:
    meta = req.meta.get(nombre)
    return Indicador(
        valor=valor,
        normal=normal,
        unidad=(meta.unidad if meta and meta.unidad else T.UNIDADES[nombre]),
        nivel=nivel_de(nombre, valor, normal),
        fuente=(meta.fuente if meta and meta.fuente else T.FUENTES[nombre]),
    )


def calcular_indicadores(req: IndicadoresRequest) -> IndicadoresResponse:
    a, h = req.actual, req.historico
    return IndicadoresResponse(
        lluvia=_indicador("lluvia", req, a.lluviaMm, h.lluviaMm),
        humedadSuelo=_indicador("humedadSuelo", req, a.humedadSuelo, h.humedadSuelo),
        calor=_indicador("calor", req, a.tempMaxC, h.tempMaxC),
        elNino=_indicador("elNino", req, a.sstAnomaliaC, 0.0),  # normal de la anomalía = 0
    )
