"""Pruebas sin internet de la capa de datos: esquema, vistas, análisis y geometría de las rejillas satelitales."""

from datetime import date

import pandas as pd
import pytest
import sqlglot
from sqlalchemy import create_engine, insert, text

from db import analisis, export_postgres, schema
from etl import cpc, mur_opendap, smap, srtm, viirs_ndvi


# ------------------------------------------------------------------ esquema y vistas
@pytest.fixture
def con():
    eng = create_engine("sqlite://")
    schema.metadata.create_all(eng)
    with eng.begin() as c:
        for n, sql in schema.VISTAS.items():
            c.execute(text(f"CREATE VIEW {n} AS {sql}"))
        c.execute(text("PRAGMA foreign_keys=ON"))
        c.execute(insert(schema.region), [{"id": 1, "codigo": "piura", "nombre": "Piura"}])
        c.execute(insert(schema.fuente_dato), [{"id": 1, "codigo": "POWER", "nombre": "NASA POWER", "institucion": "NASA", "estado": "en_uso"}])
        c.execute(insert(schema.variable), [{"id": 4, "codigo": "PRECTOTCORR", "nombre": "Lluvia", "unidad": "mm/día", "fuente_id": 1}])
        c.execute(insert(schema.zona), [{"id": 1, "nombre": "Bajo Piura", "region_id": 1, "lat": -5.35, "lon": -80.7}])
        yield c


def test_vista_datos_nasa_tiene_las_columnas_del_contrato(con):
    con.execute(insert(schema.observacion), [{"zona_id": 1, "fecha": date(2017, 3, 1), "escala": "mensual", "variable_id": 4, "valor": 12.9}])
    fila = con.execute(text("SELECT * FROM v_datos_nasa")).mappings().one()
    assert {"lat", "lon", "fecha", "fuente", "variable", "valor"} <= set(fila)
    assert fila["fuente"] == "NASA POWER" and fila["variable"] == "PRECTOTCORR"


def test_vista_anomalia_mensual_calcula_z(con):
    con.execute(insert(schema.normal_mensual), [{"zona_id": 1, "variable_id": 4, "mes": 3, "media": 2.0, "desviacion": 1.0, "n_anios": 30, "anio_ini": 1991, "anio_fin": 2020}])
    con.execute(insert(schema.observacion), [{"zona_id": 1, "fecha": date(2017, 3, 1), "escala": "mensual", "variable_id": 4, "valor": 12.0}])
    fila = con.execute(text("SELECT anomalia, z FROM v_anomalia_mensual")).one()
    assert fila == (10.0, 10.0)


def test_vista_ultimo_dato(con):
    con.execute(insert(schema.observacion), [{"zona_id": 1, "fecha": date(2026, d, 1), "escala": "mensual", "variable_id": 4, "valor": float(d)} for d in (1, 5, 3)])
    assert con.execute(text("SELECT valor FROM v_ultimo_dato")).scalar() == 5.0


def test_las_claves_foraneas_se_exigen(con):
    with pytest.raises(Exception, match="FOREIGN KEY"):
        con.execute(insert(schema.observacion), [{"zona_id": 99, "fecha": date(2017, 3, 1), "escala": "mensual", "variable_id": 4, "valor": 1.0}])


def test_no_se_repite_una_observacion(con):
    fila = {"zona_id": 1, "fecha": date(2017, 3, 1), "escala": "mensual", "variable_id": 4, "valor": 1.0}
    con.execute(insert(schema.observacion), [fila])
    with pytest.raises(Exception, match="UNIQUE"):
        con.execute(insert(schema.observacion), [fila])


def test_checks_de_dominio(con):
    with pytest.raises(Exception, match="CHECK"):
        con.execute(insert(schema.observacion), [{"zona_id": 1, "fecha": date(2017, 3, 1), "escala": "semanal", "variable_id": 4, "valor": 1.0}])
    with pytest.raises(Exception, match="CHECK"):
        con.execute(insert(schema.cultivo), [{"id": 1, "nombre": "X", "temp_min_c": 30, "temp_max_c": 20, "agua_necesaria": "alta", "meses_siembra": [], "meses_cosecha": []}])


# ------------------------------------------------------------------ PostgreSQL
def test_el_sql_de_postgres_es_valido_y_completo():
    sql = export_postgres.ddl()
    assert export_postgres.validar(sql) >= len(schema.metadata.tables) + len(schema.VISTAS)
    assert "JSONB" in sql and "BIGSERIAL" in sql and sql.count("CREATE TABLE") == len(schema.metadata.tables)
    for vista in schema.VISTAS:
        assert f"CREATE OR REPLACE VIEW {vista}" in sql


