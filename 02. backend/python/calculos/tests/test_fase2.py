"""Fase 2: campaña, rotaciones, qué hacer, permanentes, /mapa y /calcular completo (datos fijos)."""
from datetime import date

import pandas as pd
import pytest

from app.calculos.campana import niveles_lluvia, nivel_temperatura, riesgo_campana, riesgo_mes
from app.calculos.permanentes import plan_permanente
from app.calculos.que_hacer import proximo_mes_siembra, que_hacer
from app.calculos.rotaciones import descuentos_rotacion, evaluar_rotacion, generar_rotaciones
from app.catalogo import buscar, cargar_catalogo
from app.routers.mapa import nivel_zona
from tests.test_api_calcular import cliente_api  # noqa: F401  (fixture)

PIURA = (-5.19, -80.63)
NAIROBI = (-1.29, 36.82)
CAT = cargar_catalogo(None)
ARROZ, MAIZ, FRIJOL, MANGO = (buscar(CAT, x) for x in ("arroz", "maiz", "frijol", "mango"))


def clima(lluvia_mm_mes=150.0, tmax=30.0, tmin=20.0) -> pd.DataFrame:
    return pd.DataFrame({"lluvia_mm_dia": lluvia_mm_mes / 30, "lluvia_mm_mes": lluvia_mm_mes, "tmax": tmax,
                         "tmin": tmin}, index=range(1, 13))


def ind(nivel=None, direccion=None, valor=1.0, anomalia=-10.0, fuente="NASA POWER", **extra):
    return {"nivel": nivel, "direccion": direccion, "valor": valor, "anomalia": anomalia, "fuente": fuente,
            "detalle": "detalle", **extra}


def indicadores(lluvia=None, humedad=None, calor=None, nino=None) -> dict:
    return {
        "lluvia": lluvia or ind("bajo", "deficit"),
        "humedadSuelo": humedad or ind("bajo", "deficit"),
        "calor": calor or ind("bajo", "exceso", valor=30, anomalia=0.5),
        "elNino": nino or {"valor": None, "nivel": None, "fuente": "sin dato"},
    }


NINO_ALTO = {"valor": 2.4, "nivel": "alto", "fuente": "MUR SST", "semana": "2026-11-02"}


# ---------- 1. Campaña ----------

def test_niveles_basicos(umbrales):
    uc = umbrales["campana"]
    assert nivel_temperatura(-1, uc["temperatura"]) == "bajo"
    assert nivel_temperatura(1, uc["temperatura"]) == "medio"
    assert nivel_temperatura(3.5, uc["temperatura"]) == "alto"
    assert niveles_lluvia(450, 200, uc) == ("alto", "bajo")     # 2.25x y > 200 mm
    assert niveles_lluvia(320, 200, uc) == ("medio", "bajo")    # 1.6x
    assert niveles_lluvia(20, 200, uc) == ("bajo", "medio")     # 0.1x → depende del riego


def test_mes_calor_alto_cita_numero(umbrales):
    m = riesgo_mes(ARROZ, pd.Period("2027-03", "M"), clima(tmax=39.0), None, False, "es", umbrales)
    assert m["riesgo"] == "alto" and "39.0 °C" in m["motivo"] and m["fuente"] == "NASA POWER"


def test_campana_recorre_hasta_la_cosecha(umbrales):
    c = riesgo_campana(ARROZ, "2026-12", clima(), None, *NAIROBI, "es", umbrales)
    assert c["siembra"] == "2026-12" and c["cosecha"] == "2027-04" and c["duracionMeses"] == 5
    assert c["metodo"] == "climatologia NASA POWER + señal El Niño"
    assert c["mesMasRiesgoso"] is None                          # todo bajo


def test_nino_sube_lluvia_solo_ene_abr_en_la_costa_y_con_dato(umbrales):
    c = riesgo_campana(ARROZ, "2026-12", clima(), NINO_ALTO, *PIURA, "es", umbrales)
    por_mes = {m["mes"]: m for m in c["meses"]}
    assert por_mes["2026-12"]["riesgo"] == "bajo"               # diciembre no se ajusta
    assert por_mes["2027-01"]["riesgo"] == "medio" and por_mes["2027-01"]["fuente"] == "NASA POWER + MUR SST"
    assert "El Niño" in por_mes["2027-01"]["motivo"]
    # Fuera de la costa: solo se informa, no se ajusta
    lejos = riesgo_campana(ARROZ, "2026-12", clima(), NINO_ALTO, *NAIROBI, "es", umbrales)
    assert all(m["fuente"] == "NASA POWER" and m["riesgo"] == "bajo" for m in lejos["meses"])


