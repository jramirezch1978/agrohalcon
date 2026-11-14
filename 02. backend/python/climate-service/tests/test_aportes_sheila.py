"""Aportes de Sheila a la base de datos (db/aportes.py): IMERG de 12 puntos de Piura y MUR SST de la caja Niño 1+2.

Con archivos de juguete (misma estructura que calculos/data/precalculado/) y con la copia real de data/backup/sheila/.
"""

import json
from datetime import date

import pytest
from sqlalchemy import create_engine, insert, text

from db import aportes, catalogos, schema
from db.export_allpashift import VARIABLES, normales


def punto(pid, lat, lon):
    return {"id": pid, "nombre": pid.capitalize(), "lat": lat, "lon": lon}


@pytest.fixture
def carpeta(tmp_path):
    """3 puntos: uno sobre el valle 1, uno a ~1 km del valle 2 y uno lejos de todo (zona de referencia)."""
    puntos = [punto("bajo", -5.35, -80.70), punto("chira", -4.905, -80.85), punto("lejos", -4.64, -79.71)]
    meses = [f"2017-{m:02d}" for m in range(1, 13)] + [f"2018-{m:02d}" for m in range(1, 13)]
    mm_mes = {p["id"]: [310.0 if m == "2017-01" else 31.0 for m in meses] for p in puntos}  # enero 2017: 310 mm = 10 mm/día
    im = {
        "metadatos": {}, "puntos": puntos,
        "mensual": {"meses": meses, "mm_mes": mm_mes},
        "climatologia": {"periodo": "2017-2018", "mm_mes": {}, "mm_dia": {p["id"]: [1.0] * 12 for p in puntos},
                         "anios_con_dato": {p["id"]: [2] * 12 for p in puntos}},
        "diario": {"fechas": ["2026-11-01", "2026-11-02"], "mm_dia": {p["id"]: [0.0, 1.5] for p in puntos}},
    }  # fmt: skip
    mur = {"metadatos": {}, "semanas": [{"semana": f"2017-01-{d:02d}", "sst": 24.0 + i, "anomalia": 1.0 + i / 10, "dias": 7} for i, d in enumerate((2, 9, 16, 23, 30))]}
    (tmp_path / aportes.ARCHIVO_IMERG).write_text(json.dumps(im), encoding="utf-8")
    (tmp_path / aportes.ARCHIVO_MUR).write_text(json.dumps(mur), encoding="utf-8")
    return tmp_path


@pytest.fixture
def con(carpeta, monkeypatch):
    monkeypatch.setenv("CALCULOS_PRECALCULADO", str(carpeta))
    eng = create_engine("sqlite://")
    schema.metadata.create_all(eng)
    with eng.begin() as c:
        c.execute(insert(schema.region), [{"id": i, "codigo": k, "nombre": n} for i, k, n in catalogos.REGIONES])
        c.execute(insert(schema.fuente_dato), [dict(zip(("id", "codigo", "nombre", "institucion", "producto", "version", "doi", "resolucion", "cobertura", "url", "acceso", "estado", "nota"), f, strict=True)) for f in catalogos.FUENTES])
        c.execute(insert(schema.variable), [dict(zip(("id", "codigo", "nombre", "unidad", "fuente_id", "descripcion"), v, strict=True)) for v in catalogos.VARIABLES])
        c.execute(insert(schema.zona), [
            {"id": 1, "nombre": "Bajo Piura", "region_id": 1, "tipo": "agricola", "lat": -5.35, "lon": -80.70, "aproximada": True},
            {"id": 2, "nombre": "Valle del Chira", "region_id": 1, "tipo": "agricola", "lat": -4.90, "lon": -80.85, "aproximada": True},
        ])  # fmt: skip
        yield c


def test_localizar_prefiere_la_variable_de_entorno_y_devuelve_none_si_faltan_archivos(carpeta, monkeypatch, tmp_path_factory):
    monkeypatch.setenv("CALCULOS_PRECALCULADO", str(carpeta))
    assert aportes.localizar() == carpeta
    monkeypatch.setenv("CALCULOS_PRECALCULADO", str(tmp_path_factory.mktemp("vacia")))
    assert aportes.localizar() != carpeta  # cae a las rutas del repositorio (la copia de respaldo existe)


def test_un_punto_se_asigna_al_valle_si_esta_a_menos_de_5_km_y_un_valle_recibe_solo_uno():
    valles = [(1, -5.35, -80.70)]
    pts = [punto("exacto", -5.35, -80.70), punto("cerca", -5.36, -80.70), punto("lejos", -5.60, -80.70)]
    r = aportes.asignar_zonas(valles, pts)
    assert r["exacto"][0] == 1 and r["cerca"][0] is None and r["lejos"][0] is None


