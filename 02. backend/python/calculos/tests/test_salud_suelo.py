"""Salud del suelo de cada rotación: una prueba por regla (config/umbrales.yaml → salud_suelo)."""
from app.calculos.rotaciones import evaluar_rotacion, generar_rotaciones
from app.calculos.salud_suelo import puntaje_suelo
from app.catalogo import Cultivo, buscar, cargar_catalogo
from tests.test_api_calcular import cliente_api  # noqa: F401  (fixture)
from tests.test_fase2 import NAIROBI, clima, indicadores

CAT = cargar_catalogo(None)
ARROZ, MAIZ, FRIJOL, ALGODON = (buscar(CAT, x) for x in ("arroz", "maiz", "frijol", "algodon"))


def reglas(desc):
    return {d["regla"]: d["puntos"] for d in desc}


def test_arroz_tras_arroz_resta(umbrales):
    p, desc = puntaje_suelo([ARROZ, ARROZ], umbrales)
    assert reglas(desc) == {"monocultivo": -30, "agua_alta_seguidos": -10} and p == 30
    assert "agota" in desc[0]["explicacion"] and desc[0]["fuente"] == "catálogo de cultivos"


def test_misma_familia_resta_menos_que_monocultivo(umbrales):
    p, desc = puntaje_suelo([ARROZ, MAIZ], umbrales)       # ambas Poaceae
    assert reglas(desc)["misma_familia"] == -15 and "Poaceae" in desc[0]["explicacion"]
    assert p == 70 - 15 + 10 + reglas(desc).get("suelo_desnudo", 0)   # + raíces alternas; − suelo desnudo si aplica


def test_frijol_suma_por_leguminosa(umbrales):
    p, desc = puntaje_suelo([ARROZ, FRIJOL], umbrales)
    r = reglas(desc)
    assert r["leguminosa"] == 15 and r["cobertura"] == 5 and r["raices_alternas"] == 10
    assert p == min(100, 100 + r.get("suelo_desnudo", 0))
    assert "nitrógeno" in next(d for d in desc if d["regla"] == "leguminosa")["explicacion"]


def test_leguminosa_cuenta_una_sola_vez(umbrales):
    _, desc = puntaje_suelo([FRIJOL, FRIJOL], umbrales)
    assert [d["regla"] for d in desc].count("leguminosa") == 1 and "monocultivo" in reglas(desc)


def test_raices_iguales_no_suman(umbrales):
    otro = MAIZ.model_copy(update={"id": "otro", "familia": "Otra"})
    _, desc = puntaje_suelo([MAIZ, otro], umbrales)
    assert "raices_alternas" not in reglas(desc)


def test_sin_dato_no_aplica_reglas(umbrales):
    """Un catálogo sin familia ni profundidad (p. ej. base sin migrar) queda en la base: nada inventado."""
    a = Cultivo(id="a", nombre="A", tipo="temporal", temp_min=10, temp_max=30, agua="medio")
    b = Cultivo(id="b", nombre="B", tipo="temporal", temp_min=10, temp_max=30, agua="medio")
    p, desc = puntaje_suelo([a, b], umbrales)
    assert desc == [] and p == umbrales["salud_suelo"]["base"]


def test_agua_alta_en_suelo_salino_resta_solo_si_lo_dice_el_agricultor(umbrales):
    _, d_sin = puntaje_suelo([ARROZ, FRIJOL], umbrales)
    _, d_leve = puntaje_suelo([ARROZ, FRIJOL], umbrales, salinidad="leve")
    _, d_alta = puntaje_suelo([ARROZ, FRIJOL], umbrales, salinidad="alta")
    assert "agua_suelo_salino" not in reglas(d_sin)
    assert reglas(d_leve)["agua_suelo_salino"] == -10 and reglas(d_alta)["agua_suelo_salino"] == -20
    item = next(d for d in d_alta if d["regla"] == "agua_suelo_salino")
    assert item["fuente"] == "dato del agricultor"
    assert reglas(puntaje_suelo([MAIZ, FRIJOL], umbrales, salinidad="alta")[1]).get("agua_suelo_salino") is None