def test_nino_sin_dato_no_ajusta_y_lo_dice(umbrales):
    sin = {"valor": None, "nivel": None, "fuente": "sin dato"}
    c = riesgo_campana(ARROZ, "2026-12", clima(), sin, *PIURA, "es", umbrales)
    enero = c["meses"][1]
    assert enero["riesgo"] == "bajo" and "Sin señal de El Niño disponible" in enero["motivo"]


# ---------- 2. Rotaciones ----------

def _meses(n, riesgo="bajo", calor="bajo"):
    return [{"mes": f"2027-{i + 1:02d}", "riesgo": riesgo, "fuente": "NASA POWER", "cultivo": "arroz",
             "componentes": {"calor": calor, "frio": "bajo", "lluvia_exceso": "bajo", "deficit": "bajo"}}
            for i in range(n)]


def _siembras(*meses):
    return [pd.Period(m, "M") for m in meses]


def test_arroz_en_deficit_alto_resta_40(umbrales):
    ii = indicadores(humedad=ind("alto", "deficit", anomalia=-45.0, fuente="NASA POWER"))
    d = descuentos_rotacion([ARROZ], _siembras("2027-01"), _meses(5), ii, umbrales)
    assert [(x["indicador"], x["puntos"], x["fuente"]) for x in d] == [("humedadSuelo", -40, "NASA POWER")]


def test_arroz_en_deficit_medio_resta_20_y_frijol_no(umbrales):
    ii = indicadores(lluvia=ind("medio", "deficit", fuente="GPM IMERG"))
    d = descuentos_rotacion([ARROZ], _siembras("2027-01"), _meses(5), ii, umbrales)
    assert d[0]["puntos"] == -20 and d[0]["fuente"] == "GPM IMERG"
    assert descuentos_rotacion([FRIJOL], _siembras("2027-05"), _meses(3), ii, umbrales) == []


def test_mes_riesgo_alto_resta_10_por_mes(umbrales):
    d = descuentos_rotacion([FRIJOL], _siembras("2027-05"), _meses(3, riesgo="alto"), indicadores(), umbrales)
    assert {x["regla"]: x["puntos"] for x in d} == {"riesgo_alto": -30}


def test_temperatura_maximo_30(umbrales):
    d = descuentos_rotacion([ARROZ], _siembras("2027-01"), _meses(5, calor="medio"), indicadores(), umbrales)
    assert {x["regla"]: x["puntos"] for x in d} == {"temperatura": -30}


def test_siembra_fuera_de_meses_resta_15(umbrales):
    d = descuentos_rotacion([ARROZ], _siembras("2027-06"), _meses(5), indicadores(), umbrales)
    assert [(x["regla"], x["puntos"], x["fuente"]) for x in d] == [("siembra", -15, "catálogo de cultivos")]


def test_puntaje_minimo_0_y_niveles(umbrales):
    r = evaluar_rotacion([ARROZ, ARROZ], "2026-06", clima(lluvia_mm_mes=900, tmax=40), indicadores(
        humedad=ind("alto", "deficit")), *PIURA, "es", umbrales)
    assert r["riesgoClimatico"] == 0 and r["riesgo"] == "alto"
    assert sum(d["puntos"] for d in r["descuentos"]) < -100


def test_generar_incluye_tradicional_y_ordena(umbrales):
    rots = generar_rotaciones(CAT, "2027-01", clima(), indicadores(), *NAIROBI, "es", umbrales)
    assert len(rots) == 3 and any(r["nombre"] == "Arroz - Arroz" and r["tradicional"] for r in rots)
    assert [r["puntaje"] for r in rots] == sorted((r["puntaje"] for r in rots), reverse=True)
    assert [r["id"] for r in rots] == [1, 2, 3]
    for r in rots:
        assert r["ciclo"]["meses"] and r["explicacion"] and r["usoAgua"] in ("bajo", "medio", "alto")
        assert 100 + sum(d["puntos"] for d in r["descuentos"]) == r["riesgoClimatico"] or r["riesgoClimatico"] == 0


def test_explicacion_en_ingles(umbrales):
    r = evaluar_rotacion([ARROZ, ARROZ], "2027-01", clima(), indicadores(), *NAIROBI, "en", umbrales, tradicional=True)
    assert r["nombre"] == "Rice - Rice" and "always planted" in r["explicacion"]


