"""Pruebas de los scripts de datos. Las normales y entradas se prueban sin internet (datos sintéticos
con la forma exacta de NASA POWER). Las llamadas reales llevan @pytest.mark.live: `pytest -m live`."""

from datetime import date

import pytest

from app.indicators import calcular_indicadores
from app.schemas import IndicadoresRequest
from etl import nasa_power
from etl.build_backup import quincenas
from etl.inputs import construir_entrada, normales_mensuales


def mensual_falso() -> dict:
    """1991-2020: marzo siempre 2 mm/día, el resto 0.5; T2M_MAX 35; GWETTOP 0.3; T2M_MIN 22."""
    serie = {p: {} for p in ("PRECTOTCORR", "T2M_MAX", "T2M_MIN", "GWETTOP")}
    for anio in range(1991, 2021):
        for mes in range(1, 13):
            k = f"{anio}{mes:02d}"
            serie["PRECTOTCORR"][k] = 2.0 if mes == 3 else 0.5
            serie["T2M_MAX"][k], serie["T2M_MIN"][k], serie["GWETTOP"][k] = 35.0, 22.0, 0.3
    serie["PRECTOTCORR"]["202003"] = 8.0  # un año atípico dentro de la base
    return serie


def diario_falso(lluvia: float, humedad: float, tmax: float, desde=date(2017, 3, 1), dias=31) -> dict:
    from datetime import timedelta

    claves = [(desde + timedelta(days=i)).strftime("%Y%m%d") for i in range(dias)]
    return {
        "PRECTOTCORR": dict.fromkeys(claves, lluvia),
        "GWETTOP": dict.fromkeys(claves, humedad),
        "T2M_MAX": dict.fromkeys(claves, tmax),
        "T2M_MIN": dict.fromkeys(claves, 22.0),
    }


def test_normales_son_el_promedio_del_mismo_mes():
    n = normales_mensuales(mensual_falso())
    assert n[3]["PRECTOTCORR"] == pytest.approx((29 * 2.0 + 8.0) / 30)  # marzo, con el año atípico
    assert n[7]["PRECTOTCORR"] == pytest.approx(0.5)
    assert n[1]["T2M_MAX"] == 35.0


def test_normales_ignoran_anios_fuera_de_la_base():
    serie = mensual_falso()
    serie["PRECTOTCORR"]["201703"] = 99.0  # 2017 está dentro de 1991-2020 -> sí cuenta
    serie["PRECTOTCORR"]["202603"] = 99.0  # 2026 está fuera -> no cuenta
    n = normales_mensuales(serie)
    assert n[3]["PRECTOTCORR"] == pytest.approx((28 * 2.0 + 8.0 + 99.0) / 30)


def test_entrada_valida_contra_el_servicio_y_detecta_inundacion():
    normales = normales_mensuales(mensual_falso())
    diario = diario_falso(lluvia=14.0, humedad=0.5, tmax=31.0)
    cuerpo, traza = construir_entrada(-5.35, -80.7, date(2017, 3, 15), diario, normales, sst_anomalia_c=2.1)
    ind = calcular_indicadores(IndicadoresRequest.model_validate(cuerpo))  # el contrato lo acepta tal cual
    assert ind.lluvia.nivel == "alto" and ind.elNino.nivel == "alto"
    assert ind.lluvia.fuente == "NASA POWER (PRECTOTCORR)"  # no dice IMERG si no vino de IMERG
    assert ind.humedadSuelo.fuente == "NASA POWER (GWETTOP)" and ind.humedadSuelo.unidad == "fracción 0-1"
    assert traza["ultimoDiaConDato"] == "2017-03-15" and traza["advertencias"] == []


def test_entrada_sin_sst_lo_avisa_y_no_miente_la_fuente():
    normales = normales_mensuales(mensual_falso())
    cuerpo, traza = construir_entrada(
        -5.35, -80.7, date(2017, 3, 15), diario_falso(1, 0.3, 35), normales, sst_anomalia_c=None
    )
    assert cuerpo["actual"]["sstAnomaliaC"] == 0.0
    assert "sin dato" in cuerpo["meta"]["elNino"]["fuente"]
    assert traza["advertencias"]


def test_entrada_con_ventana_vacia_falla_claro():
    normales = normales_mensuales(mensual_falso())
    with pytest.raises(ValueError, match="POWER no tiene datos"):
        construir_entrada(0, 0, date(2010, 1, 1), diario_falso(1, 0.3, 35), normales, 0.0)


def test_promedio_ventana_toma_los_ultimos_dias_con_dato():
    serie = {"20260101": 1.0, "20260102": 2.0, "20260103": 3.0, "20260105": 5.0}
    prom, ultimo = nasa_power.promedio_ventana(serie, date(2026, 1, 10), 2)
    assert (prom, ultimo) == (4.0, date(2026, 1, 5))
    assert nasa_power.promedio_ventana(serie, date(2025, 12, 1), 3) is None


def test_quincenas_cubren_el_mes_completo():
    q = quincenas(2017, 2, 3)
    assert q[0] == (date(2017, 2, 1), date(2017, 2, 15))
    assert q[1] == (date(2017, 2, 16), date(2017, 2, 28))  # 2017 no es bisiesto
    assert q[-1] == (date(2017, 3, 16), date(2017, 3, 31))
    assert len(q) == 4


# ------------------------------------------------------------------ llamadas reales (necesitan internet)
@pytest.mark.live
def test_live_power_marzo_2017_piura():
    """La 'máquina del tiempo': marzo 2017 llovió ~13 mm/día en Piura frente a ~1,4 en marzo 2016."""
    m = nasa_power.mensual(-5.19, -80.63, 2016, 2017)
    assert m["PRECTOTCORR"]["201703"] > 10
    assert m["PRECTOTCORR"]["201603"] < 3


@pytest.mark.live
def test_live_cmr_versiones_de_los_datasets():
    from etl import cmr

    smap = cmr.coleccion("SPL3SMP_E", "006")
    assert smap and smap["version"] == "006" and smap["doi"]
    assert cmr.coleccion("MUR-JPL-L4-GLOB-v4.1")["version"] == "4.1"


@pytest.mark.live
def test_live_oni_2017_fue_neutral_pese_al_nino_costero():
    from etl import oni

    s2017 = [f for f in oni.serie() if f["anio"] == 2017 and f["trimestre"] in ("JFM", "FMA", "MAM")]
    assert s2017 and all(f["fase"] == "neutral" for f in s2017)
