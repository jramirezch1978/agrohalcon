"""El panel técnico (solo desarrollo): se sirve desde el mismo servicio y su JSON es JSON estándar."""

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PANEL_JSON = RAIZ / "data" / "backup" / "panel.json"


@pytest.mark.skipif(not (RAIZ / "panel" / "index.html").exists(), reason="sin carpeta panel/")
def test_el_panel_se_sirve(client):
    r = client.get("/panel/")
    assert r.status_code == 200 and "AllpaShift" in r.text and "/recomendacion" in r.text
    for ruta in ("/validacion", "/asistente/preguntar", "/asistente/estado"):  # las tarjetas nuevas llaman a estos endpoints
        assert ruta in r.text, ruta


@pytest.mark.skipif(not PANEL_JSON.exists(), reason="corre `python -m db.export_panel`")
def test_panel_json_es_estandar_y_completo():
    def prohibido(c):  # NaN / Infinity no son JSON: el navegador los rechaza
        raise ValueError(f"valor no estándar en panel.json: {c}")

    d = json.loads(PANEL_JSON.read_text(encoding="utf-8"), parse_constant=prohibido)
    assert {"resumen", "zonas", "nino", "episodios", "fuentes", "mur"} <= set(d)
    assert len(d["zonas"]) == 16 and all("hoy" in z for z in d["zonas"])
    assert d["resumen"]["nino12_anom"]["valor"] is not None
    estados = {f["estado"] for f in d["fuentes"]}
    assert estados <= {"en_uso", "probado", "bloqueado", "planeado"}


def test_el_servicio_de_produccion_no_depende_del_panel(client):
    """El contrato sigue funcionando sin la carpeta panel/ (en la imagen de Docker no existe)."""
    assert client.get("/salud").json()["estado"] == "ok"