def test_carga_convierte_mm_mes_a_mm_dia_y_crea_zonas_de_referencia(con):
    r = aportes.cargar(con, {})
    assert r["puntos_en_valles"] == 2 and r["puntos_de_referencia"] == 1
    zona_ref = con.execute(text("SELECT id, tipo, nombre FROM zona WHERE tipo = 'referencia'")).one()
    assert zona_ref.id == aportes.ID_REFERENCIA and "punto IMERG" in zona_ref.nombre

    enero = con.execute(text("SELECT valor, calidad FROM observacion WHERE zona_id = 1 AND fecha = '2017-01-01' AND escala = 'mensual'")).one()
    assert enero.valor == pytest.approx(10.0) and enero.calidad == "final"  # 310 mm / 31 días
    febrero = con.execute(text("SELECT valor FROM observacion WHERE zona_id = 1 AND fecha = '2017-02-01' AND escala = 'mensual'")).scalar()
    assert febrero == pytest.approx(31.0 / 28, abs=1e-3)  # febrero de 2017 tiene 28 días (se guarda con 4 decimales)
    diario = con.execute(text("SELECT valor, calidad FROM observacion WHERE zona_id = 1 AND fecha = '2026-11-02' AND escala = 'diaria'")).one()
    assert diario.valor == 1.5 and diario.calidad == "late"  # la corrida rápida no es la final


def test_la_normal_de_imerg_conserva_su_periodo_2001_2020_no_1991_2020(con):
    aportes.cargar(con, {})
    n = con.execute(text("SELECT media, n_anios, anio_ini, anio_fin FROM normal_mensual WHERE zona_id = 1 AND mes = 1")).one()
    assert (n.media, n.n_anios, n.anio_ini, n.anio_fin) == (1.0, 2, 2017, 2018)  # el periodo que declaró Sheila, no el de POWER


def test_mur_nino12_semanal_entra_como_indice_con_su_fuente(con):
    aportes.cargar(con, {})
    filas = con.execute(text("SELECT codigo, COUNT(*) FROM indice_climatico GROUP BY codigo")).fetchall()
    assert dict(filas) == {"MUR_NINO12": 5, "MUR_NINO12_ANOM": 5}
    fuente = con.execute(text("SELECT f.codigo FROM indice_climatico i JOIN fuente_dato f ON f.id = i.fuente_id LIMIT 1")).scalar()
    assert fuente == "MUR_NINO12"


def test_el_contraste_necesita_al_menos_6_meses_comunes_y_no_inventa(con):
    r = aportes.cargar(con, {})
    assert r["contrastes"] == 0  # sin POWER ni NOAA CPC en esta base de juguete no hay con qué contrastar
    assert con.execute(text("SELECT COUNT(*) FROM contraste_fuentes")).scalar() == 0


def test_el_contraste_mide_correlacion_y_sesgo(con):
    aportes.cargar(con, {})
    im, po = catalogos.CODIGO_VARIABLE["IMERG_PRECIP_M"], catalogos.CODIGO_VARIABLE["PRECTOTCORR"]
    con.execute(text("DELETE FROM observacion WHERE variable_id = :v AND zona_id = 1"), {"v": im})
    filas = []
    for i in range(12):  # IMERG sube de 1 a 12 mm/día; POWER = IMERG - 0.8 con un pequeño ruido: misma forma, sesgo constante
        f = date(2018, i + 1, 1)
        filas += [{"zona_id": 1, "fecha": f, "escala": "mensual", "variable_id": im, "valor": float(i + 1)},
                  {"zona_id": 1, "fecha": f, "escala": "mensual", "variable_id": po, "valor": float(i + 1) - 0.8 + (i % 3) * 0.05}]  # fmt: skip
    con.execute(insert(schema.observacion), filas)
    e = next(f for f in aportes.contrastes(con) if f["par"] == "IMERG_vs_POWER" and f["zona_id"] == 1)
    assert e["n"] == 12 and e["correlacion"] > 0.99 and e["sesgo_medio"] == pytest.approx(0.75, abs=0.1)
    assert e["periodo_ini"] == date(2018, 1, 1) and e["periodo_fin"] == date(2018, 12, 1)


# ------------------------------------------------------------------ la copia real de data/backup/sheila
def test_la_copia_real_de_sheila_tiene_la_forma_esperada():
    carpeta = aportes.BACKUP / "sheila"
    im = json.loads((carpeta / aportes.ARCHIVO_IMERG).read_text(encoding="utf-8"))
    assert len(im["puntos"]) == 12 and im["mensual"]["meses"][0] == "2001-01" and im["mensual"]["meses"][-1] == "2025-09"
    assert all(len(v) == len(im["mensual"]["meses"]) for v in im["mensual"]["mm_mes"].values())
    marzo = im["mensual"]["meses"].index("2017-03")
    razon = {pid: serie[marzo] / im["climatologia"]["mm_mes"][pid][2] for pid, serie in im["mensual"]["mm_mes"].items()}
    sierra = {"huancabamba", "ayabaca"}
    assert all(r > 2.5 for pid, r in razon.items() if pid not in sierra), razon  # valles: 2,7 a 7,5 veces la normal en marzo de 2017
    assert all(1.5 < razon[pid] < 2.5 for pid in sierra), razon  # la sierra llovió menos veces su normal (que ya es alta)
    assert razon["bajo_piura"] > 5 and razon["sechura"] > 5, razon  # y en la costa seca, más de 5 veces
    mur = json.loads((carpeta / aportes.ARCHIVO_MUR).read_text(encoding="utf-8"))
    assert len(mur["semanas"]) > 500 and all(s["anomalia"] is not None for s in mur["semanas"])


def test_la_exportacion_al_esquema_del_equipo_no_inventa_fuentes():
    assert {f for _, f, _ in VARIABLES.values()} == {"NASA POWER", "SMAP", "VIIRS NDVI", "MUR SST", "GPM IMERG"}
    assert all(":" in v for v, _, _ in VARIABLES.values())
    assert callable(normales)
