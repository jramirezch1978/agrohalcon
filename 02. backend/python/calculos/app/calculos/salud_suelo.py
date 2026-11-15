"""Puntaje de SALUD DEL SUELO de una rotación (0-100, sin IA; reglas y puntos en config/umbrales.yaml → salud_suelo).

Parte de una base y suma o resta según cómo la rotación trata al suelo:
- monocultivo (el mismo cultivo dos veces): agota los mismos nutrientes y mantiene sus plagas → resta.
- misma familia botánica (cultivos distintos): lo mismo, en menor medida → resta.
- leguminosa: fija nitrógeno del aire en el suelo → suma (una vez por rotación).
- raíces de distinta profundidad: aprovechan capas distintas del suelo → suma.
- cultivo de cobertura: protege el suelo de la erosión y el sol → suma (una vez por rotación).
- dos cultivos de mucha agua seguidos: tanto riego cansa el suelo y lo puede salinizar → resta.
- agua alta en suelo salino (solo si la parcela dice que es salino): el riego intenso sube las sales → resta.
- cultivo poco tolerante a la sal en suelo salino (dato del agricultor + tolerancia del catálogo) → resta.
- suelo arenoso con cultivo de mucha agua: el arenoso retiene poca agua → resta.
Si falta el dato del catálogo (familia, profundidad), la regla no se aplica: nunca se inventa.
Resultado limitado a 0-100.
"""
from __future__ import annotations

from app.catalogo import Cultivo
from app.textos.plantillas import texto

FUENTE_CATALOGO = "catálogo de cultivos"
FUENTE_AGRICULTOR = "dato del agricultor"
FUENTE_SOILGRIDS = "SoilGrids (ISRIC)"
NIVEL_TOL = ("baja", "media", "alta")


def _item(regla: str, puntos: int, explicacion: str, fuente: str = FUENTE_CATALOGO) -> dict:
    return {"regla": regla, "puntos": puntos, "explicacion": explicacion, "fuente": fuente}


def descuentos_suelo(cultivos: list[Cultivo], u: dict, lang: str = "es", salinidad: str | None = None,
                     tipo_suelo: str | None = None, fuente_suelo: str | None = None) -> list[dict]:
    us = u["salud_suelo"]
    nombre = lambda c: c.nombre_en(lang).lower()  # noqa: E731  (en medio de la frase)
    Nombre = lambda c: c.nombre_en(lang)  # noqa: E731  (al inicio de la frase)
    out: list[dict] = []
    a, b = cultivos[0], cultivos[-1]

    # 1) Repetir cultivo o familia en temporadas seguidas
    if a.id == b.id:
        out.append(_item("monocultivo", us["monocultivo"], texto(lang, "s_monocultivo", cultivo=nombre(a))))
    elif a.familia and a.familia == b.familia:
        out.append(_item("misma_familia", us["misma_familia"],
                         texto(lang, "s_familia", a=Nombre(a), b=nombre(b), familia=a.familia)))

    # 2) Leguminosa: fija nitrógeno
    if leg := next((c for c in cultivos if c.leguminosa), None):
        out.append(_item("leguminosa", us["leguminosa"], texto(lang, "s_leguminosa", cultivo=Nombre(leg))))

    # 3) Raíces de distinta profundidad
    if a.id != b.id and a.profundidad_raiz and b.profundidad_raiz and a.profundidad_raiz != b.profundidad_raiz:
        out.append(_item("raices_alternas", us["raices_alternas"], texto(
            lang, "s_raices", a=Nombre(a), b=nombre(b),
            pa=texto(lang, f"raiz_{a.profundidad_raiz}"), pb=texto(lang, f"raiz_{b.profundidad_raiz}"))))

    # 4) Cultivo de cobertura
    if cob := next((c for c in cultivos if c.cobertura), None):
        out.append(_item("cobertura", us["cobertura"], texto(lang, "s_cobertura", cultivo=Nombre(cob))))

    # 4b) Dos cultivos de mucha agua seguidos
    if len(cultivos) > 1 and all((c.usoAgua or c.agua) == "alto" for c in cultivos):
        out.append(_item("agua_alta_seguidos", us["agua_alta_seguidos"],
                         texto(lang, "s_agua_seguidos", a=Nombre(a), b=nombre(b))))

    # 5) Agua alta en suelo salino (dato de la parcela)
    puntos_sal = us["agua_alta_suelo_salino"].get(salinidad or "no", 0)
    if puntos_sal and (sed := next((c for c in cultivos if (c.usoAgua or c.agua) == "alto"), None)):
        out.append(_item("agua_suelo_salino", puntos_sal, texto(lang, "s_agua_salino", cultivo=Nombre(sed)),
                         fuente=FUENTE_AGRICULTOR))

    # 6) Cultivo poco tolerante a la sal en suelo salino (sin dato de tolerancia → no se aplica)
    tabla = us["salinidad_tolerancia"].get(salinidad or "no")
    if tabla:
        con_dato = [(tabla[c.tolerancia_salinidad], c) for c in cultivos if c.tolerancia_salinidad]
        if con_dato and (peor := min(con_dato, key=lambda x: x[0]))[0]:
            out.append(_item("tolerancia_salinidad", peor[0], texto(
                lang, "s_tolerancia_sal", cultivo=Nombre(peor[1]), tol=texto(lang, f"tol_{peor[1].tolerancia_salinidad}")),
                fuente=FUENTE_AGRICULTOR))

    # 6b) Meses de suelo desnudo en el año (sin cultivo entre una campaña y la siguiente)
    desnudo = meses_suelo_desnudo(cultivos)
    if desnudo is not None and desnudo >= us.get("suelo_desnudo_desde_meses", 99):
        out.append(_item("suelo_desnudo", us["suelo_desnudo"], texto(lang, "s_desnudo", n=desnudo)))

    # 7) Suelo arenoso con cultivo de mucha agua
    if tipo_suelo == "arenoso" and (sed := next((c for c in cultivos if (c.usoAgua or c.agua) == "alto"), None)):
        out.append(_item("arenoso_agua_alta", us["arenoso_agua_alta"], texto(lang, "s_arenoso", cultivo=Nombre(sed)),
                         fuente=FUENTE_SOILGRIDS if fuente_suelo == "soilgrids" else FUENTE_AGRICULTOR))
    return out


def meses_suelo_desnudo(cultivos: list[Cultivo]) -> int | None:
    """Meses del año sin cultivo: 12 menos la duración de la rotación (None si falta la duración)."""
    if any(not c.duracion_meses for c in cultivos):
        return None
    return max(0, 12 - sum(c.duracion_meses for c in cultivos))


def puntaje_suelo(cultivos: list[Cultivo], u: dict, lang: str = "es", salinidad: str | None = None,
                  tipo_suelo: str | None = None, fuente_suelo: str | None = None) -> tuple[int, list[dict]]:
    desc = descuentos_suelo(cultivos, u, lang, salinidad, tipo_suelo, fuente_suelo)
    return max(0, min(100, u["salud_suelo"]["base"] + sum(d["puntos"] for d in desc))), desc