def test_rotacion_devuelve_los_dos_puntajes(umbrales):
    r = evaluar_rotacion([ARROZ, FRIJOL], "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales)
    assert r["saludSuelo"] == 100 + reglas(r["descuentosSuelo"]).get("suelo_desnudo", 0) and r["puntajeAgua"] == 20
    w = umbrales["prioridades"]["pesos"]["arriesgar_menos"]                  # prioridad por defecto
    assert r["puntaje"] == round(r["riesgoClimatico"] * w["clima"] + r["saludSuelo"] * w["suelo"] + 20 * w["agua"])
    assert {"regla", "puntos", "explicacion", "fuente"} <= set(r["descuentosSuelo"][0])


def test_textos_en_ingles(umbrales):
    _, desc = puntaje_suelo([ARROZ, FRIJOL], umbrales, lang="en")
    assert any("legume" in d["explicacion"] for d in desc)


def test_dos_cultivos_de_mucha_agua_seguidos_restan(umbrales):
    sediento = MAIZ.model_copy(update={"id": "sediento", "familia": "Otra", "agua": "alto", "usoAgua": "alto"})
    _, d = puntaje_suelo([ARROZ, sediento], umbrales)
    assert reglas(d)["agua_alta_seguidos"] == -10 and "mucha agua" in next(x for x in d if x["regla"] == "agua_alta_seguidos")["explicacion"]
    _, d = puntaje_suelo([ARROZ, FRIJOL], umbrales)                    # frijol usa poca agua
    assert "agua_alta_seguidos" not in reglas(d)


# ---------- Punto 2: información local del suelo ----------

def test_cultivo_poco_tolerante_en_suelo_salino_resta(umbrales):
    _, d = puntaje_suelo([ARROZ, FRIJOL], umbrales, salinidad="alta")      # arroz y frijol: tolerancia baja
    assert reglas(d)["tolerancia_salinidad"] == -20
    _, d = puntaje_suelo([ALGODON, MAIZ], umbrales, salinidad="alta")      # algodón alta, maíz media → peor: maíz
    assert reglas(d)["tolerancia_salinidad"] == -10 and "Maíz" in next(x for x in d if x["regla"] == "tolerancia_salinidad")["explicacion"]
    _, d = puntaje_suelo([ALGODON, ALGODON], umbrales, salinidad="leve")
    assert "tolerancia_salinidad" not in reglas(d)


def test_sin_dato_de_tolerancia_no_resta(umbrales):
    a = Cultivo(id="a", nombre="A", tipo="temporal", temp_min=10, temp_max=30, agua="medio")
    _, d = puntaje_suelo([a, a.model_copy(update={"id": "b"})], umbrales, salinidad="alta")
    assert "tolerancia_salinidad" not in reglas(d)


def test_suelo_arenoso_castiga_cultivo_de_mucha_agua_y_cita_la_fuente(umbrales):
    _, d = puntaje_suelo([ARROZ, FRIJOL], umbrales, tipo_suelo="arenoso", fuente_suelo="soilgrids")
    item = next(x for x in d if x["regla"] == "arenoso_agua_alta")
    assert item["puntos"] == -10 and item["fuente"] == "SoilGrids (ISRIC)"
    _, d = puntaje_suelo([ARROZ, FRIJOL], umbrales, tipo_suelo="arenoso", fuente_suelo="agricultor")
    assert next(x for x in d if x["regla"] == "arenoso_agua_alta")["fuente"] == "dato del agricultor"
    _, d = puntaje_suelo([ARROZ, FRIJOL], umbrales, tipo_suelo="franco")
    assert "arenoso_agua_alta" not in reglas(d)


# ---------- Punto 3: prioridad del agricultor ----------

def test_cuidar_el_suelo_cambia_la_recomendada(umbrales):
    def mejor(prioridad):
        return generar_rotaciones(CAT, "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales, prioridad=prioridad)[0]
    agua, suelo = mejor("ahorrar_agua"), mejor("cuidar_suelo")
    assert suelo["saludSuelo"] >= agua["saludSuelo"]
    assert "cuidar el suelo" in suelo["motivoRecomendada"] and "ahorrar agua" in agua["motivoRecomendada"]


def test_prioridad_cambia_el_orden_con_un_caso_claro(umbrales):
    """Arroz-Frijol (suelo 100, agua alta) vs Maíz-Algodón (suelo 70, agua media): ahorrar agua y cuidar suelo eligen distinto."""
    def final(cultivos, prioridad):
        return evaluar_rotacion(cultivos, "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales, prioridad=prioridad)["puntaje"]
    af, ma = [ARROZ, FRIJOL], [MAIZ, ALGODON]
    assert final(af, "cuidar_suelo") > final(ma, "cuidar_suelo")
    assert final(ma, "ahorrar_agua") > final(af, "ahorrar_agua")


def test_prioridad_desconocida_usa_la_por_defecto(umbrales):
    r1 = evaluar_rotacion([ARROZ, FRIJOL], "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales, prioridad="otra")
    r2 = evaluar_rotacion([ARROZ, FRIJOL], "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales)
    assert r1["puntaje"] == r2["puntaje"]


def test_la_tradicional_nunca_lleva_motivo_de_recomendada(umbrales):
    for p in ("ahorrar_agua", "arriesgar_menos", "cuidar_suelo"):
        rots = generar_rotaciones(CAT, "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales, prioridad=p)
        assert all("motivoRecomendada" not in r for r in rots[1:])


def test_api_calcular_recibe_prioridad_y_suelo(cliente_api):  # noqa: F811
    api, _ = cliente_api
    base = {"lat": -1.29, "lon": 36.82, "lang": "es", "tipoCultivo": "temporal", "mesSiembra": "2027-01"}
    r = api.post("/calcular", json={**base, "prioridad": "cuidar_suelo", "tipoSuelo": "arenoso", "salinidad": "alta",
                                    "fuenteSuelo": "agricultor"}).json()
    assert r["perfil"]["prioridad"] == "cuidar_suelo" and r["perfil"]["pesos"]["suelo"] == 0.5
    assert r["perfil"]["tipoSuelo"] == "arenoso" and r["perfil"]["salinidad"] == "alta"
    assert "cuidar el suelo" in r["rotaciones"][0]["motivoRecomendada"]
    sin = api.post("/calcular", json=base).json()                       # sin datos nuevos: sigue funcionando
    assert sin["perfil"]["prioridad"] == "arriesgar_menos" and sin["perfil"]["tipoSuelo"] is None
    assert api.post("/calcular", json={**base, "prioridad": "ganar_mas"}).status_code == 422


# ---------------------------------------------------------------- reto: suelo desnudo, agua disponible, heladas, ET0
def test_suelo_desnudo_resta_y_se_informa(umbrales):
    from app.calculos.salud_suelo import meses_suelo_desnudo
    n = meses_suelo_desnudo([ARROZ, FRIJOL])
    _, desc = puntaje_suelo([ARROZ, FRIJOL], umbrales)
    if n >= umbrales["salud_suelo"]["suelo_desnudo_desde_meses"]:
        item = next(d for d in desc if d["regla"] == "suelo_desnudo")
        assert item["puntos"] == umbrales["salud_suelo"]["suelo_desnudo"] and str(n) in item["explicacion"]
    else:
        assert "suelo_desnudo" not in reglas(desc)


def test_poca_agua_baja_el_puntaje_de_agua(umbrales):
    normal = evaluar_rotacion([ARROZ, FRIJOL], "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales)
    poca = evaluar_rotacion([ARROZ, FRIJOL], "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales, agua_disponible="poca")
    assert normal["puntajeAgua"] == 20 and poca["puntajeAgua"] == 0 and poca["puntaje"] < normal["puntaje"]


def test_et0_hargreaves_valores_razonables():
    from app.calculos.campana import et0_hargreaves
    assert 4.5 <= et0_hargreaves(-5.19, 1, 34, 22) <= 7.0      # costa de Piura en verano
    assert et0_hargreaves(-5.19, 1, 20, 25) is None             # máxima menor que mínima: sin dato


def test_helada_es_riesgo_alto(umbrales):
    import pandas as pd
    from app.calculos.campana import riesgo_mes
    c = clima().copy()
    c["tmin"] = 1.0
    m = riesgo_mes(FRIJOL, pd.Period("2027-07", freq="M"), c, None, False, "es", umbrales, -5.24)
    assert m["componentes"]["helada"] == "alto" and m["riesgo"] == "alto" and m["et0MmDia"] is not None
