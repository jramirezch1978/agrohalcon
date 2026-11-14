"""Los 3 endpoints que usa la API Java (app/allpashift_api.py) frente al contrato del frontend (03. frontend/src/types/api.ts).

Sin internet: se reemplazan las descargas de app/nasa_cliente.py por datos sintéticos con la forma real de NASA POWER.
El cuerpo del pedido es el que arma Java en RecomendacionService.recomendacion().
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import allpashift_api, nasa_cliente
from app.main import app

NIVELES = {"bajo", "medio", "alto"}
AGUA_NIVEL = {"bajo", "medio", "alto"}
MUESTRA = Path(__file__).resolve().parents[1] / "samples" / "catalogo_cultivos_ejemplo.json"

# Piura: seca casi todo el año, lluvias en feb-abr (mm/día)
LLUVIA = [1.6, 3.2, 3.9, 1.2, 0.3, 0.1, 0.05, 0.05, 0.1, 0.2, 0.2, 0.6]


def clima_normal() -> dict[str, list[float]]:
    return {
        "PRECTOTCORR": LLUVIA,
        "GWETTOP": [0.55] * 12,
        "GWETROOT": [0.60] * 12,
        "T2M_MAX": [31.0, 32.0, 32.5, 31.5, 29.0, 27.0, 26.0, 26.0, 27.0, 28.0, 29.0, 30.0],
        "T2M_MIN": [21.0, 22.0, 22.0, 21.0, 19.0, 17.5, 16.5, 16.5, 17.0, 18.0, 19.0, 20.0],
        "T2M": [26.0] * 12,
    }


@pytest.fixture
def nasa_falsa(monkeypatch):
    estado = {"reciente": {"lluviaMmDia": 0.5, "humedadSup": 0.55, "tMax": 31.0, "tMin": 21.0, "ultimoDia": "20261110", "dias": 30},
              "sst": 0.2}
    monkeypatch.setattr(nasa_cliente, "climatologia", lambda lat, lon: clima_normal())
    monkeypatch.setattr(nasa_cliente, "reciente", lambda lat, lon: estado["reciente"])
    monkeypatch.setattr(nasa_cliente, "sst_anomalia", lambda lat, lon: estado["sst"])
    monkeypatch.setattr(nasa_cliente, "sst_respaldo", lambda lat, lon, hoy=None: estado.get("respaldo"))  # por defecto sin Plan B

    def mensual(lat, lon, anio):
        # 2017: marzo con 14.2 mm/día (valor real de POWER en el Bajo Piura); el resto normal
        lluvia = [v if m != 2 else 14.2 for m, v in enumerate(LLUVIA)] if anio == 2017 else list(LLUVIA)
        return {"PRECTOTCORR": lluvia, "GWETROOT": [0.6] * 12}

    monkeypatch.setattr(nasa_cliente, "mensual", mensual)
    return estado


@pytest.fixture
def cliente():
    return TestClient(app)


def pedido_java(mes: str = "2026-12") -> dict:
    """Mismo formato que RecomendacionService.java para cultivos temporales."""
    crudo = json.loads(MUESTRA.read_text(encoding="utf-8"))
    cultivos = crudo["cultivos"] if isinstance(crudo, dict) else crudo
    cultivos = [{**c, "cicloDias": 120, "toleraSequia": c["nombre"] in ("Algodón", "Maíz"), "toleraInundacion": c["nombre"] == "Arroz"}
                for c in cultivos]
    ids = [c["id"] for c in cultivos]
    return {"lat": -5.19, "lon": -80.63, "tipoCultivo": "temporal", "mesSiembra": mes, "cultivos": cultivos,
            "rotaciones": [{"id": i + 1, "nombre": f"{a} -> {b}", "cultivo1Id": a, "cultivo2Id": b}
                           for i, (a, b) in enumerate(zip(ids, ids[1:] + ids[:1], strict=True))],
            "rotacionActualId": 1}


def verificar_indicadores(ind: dict, con_nino: bool = True) -> None:
    claves = {"lluvia", "humedadSuelo", "calor"} | ({"elNino"} if con_nino else set())
    assert set(ind) == claves
    for k, v in ind.items():
        assert isinstance(v["valor"], (int, float)) and isinstance(v["normal"], (int, float)), k
        assert v["nivel"] in NIVELES and v["unidad"] and v["fuente"], k
        assert v.get("detalle"), f"{k}: el frontend muestra 'detalle'"


# ------------------------------------------------------------------ POST /calcular (temporal)
def test_calcular_temporal_cumple_el_contrato_del_frontend(cliente, nasa_falsa):
    r = cliente.post("/calcular", json=pedido_java())
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert set(cuerpo) >= {"datosNasa", "recomendacion", "contrato"}  # lo que lee RecomendacionService.guardar()

    reco = cuerpo["recomendacion"]
    assert reco["lat"] == -5.19 and len(reco["fecha"]) == 10
    verificar_indicadores(reco["indicadores"])
    assert reco["rotaciones"], "debe haber rotaciones"
    for rot in reco["rotaciones"]:
        assert {"id", "nombre", "puntaje", "riesgo", "explicacion"} <= set(rot)
        assert 0 <= rot["puntaje"] <= 100 and rot["riesgo"] in NIVELES
        assert rot["usoAgua"] in AGUA_NIVEL
        for d in rot.get("descuentos", []):
            assert d["puntos"] < 0 and d["fuente"] and d["indicador"] in {"lluvia", "humedadSuelo", "calor", "elNino", "campana"}
        ciclo = rot["ciclo"]
        assert ciclo["duracionMeses"] == len(ciclo["meses"]) >= 2
        assert ciclo["siembra"] == ciclo["meses"][0]["mes"] == "2026-12"
        for m in ciclo["meses"]:
            assert m["riesgo"] in NIVELES and m["motivo"] and m["fuente"]
    qh = reco["queHacer"]
    assert qh["tipo"] in {"sembrar", "esperar", "regar", "proteger", "preparar drenaje"}
    assert qh["accion"] and qh["motivo"] and qh["fuente"]

    # la forma del contrato (la usa el asistente) y las filas que Java graba en nasa.datos_nasa
    assert cuerpo["contrato"]["queHacer"]["accion"] == qh["accion"]
    filas = cuerpo["datosNasa"]
    assert {f["fuente"] for f in filas} == {"NASA POWER", "MUR SST"}
    assert all({"lat", "lon", "fecha", "fuente", "variable", "valor"} <= set(f) for f in filas)
    assert all(":" in f["variable"] for f in filas), "formato NOMBRE_NASA:campoContrato"


def test_la_rotacion_actual_siempre_se_incluye(cliente, nasa_falsa):
    reco = cliente.post("/calcular", json=pedido_java()).json()["recomendacion"]
    assert 1 in {r["id"] for r in reco["rotaciones"]}


def test_sin_sst_no_se_inventa_el_nino(cliente, nasa_falsa):
    nasa_falsa["sst"] = None
    cuerpo = cliente.post("/calcular", json=pedido_java()).json()
    verificar_indicadores(cuerpo["recomendacion"]["indicadores"], con_nino=False)
    assert {f["fuente"] for f in cuerpo["datosNasa"]} == {"NASA POWER"}


def test_si_noaa_no_responde_el_nino_sale_del_respaldo_y_lo_avisa(cliente, nasa_falsa):
    nasa_falsa["sst"] = None
    nasa_falsa["respaldo"] = {"anomalia": 6.0, "sst": 27.3, "semana": "2026-11-09", "dias": 4}
    cuerpo = cliente.post("/calcular", json=pedido_java()).json()
    nino = cuerpo["recomendacion"]["indicadores"]["elNino"]
    assert nino["nivel"] == "alto" and nino["fuente"] == "MUR SST", "la fuente sigue siendo MUR SST: el frontend busca esa etiqueta"
    assert "respaldo" in nino["aviso"] and "2026-11-09" in nino["aviso"]
    fila = next(f for f in cuerpo["datosNasa"] if f["fuente"] == "MUR SST")
    assert fila["variable"].endswith(":nino12semanal") and fila["fecha"] == "2026-11-09", "no se graba como 'hoy en este punto'"


def test_con_noaa_en_vivo_no_hay_aviso_de_respaldo(cliente, nasa_falsa):
    nino = cliente.post("/calcular", json=pedido_java()).json()["recomendacion"]["indicadores"]["elNino"]
    assert "aviso" not in nino or not nino["aviso"]


def test_respaldo_real_solo_vale_en_la_costa_y_si_no_esta_vencido():
    archivo = json.loads(nasa_cliente.RESPALDO_NINO12.read_text(encoding="utf-8"))
    ultima = max(archivo["semanas"], key=lambda s: s["semana"])
    dia = date.fromisoformat(ultima["semana"])
    r = nasa_cliente.sst_respaldo(-5.19, -80.63, hoy=dia + timedelta(days=10))
    assert r and r["semana"] == ultima["semana"] and r["anomalia"] == ultima["anomalia"]
    assert nasa_cliente.sst_respaldo(-5.19, -80.63, hoy=dia + timedelta(days=6 + nasa_cliente.MAX_DIAS_RESPALDO + 1)) is None  # vencido
    assert nasa_cliente.sst_respaldo(-5.19, -80.63, hoy=dia + timedelta(days=6 + nasa_cliente.MAX_DIAS_RESPALDO)) is not None  # justo en el límite
    assert nasa_cliente.sst_respaldo(-7.0, -70.0, hoy=dia) is None  # selva: El Niño costero no aplica


def test_respaldo_sin_archivo_no_rompe(monkeypatch, tmp_path):
    monkeypatch.setattr(nasa_cliente, "RESPALDO_NINO12", tmp_path / "no_existe.json")
    assert nasa_cliente.sst_respaldo(-5.19, -80.63) is None


def test_sin_dato_reciente_se_usa_la_normal_y_el_pedido_no_falla(cliente, nasa_falsa):
    nasa_falsa["reciente"] = None
    r = cliente.post("/calcular", json=pedido_java())
    assert r.status_code == 200
    filas = r.json()["datosNasa"]
    assert not any(f["variable"].endswith(":prom30d") and f["fuente"] == "NASA POWER" for f in filas), \
        "sin dato reciente no se graba como si fuera medido"


def test_sin_catalogo_responde_422(cliente, nasa_falsa):
    assert cliente.post("/calcular", json={"lat": -5.19, "lon": -80.63, "tipoCultivo": "temporal"}).status_code == 422


def test_nasa_caida_responde_503(cliente, monkeypatch):
    def falla(lat, lon):
        raise RuntimeError("sin red")

    monkeypatch.setattr(nasa_cliente, "climatologia", falla)
    assert cliente.post("/calcular", json=pedido_java()).status_code == 503


# ------------------------------------------------------------------ POST /calcular (permanente)
def test_calcular_permanente(cliente, nasa_falsa):
    cuerpo = {"lat": -5.19, "lon": -80.63, "tipoCultivo": "permanente",
              "permanente": {"nombre": "Mango", "calendario": "CCCCFFFKKDDS",
                             "fases": {"S": "Siembra", "C": "Crecimiento", "F": "Floración", "K": "Cosecha", "D": "Descanso"},
                             "acciones": [{"fase": "F", "descripcion": "Evita el estrés hídrico", "alerta": "Lluvia en floración"}]}}
    r = cliente.post("/calcular", json=cuerpo)
    assert r.status_code == 200, r.text
    reco = r.json()["recomendacion"]
    plan = reco["plan"]
    assert plan["cultivo"] == "Mango" and len(plan["meses"]) == 12 and plan["etapaActual"]
    assert all(m["riesgo"] in NIVELES and m["etapa"] for m in plan["meses"])
    assert reco["rotaciones"] == [] and reco["queHacer"]["tipo"] in {"regar", "preparar drenaje"}


def test_permanente_sin_datos_del_cultivo_responde_422(cliente, nasa_falsa):
    assert cliente.post("/calcular", json={"lat": -5.19, "lon": -80.63, "tipoCultivo": "permanente"}).status_code == 422


# ------------------------------------------------------------------ POST /indicadores-punto (mapa)
def test_indicadores_punto_da_el_nivel_del_peor_indicador(cliente, nasa_falsa):
    nasa_falsa["sst"] = 2.0  # mar +2 °C → El Niño alto
    r = cliente.post("/indicadores-punto", json={"lat": -5.35, "lon": -80.7})
    assert r.status_code == 200
    cuerpo = r.json()
    verificar_indicadores(cuerpo["indicadores"])
    assert cuerpo["nivel"] == "alto" and cuerpo["datosNasa"]


# ------------------------------------------------------------------ POST /validacion (máquina del tiempo)
def test_validacion_2017_da_alerta_y_semanas_de_anticipacion(cliente, nasa_falsa):
    r = cliente.post("/validacion", json={"anio": 2017, "lat": -5.19, "lon": -80.63,
                                           "eventos": [{"nombre": "El Niño costero 2017", "inicio": "2017-01-01", "fin": "2017-04-30"}]})
    assert r.status_code == 200, r.text
    v = r.json()
    assert v["anio"] == 2017 and v["evento"]["nombre"].startswith("El Niño")
    assert len(v["series"]["lluvia"]["valores"]) == len(v["series"]["lluvia"]["normal"]) == 12
    assert v["series"]["lluvia"]["fuente"] == "NASA POWER"
    assert v["alerta"]["indicador"] == "lluvia" and v["alerta"]["fecha"] == "2017-03-15" and v["alerta"]["nivel"] == "alto"
    assert v["mesLluviaMaxima"] == "2017-03"
    assert v["realidad"]["fuente"] == "INDECI / SENASA"
    assert v["recomendacionPrevia"]["tipo"] == "preparar drenaje" and v["resumen"]


def test_validacion_de_un_anio_normal_no_inventa_alerta(cliente, nasa_falsa):
    v = cliente.post("/validacion", json={"anio": 2019, "lat": -5.19, "lon": -80.63}).json()
    assert v["alerta"] is None and v["semanasAnticipacion"] is None and v["evento"] is None
    assert v["recomendacionPrevia"]["tipo"] == "sembrar"


# ------------------------------------------------------------------ funciones puras
def test_tipo_accion_reconoce_las_cinco_acciones():
    t = allpashift_api.tipo_accion
    assert t("Prepara drenajes en tus parcelas") == "preparar drenaje"
    assert t("Espera, todavía no siembres") == "esperar"
    assert t("Protege el cultivo del calor") == "proteger"
    assert t("Riega temprano") == "regar"
    assert t("Siembra arroz") == "sembrar"


def test_el_nino_extraordinario_no_muestra_el_icono_de_sembrar(cliente, nasa_falsa):
    """Antes el texto 'consulta a un técnico agrario antes de sembrar' caía en 'sembrar'."""
    nasa_falsa["sst"] = 3.5
    qh = cliente.post("/calcular", json=pedido_java()).json()["recomendacion"]["queHacer"]
    assert "ENFEN" in qh["accion"] and qh["tipo"] == "esperar"


def test_inundacion_pide_esperar(cliente, nasa_falsa):
    nasa_falsa["reciente"] = {"lluviaMmDia": 14.0, "humedadSup": 0.9, "tMax": 31.0, "tMin": 21.0, "ultimoDia": "20260310", "dias": 30}
    qh = cliente.post("/calcular", json=pedido_java()).json()["recomendacion"]["queHacer"]
    assert "inundación" in qh["accion"] and qh["tipo"] == "esperar"