# ---------- 3. Qué hacer ----------

HOY_SIEMBRA = date(2027, 1, 10)    # enero: mes de siembra del arroz
HOY_NO_SIEMBRA = date(2026, 11, 14)
MEJOR = {"nombre": "Arroz - Frijol", "puntaje": 85, "cultivos": ["arroz", "frijol"]}


def test_prioridad_1_drenaje_gana_a_todo():
    ii = indicadores(humedad=ind("alto", "deficit", anomalia=-50), calor=ind("alto", "exceso", 36, 3.5), nino=NINO_ALTO)
    q = que_hacer(ii, *PIURA, "es", HOY_SIEMBRA, "temporal", MEJOR, ARROZ)
    assert q["tipo"] == "preparar drenaje" and q["fuente"] == "MUR SST" and "2.4 °C más caliente" in q["motivo"]


def test_drenaje_solo_en_la_costa_y_con_dato():
    ii = indicadores(nino=NINO_ALTO)
    assert que_hacer(ii, *NAIROBI, "es", HOY_SIEMBRA, "temporal", MEJOR, ARROZ)["tipo"] == "sembrar"
    sin = indicadores(nino={"valor": None, "nivel": None, "fuente": "sin dato"})
    assert que_hacer(sin, *PIURA, "es", HOY_SIEMBRA, "temporal", MEJOR, ARROZ)["tipo"] == "sembrar"


def test_prioridad_2_deficit_alto_en_mes_de_siembra():
    ii = indicadores(humedad=ind("alto", "deficit", anomalia=-45.0), calor=ind("alto", "exceso", 36, 3.5))
    q = que_hacer(ii, *NAIROBI, "es", HOY_SIEMBRA, "temporal", MEJOR, ARROZ)
    assert q["tipo"] == "esperar" and "45 %" in q["motivo"]
    # Fuera del mes de siembra la regla 2 no aplica → gana el calor
    assert que_hacer(ii, *NAIROBI, "es", HOY_NO_SIEMBRA, "temporal", MEJOR, ARROZ)["tipo"] == "proteger"


def test_prioridad_3_calor():
    q = que_hacer(indicadores(calor=ind("alto", "exceso", 36.2, 3.4)), *NAIROBI, "es", HOY_SIEMBRA, "temporal", MEJOR, ARROZ)
    assert q["tipo"] == "proteger" and "+3.4 °C" in q["motivo"]


def test_prioridad_4_sembrar_o_esperar_al_proximo_mes():
    q = que_hacer(indicadores(), *NAIROBI, "es", HOY_SIEMBRA, "temporal", MEJOR, ARROZ)
    assert q["tipo"] == "sembrar" and "mejor opción" in q["accion"]
    q = que_hacer(indicadores(), *NAIROBI, "es", HOY_NO_SIEMBRA, "temporal", MEJOR, ARROZ)
    assert q["tipo"] == "esperar" and "diciembre" in q["accion"]
    assert proximo_mes_siembra(ARROZ, HOY_NO_SIEMBRA) == 12


def test_permanente_regar_con_deficit_alto():
    ii = indicadores(humedad=ind("alto", "deficit", anomalia=-60.0))
    q = que_hacer(ii, *NAIROBI, "es", HOY_NO_SIEMBRA, "permanente", permanente=MANGO, etapa_actual="fructificación")
    assert q["tipo"] == "regar" and "mango" in q["accion"]


# ---------- 4. Permanentes ----------

def test_plan_mango_etapa_y_acciones(umbrales):
    # Calor alto HOY durante la floración (septiembre) → "Riega temprano y evita el estrés por calor"
    ii = indicadores(calor=ind("alto", "exceso", 37.0, 3.5))
    plan = plan_permanente(MANGO, date(2026, 9, 10), clima(), ii, *NAIROBI, "es", umbrales)
    assert plan["etapaActual"] == "floración" and len(plan["meses"]) == 12
    assert plan["meses"][0]["etapa"] == "floración" and plan["meses"][0]["riesgo"] == "alto"
    accion = next(a for a in plan["acciones"] if "estrés por calor" in a["accion"])
    assert accion["etapa"] == "floración" and accion["fuente"] == "NASA POWER"


