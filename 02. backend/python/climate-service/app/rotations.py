"""Puntaje de rotaciones (0-100): se parte de 100 y se descuentan puntos cuando el clima esperado
choca con lo que el cultivo necesita. Todas las reglas y números están en thresholds.py."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from . import thresholds as T
from .crops import DatosInvalidos, generar_candidatas, indexar
from .indicators import anomalia, describir, fmt1, nivel_de
from .meses import NOMBRES_MES
from .schemas import (
    Cultivo,
    Indicador,
    IndicadoresResponse,
    Nivel,
    RotacionCandidata,
    RotacionResultado,
)

Nivel2 = Literal["alta", "media", "baja"]

AGUA_TXT = {"alta": "mucha agua", "media": "agua moderada", "baja": "poca agua"}


@dataclass(frozen=True)
class Descuento:
    indicador: str  # lluvia | humedadSuelo | calor | elNino | temporada
    puntos: float
    frase: str  # empieza en minúscula; se une al nombre del cultivo
    generico: bool = False  # True = habla del clima, no del cultivo: se dice una vez, sin nombre de cultivo


@dataclass(frozen=True)
class Evaluacion:
    resultado: RotacionResultado
    cultivo1: Cultivo
    cultivo2: Cultivo


def _minuscula(texto: str) -> str:
    return texto[:1].lower() + texto[1:]


def _mayuscula(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


def riesgo_de(puntaje: int) -> Nivel:
    if puntaje >= T.RIESGO_BAJO_DESDE:
        return "bajo"
    if puntaje >= T.RIESGO_MEDIO_DESDE:
        return "medio"
    return "alto"


def descuentos_cultivo(
    c: Cultivo, ind: IndicadoresResponse, mes: int, es_primero: bool
) -> list[Descuento]:
    """Lista de descuentos de UN cultivo frente a los indicadores. Cada descuento dice por qué."""
    out: list[Descuento] = []
    agua = c.aguaNecesaria

    # 1) Falta de agua en el suelo (el indicador principal de sequía, SMAP)
    if anomalia("humedadSuelo", ind.humedadSuelo.valor, ind.humedadSuelo.normal) < 0:
        pts = T.SEQUIA_PTS[agua][ind.humedadSuelo.nivel]
        if pts:
            union = "y" if agua != "baja" else "pero"
            frase = f"necesita {AGUA_TXT[agua]} {union} {_minuscula(describir('humedadSuelo', ind.humedadSuelo))}"
            out.append(Descuento("humedadSuelo", pts, frase))

    # 2) Lluvia: faltante (cuenta menos que el suelo) o exceso (encharcamiento)
    a_lluvia = anomalia("lluvia", ind.lluvia.valor, ind.lluvia.normal)
    if a_lluvia < 0:
        pts = T.SEQUIA_PTS[agua][ind.lluvia.nivel] * T.LLUVIA_DEFICIT_FACTOR
        if pts:
            out.append(Descuento("lluvia", pts, _minuscula(describir("lluvia", ind.lluvia)), generico=True))
    elif a_lluvia > 0:
        pts = T.EXCESO_PTS[ind.lluvia.nivel] * T.EXCESO_FACTOR[agua]
        riesgo_inundacion = a_lluvia >= T.LLUVIA_EXCESO_EXTREMO_REL
        if riesgo_inundacion:
            pts = max(pts, T.EXCESO_EXTREMO_PTS)
        if pts:
            cola = "hay riesgo de inundación" if riesgo_inundacion else "puede encharcar el cultivo"
            frase = f"{_minuscula(describir('lluvia', ind.lluvia))} y {cola}"
            out.append(Descuento("lluvia", pts, frase, generico=True))

    # 3) Calor frente al máximo que tolera el cultivo
    margen = c.tempMaxC - ind.calor.valor
    pts = T.CALOR_NIVEL_PTS[ind.calor.nivel]
    if margen < 0:
        pts += T.CALOR_PTS_POR_C_SOBRE_LIMITE * -margen
    elif margen > T.CALOR_MARGEN_SEGURO_C:
        pts *= T.CALOR_FACTOR_CON_MARGEN
    pts = min(pts, T.CALOR_MAX_PTS)
    if pts:
        if margen < 0:
            frase = f"el calor esperado ({ind.calor.valor:.0f} °C) pasa su límite ({c.tempMaxC:.0f} °C)"
        else:
            frase = f"el calor ({ind.calor.valor:.0f} °C) se acerca a su límite ({c.tempMaxC:.0f} °C)"
        out.append(Descuento("calor", pts, frase))

    # 4) Señal de El Niño: anticipa exceso de lluvia
    pts = T.EL_NINO_PTS[ind.elNino.nivel] * T.EXCESO_FACTOR[agua]
    if ind.elNino.valor >= T.EL_NINO_EXTREMO_C:
        pts = max(pts, T.EL_NINO_EXTREMO_PTS)
        frase = f"hay una señal de El Niño extraordinaria (+{fmt1(ind.elNino.valor)} °C en el mar) con riesgo de lluvias e inundaciones"
        out.append(Descuento("elNino", pts, frase, generico=True))
    elif pts:
        frase = f"hay señal de El Niño (+{fmt1(ind.elNino.valor)} °C en el mar) y puede traer exceso de lluvia"
        out.append(Descuento("elNino", pts, frase, generico=True))

    # 5) Época de siembra (solo el cultivo que se siembra ahora)
    if es_primero and c.mesesSiembra and mes not in c.mesesSiembra:
        out.append(
            Descuento(
                "temporada",
                T.FUERA_DE_TEMPORADA_PTS,
                f"{NOMBRES_MES[mes - 1]} está fuera de su época de siembra",
            )
        )
    return out


def _explicar(c1: Cultivo, c2: Cultivo, d1: list[Descuento], d2: list[Descuento]) -> str:
    # Peso de cada descuento en el puntaje final; el mismo cultivo repetido suma ambos pesos
    acumulado: dict[tuple[str | None, str, str], float] = {}
    for c, descuentos, peso in ((c1, d1, T.PESO_CULTIVO1), (c2, d2, T.PESO_CULTIVO2)):
        for d in descuentos:
            clave = (None if d.generico else c.nombre, d.indicador, d.frase)  # lo genérico se dice una sola vez
            acumulado[clave] = acumulado.get(clave, 0.0) + d.puntos * peso
    relevantes = sorted(
        (kv for kv in acumulado.items() if kv[1] >= T.DESCUENTO_MINIMO_EXPLICADO),
        key=lambda kv: -kv[1],
    )[:2]

    mismo_cultivo = str(c1.id) == str(c2.id)
    nota_plagas = "; repetir el mismo cultivo no corta el ciclo de plagas" if mismo_cultivo else ""

    if not relevantes:
        if c1.aguaNecesaria == c2.aguaNecesaria == "baja":
            return "Usa poca agua y los indicadores actuales casi no la afectan" + nota_plagas
        return "Los indicadores actuales casi no afectan a esta rotación" + nota_plagas

    # Agrupa por cultivo para no repetir su nombre en cada frase
    por_cultivo: dict[str | None, list[str]] = {}
    for (nombre, _indicador, frase), _pts in relevantes:
        por_cultivo.setdefault(nombre, []).append(frase)

    partes = []
    for nombre, frases in por_cultivo.items():
        cuerpo = " y ".join(frases)
        # Lo del clima (nombre None) y el monocultivo van sin nombre; lo propio de cada cultivo, con "Cultivo: ..."
        partes.append(_mayuscula(cuerpo) if nombre is None or mismo_cultivo else f"{nombre}: {cuerpo}")
    return "; ".join(partes) + nota_plagas


def evaluar_rotacion(
    rot: RotacionCandidata,
    c1: Cultivo,
    c2: Cultivo,
    ind: IndicadoresResponse,
    mes: int,
) -> Evaluacion:
    d1 = descuentos_cultivo(c1, ind, mes, es_primero=True)
    d2 = descuentos_cultivo(c2, ind, mes, es_primero=False)
    p1 = min(100.0, sum(d.puntos for d in d1))
    p2 = min(100.0, sum(d.puntos for d in d2))
    descuento = T.PESO_CULTIVO1 * p1 + T.PESO_CULTIVO2 * p2
    if str(c1.id) == str(c2.id):
        descuento += T.MONOCULTIVO_PTS
    puntaje = max(0, min(100, round(100 - descuento)))
    resultado = RotacionResultado(
        id=rot.id,
        nombre=rot.nombre or f"{c1.nombre} - {c2.nombre}",
        puntaje=puntaje,
        riesgo=riesgo_de(puntaje),
        explicacion=_explicar(c1, c2, d1, d2),
    )
    return Evaluacion(resultado, c1, c2)


def evaluar_todas(
    ind: IndicadoresResponse,
    cultivos: list[Cultivo],
    candidatas: list[RotacionCandidata],
    fecha: date,
) -> list[Evaluacion]:
    por_id = indexar(cultivos)
    evaluaciones = []
    for rot in candidatas:
        try:
            c1, c2 = por_id[str(rot.cultivo1Id)], por_id[str(rot.cultivo2Id)]
        except KeyError as e:
            raise DatosInvalidos(
                f"La rotación {rot.id} usa el cultivo {e.args[0]!r}, que no está en el catálogo enviado"
            ) from None
        evaluaciones.append(evaluar_rotacion(rot, c1, c2, ind, fecha.month))
    return evaluaciones


def seleccionar(
    evaluaciones: list[Evaluacion], top: int, actual_id: int | None, variadas: bool
) -> list[Evaluacion]:
    """Elige las `top` mejores. Si `variadas` (candidatas generadas por el servicio), descarta los
    monocultivos (no son rotación) y prefiere distintos cultivos de inicio, para que el comparador
    no muestre tres variantes de lo mismo. La rotación actual del agricultor siempre se incluye."""
    orden = sorted(evaluaciones, key=lambda e: (-e.resultado.puntaje, e.resultado.id))
    if variadas:
        orden = [e for e in orden if str(e.cultivo1.id) != str(e.cultivo2.id)] or orden
        vistos: set[str] = set()
        primeras, resto = [], []
        for e in orden:
            clave = str(e.cultivo1.id)
            (resto if clave in vistos else primeras).append(e)
            vistos.add(clave)
        orden = primeras + resto
    elegidas = orden[:top]

    if actual_id is not None and all(e.resultado.id != actual_id for e in elegidas):
        actual = next((e for e in evaluaciones if e.resultado.id == actual_id), None)
        if actual is None:
            raise DatosInvalidos(f"rotacionActualId={actual_id} no está entre las rotaciones evaluadas")
        elegidas = elegidas[: top - 1] + [actual]
    return sorted(elegidas, key=lambda e: (-e.resultado.puntaje, e.resultado.id))


INDICADORES = ("lluvia", "humedadSuelo", "calor", "elNino")


def perturbar(ind: IndicadoresResponse, signo: int, solo: str | None = None) -> IndicadoresResponse:
    """Empuja un indicador (o todos, si `solo` es None) K·σ hacia el lado malo (signo=+1) o el bueno (signo=-1)
    y recalcula sus niveles. 'Malo' = más lejos de lo normal en la dirección que daña (más déficit de agua, más
    calor, más señal de El Niño; la lluvia daña en ambos sentidos: se aleja o se acerca a su normal)."""
    nuevos = {}
    for nombre in INDICADORES:
        i: Indicador = getattr(ind, nombre)
        if solo is not None and nombre != solo:
            nuevos[nombre] = i
            continue
        tipo, magnitud = T.INCERTIDUMBRE[nombre]
        sigma = T.INCERTIDUMBRE_K * (magnitud * abs(i.valor) if tipo == "rel" else magnitud)
        if nombre == "lluvia":
            direccion = 1 if i.valor >= i.normal else -1  # alejarse de lo normal
            valor = i.valor + signo * direccion * sigma
        elif nombre == "humedadSuelo":
            valor = i.valor - signo * sigma  # malo = menos humedad
        else:
            valor = i.valor + signo * sigma  # malo = más calor / más señal de El Niño
        valor = max(0.0, valor) if nombre in ("lluvia", "humedadSuelo") else valor
        if nombre == "humedadSuelo":
            valor = min(valor, 1.0)
        nuevos[nombre] = i.model_copy(update={"valor": valor, "nivel": nivel_de(nombre, valor, i.normal)})
    return IndicadoresResponse(**nuevos)


def _confianza(ancho: int) -> Nivel2:
    if ancho <= T.CONFIANZA_ALTA_HASTA:
        return "alta"
    return "media" if ancho <= T.CONFIANZA_MEDIA_HASTA else "baja"


def con_incertidumbre(
    elegidas: list[Evaluacion], ind: IndicadoresResponse, fecha: date, candidatas: list[RotacionCandidata]
) -> list[Evaluacion]:
    """Añade puntajeMin / puntajeMax / confianza por propagación de errores INDEPENDIENTES: se mueve cada indicador
    1 σ por separado, se mide cuánto cambia el puntaje y los cambios se suman en cuadratura (raíz de la suma de cuadrados).
    (Empujar los 4 a la vez al peor lado sería un caso extremo muy poco probable, no un rango de 1 σ.)"""
    por_id = {r.id: r for r in candidatas}
    salida = []
    for e in elegidas:
        rot = por_id.get(e.resultado.id) or RotacionCandidata(
            id=e.resultado.id, nombre=e.resultado.nombre, cultivo1Id=e.cultivo1.id, cultivo2Id=e.cultivo2.id
        )
        base = e.resultado.puntaje
        bajan, suben = [], []
        for nombre in INDICADORES:
            for signo, lista in ((+1, bajan), (-1, suben)):
                p = evaluar_rotacion(rot, e.cultivo1, e.cultivo2, perturbar(ind, signo, nombre), fecha.month).resultado.puntaje
                lista.append(p - base)
        baja = sum(min(d, 0) ** 2 for d in bajan + suben) ** 0.5  # solo cuenta lo que empeora el puntaje
        sube = sum(max(d, 0) ** 2 for d in bajan + suben) ** 0.5
        p_min, p_max = max(0, round(base - baja)), min(100, round(base + sube))
        r = e.resultado.model_copy(update={"puntajeMin": p_min, "puntajeMax": p_max, "confianza": _confianza(p_max - p_min)})
        salida.append(Evaluacion(r, e.cultivo1, e.cultivo2))
    return salida


def rotaciones_para(
    ind: IndicadoresResponse,
    cultivos: list[Cultivo],
    candidatas: list[RotacionCandidata] | None,
    fecha: date,
    top: int,
    actual_id: int | None,
    incertidumbre: bool = False,
) -> tuple[list[Evaluacion], list[Evaluacion]]:
    """Devuelve (las elegidas para mostrar, todas las evaluadas). 'Qué hago' mira todas."""
    variadas = candidatas is None
    candidatas = candidatas if candidatas is not None else generar_candidatas(cultivos)
    todas = evaluar_todas(ind, cultivos, candidatas, fecha)
    elegidas = seleccionar(todas, top, actual_id, variadas)
    if incertidumbre:
        elegidas = con_incertidumbre(elegidas, ind, fecha, candidatas)
    return elegidas, todas
