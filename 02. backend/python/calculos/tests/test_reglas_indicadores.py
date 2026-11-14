import pandas as pd
import pytest

from app.calculos.indicadores import (
    anomalia_pct, nivel_calor, nivel_el_nino, nivel_humedad, nivel_lluvia, nivel_por_corte,
    normal_misma_ventana, normal_ponderada, ventana_reciente,
)


def test_anomalia_pct():
    assert anomalia_pct(5.5, 10) == pytest.approx(-45)
    assert anomalia_pct(12, 10) == pytest.approx(20)


@pytest.mark.parametrize("x,esperado", [(0, "bajo"), (19.9, "bajo"), (20, "medio"), (40, "medio"), (40.1, "alto")])
def test_cortes_20_40(x, esperado):
    assert nivel_por_corte(x, 20, 40) == esperado


def test_humedad_menos_45_es_alto(umbrales):
    nivel, anom, direccion = nivel_humedad(0.11, 0.20, umbrales["humedad_suelo"])
    assert (nivel, direccion) == ("alto", "deficit")
    assert anom == pytest.approx(-45)


def test_humedad_sobre_lo_normal_no_es_sequia(umbrales):
    nivel, _, direccion = nivel_humedad(0.40, 0.20, umbrales["humedad_suelo"])
    assert (nivel, direccion) == ("bajo", "exceso")


def test_lluvia_riesgo_por_falta_y_por_exceso(umbrales):
    u = umbrales["lluvia"]
    assert nivel_lluvia(3.0, 10.0, u)[0] == "alto"      # -70 %
    assert nivel_lluvia(7.0, 10.0, u)[0] == "medio"     # -30 %
    assert nivel_lluvia(9.0, 10.0, u)[0] == "bajo"      # -10 %
    assert nivel_lluvia(15.0, 10.0, u)[:3:2] == ("alto", "exceso")  # +50 %


def test_lluvia_estacion_seca_no_dispara(umbrales):
    # 0.6 vs 0.15 mm/día es +300 %, pero ambos son casi cero: no hay señal
    nivel, anom, direccion = nivel_lluvia(0.6, 0.15, umbrales["lluvia"])
    assert (nivel, direccion) == ("bajo", "estacion_seca")
    assert anom == pytest.approx(300)


@pytest.mark.parametrize("dif,esperado", [(-2, "bajo"), (1.4, "bajo"), (1.5, "medio"), (3.0, "medio"), (3.2, "alto")])
def test_calor(umbrales, dif, esperado):
    assert nivel_calor(dif, umbrales["calor"]) == esperado


@pytest.mark.parametrize("sst,esperado", [(0.2, "bajo"), (0.8, "medio"), (2.4, "alto")])
def test_el_nino(umbrales, sst, esperado):
    assert nivel_el_nino(sst, umbrales["el_nino"]) == esperado


def test_normal_ponderada_por_dias():
    clim = pd.Series({m: float(m) for m in range(1, 13)})      # enero = 1, febrero = 2…
    fechas = pd.date_range("2026-01-22", "2026-02-20")           # 10 días de enero + 20 de febrero
    assert normal_ponderada(clim, fechas) == pytest.approx((10 * 1 + 20 * 2) / 30)


def test_normal_misma_ventana_usa_solo_esos_dias_de_cada_anio():
    idx = pd.date_range("2001-01-01", "2002-12-31")
    hist = pd.Series(0.0, index=idx)
    hist[(idx.month == 10) & (idx.day >= 20)] = 10.0              # solo 20-31 de octubre vale 10
    ventana = pd.date_range("2026-10-20", "2026-10-31")
    assert normal_misma_ventana(hist, ventana) == pytest.approx(10.0)


def test_ventana_termina_en_ultimo_dia_valido():
    idx = pd.date_range("2026-10-01", "2026-11-14")
    df = pd.DataFrame({"A": 1.0}, index=idx)
    df.loc["2026-11-12":, "A"] = float("nan")                    # latencia de 3 días
    v = ventana_reciente(df, ["A"], 30)
    assert v.index.max() == pd.Timestamp("2026-11-11")
    assert len(v) == 30