def test_plan_mango_con_nino_activa_drenaje_en_cosecha(umbrales):
    plan = plan_permanente(MANGO, date(2026, 11, 14), clima(lluvia_mm_mes=20), indicadores(nino=NINO_ALTO),
                           *PIURA, "es", umbrales)
    cosecha = [a for a in plan["acciones"] if a["etapa"] == "cosecha"]
    assert cosecha and cosecha[0]["fuente"] == "NASA POWER + MUR SST"


# ---------- 5. /calcular completo ----------

def test_calcular_temporal_formato_frontend(cliente_api):  # noqa: F811
    api, _ = cliente_api
    r = api.post("/calcular", json={"lat": -1.29, "lon": 36.82, "lang": "es", "tipoCultivo": "temporal",
                                    "mesSiembra": "2027-01"}).json()
    assert set(r) >= {"indicadores", "rotaciones", "queHacer", "lat", "lon", "fecha"}
    assert len(r["rotaciones"]) == 3 and r["catalogo"] == "ejemplo"
    rot = r["rotaciones"][0]
    assert set(rot) >= {"id", "nombre", "puntaje", "riesgo", "explicacion", "usoAgua", "descuentos", "ciclo"}
    assert set(rot["ciclo"]) >= {"siembra", "cosecha", "duracionMeses", "meses", "mesMasRiesgoso"}
    assert set(r["queHacer"]) >= {"tipo", "accion", "motivo", "fuente"}


def test_calcular_permanente(cliente_api):  # noqa: F811
    api, _ = cliente_api
    r = api.post("/calcular", json={"lat": -1.29, "lon": 36.82, "lang": "en", "tipoCultivo": "permanente",
                                    "cultivo": "mango"}).json()
    assert r["rotaciones"] == [] and r["plan"]["cultivo"] == "Mango" and len(r["plan"]["meses"]) == 12
    assert set(r["plan"]) >= {"cultivo", "etapaActual", "meses", "acciones"}


def test_calcular_con_catalogo_de_java(cliente_api):  # noqa: F811
    api, _ = cliente_api
    cat = [{"id": "sorgo", "nombre": "Sorgo", "tipo": "temporal", "temp_min": 15, "temp_max": 40, "agua": "bajo",
            "duracion_meses": 4, "meses_siembra": [1]},
           {"id": "camote", "nombre": "Camote", "tipo": "temporal", "temp_min": 15, "temp_max": 35, "agua": "bajo",
            "duracion_meses": 4, "meses_siembra": [1], "tradicional": True}]
    r = api.post("/calcular", json={"lat": -1.29, "lon": 36.82, "mesSiembra": "2027-01", "catalogo": cat}).json()
    assert r["catalogo"] == "java" and {x["nombre"] for x in r["rotaciones"]} >= {"Camote - Camote"}


def test_permanente_desconocido_422(cliente_api):  # noqa: F811
    api, _ = cliente_api
    assert api.post("/calcular", json={"lat": 0, "lon": 0, "tipoCultivo": "permanente", "cultivo": "cacao"}).status_code == 422


# ---------- 6. /mapa ----------

def test_el_nino_y_la_vegetacion_no_pintan_el_mapa():
    ind = {"lluvia": {"nivel": "bajo"}, "calor": {"nivel": "medio"}, "elNino": {"nivel": "alto", "valor": 6.0},
           "vegetacion": {"nivel": "alto"}}
    assert nivel_zona(ind) == ("medio", "calor")
    assert nivel_zona(ind, excluir=()) == ("alto", "elNino")


def test_nivel_zona_es_el_peor_indicador():
    assert nivel_zona({"lluvia": {"nivel": "bajo"}, "calor": {"nivel": "medio"}, "elNino": {"nivel": None}}) == ("medio", "calor")
    assert nivel_zona({"a": {"nivel": None}}) == (None, None)


def test_mapa_piura_7_zonas_y_usa_cache(cliente_api):  # noqa: F811
    api, llamadas = cliente_api
    r = api.post("/mapa", json={"region": "piura"}).json()
    assert r["region"] == "piura" and len(r["zonas"]) == 7
    assert {z["nombre"] for z in r["zonas"]} == {"Bajo Piura", "Alto Piura", "Valle del Chira", "Sullana",
                                                 "Chulucanas", "Tambogrande", "Sechura"}
    assert all(z["nivel"] in ("bajo", "medio", "alto") for z in r["zonas"])
    n = len(llamadas)
    api.post("/mapa", json={"region": "piura"})
    assert len(llamadas) == n                                    # segunda vez: todo desde la caché
    assert api.post("/mapa", json={"region": "lima"}).json() == {"region": "lima", "zonas": []}