def test_sqlglot_detecta_sql_roto():
    with pytest.raises(sqlglot.errors.ParseError):
        sqlglot.parse("CREATE TABLE (", read="postgres")


# ------------------------------------------------------------------ análisis
def test_tendencia_detecta_calentamiento_y_no_inventa_en_ruido():
    filas = []
    for anio in range(1981, 2026):
        for mes in range(1, 13):
            filas.append({"zona_id": 1, "variable": "T2M", "fecha": pd.Timestamp(anio, mes, 1), "valor": 25 + 0.03 * (anio - 1981)})
            filas.append({"zona_id": 1, "variable": "PRECTOTCORR", "fecha": pd.Timestamp(anio, mes, 1), "valor": 1 + 0.5 * ((anio * 7 + mes) % 5)})
    t = analisis.tendencias(pd.DataFrame(filas)).set_index("variable")
    assert t.loc["T2M", "sentido"] == "creciente" and t.loc["T2M", "pendiente_sen_por_decada"] == pytest.approx(0.3, abs=0.01)
    assert t.loc["PRECTOTCORR", "p_valor"] > 0.05 and t.loc["PRECTOTCORR", "sentido"] == "sin tendencia"


def test_anios_nino_costero_se_calculan_del_indice():
    meses = pd.date_range("1981-01-01", "2020-12-01", freq="MS")
    nino = pd.DataFrame({"fecha": meses, "nino12_anom": 0.0})
    nino.loc[(nino["fecha"] >= "1997-12-01") & (nino["fecha"] <= "1998-04-01"), "nino12_anom"] = 3.0
    nino.loc[(nino["fecha"] >= "2016-12-01") & (nino["fecha"] <= "2017-04-01"), "nino12_anom"] = 0.9  # no llega a +1,0
    assert analisis.anios_nino_costero(nino) == [1998]


def test_composite_nino_razon():
    filas = [{"zona_id": 1, "variable": "PRECTOTCORR", "fecha": pd.Timestamp(a, 3, 1), "valor": 10.0 if a in (1983, 1998) else 1.0} for a in range(1981, 2001)]
    c = analisis.composite_nino(pd.DataFrame(filas), [1983, 1998]).iloc[0]
    assert c["media_nino"] == 10.0 and c["media_normal"] == 1.0 and c["razon"] == 10.0 and (c["n_nino"], c["n_normal"]) == (2, 18)


def test_episodios_calientes_ignoran_picos_cortos():
    base = [{"fecha": f"2020-{m:02d}-01", "nino12_anom": a} for m, a in enumerate([0, 1.2, 2.0, 1.5, 0.2, 1.4, 0, 0, 0, 0, 0, 0], 1)]
    e = cpc.episodios(base)
    assert len(e) == 1 and e[0]["meses"] == 3 and e[0]["pico_anom"] == 2.0 and e[0]["pico_fecha"] == "2020-03-01"


# ------------------------------------------------------------------ geometría de las rejillas (verificada contra archivos NASA reales)
def test_smap_ease2_piura():
    assert smap.pixel(-5.19, -80.63) == (885, 1064)  # comprobado con 8/8 píxeles reales del HDF5


def test_viirs_tesela_sinusoidal_de_piura():
    h, v, fila, col = viirs_ndvi.tesela_y_pixel(-5.19, -80.63)
    assert (h, v) == (9, 9)  # el catálogo devolvió h09v09 y h10v09 para la zona
    assert 0 <= fila < 2400 and 0 <= col < 2400


@pytest.mark.parametrize("lat, lon, esperado", [(-5.19, -80.63, "S06W081"), (-5.0, -80.0, "S05W080"), (4.2, 10.7, "N04E010")])
def test_nombre_de_tesela_srtm(lat, lon, esperado):
    assert srtm.nombre_tesela(lat, lon) == esperado


def test_mur_indices_reproducen_lat_lon_reales():
    i, j = mur_opendap._indices(-5.5, -81.5)
    # el servidor devolvió lat=-5.49, lon=-81.49 para (8450, 9850) con la fórmula anterior; esta cae en la celda vecina exacta
    assert mur_opendap.LAT0 + mur_opendap.PASO * i == pytest.approx(-5.5, abs=0.005)
    assert mur_opendap.LON0 + mur_opendap.PASO * j == pytest.approx(-81.5, abs=0.005)


def test_anomalia_mur_interpola_la_climatologia_circular():
    clima = [{"doy": 1, "media_c": 20.0}, {"doy": 181, "media_c": 16.0}]
    # a mitad de camino entre ambos puntos la climatología es 18
    assert mur_opendap.anomalia(clima, date(2021, 3, 31), 21.0) == pytest.approx(3.0, abs=0.1)
    assert mur_opendap.anomalia([], date(2021, 3, 31), 21.0) is None
