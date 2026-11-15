"""Resume la base de datos en un JSON para el panel técnico (panel/index.html) y para quien quiera mostrar los datos.

    python -m db.export_panel        # escribe data/backup/panel.json
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from etl.config import BACKUP

from .build import RUTA_DB, SAMPLE_CATALOGO


def _n(x):
    """NaN de pandas -> None (JSON válido)."""
    return None if x is None or (isinstance(x, float) and x != x) else x


def _limpiar(o):
    """Recorre el resultado y cambia cualquier NaN/inf por None: el JSON del panel debe ser estándar."""
    if isinstance(o, float):
        return o if o == o and o not in (float("inf"), float("-inf")) else None
    if isinstance(o, dict):
        return {k: _limpiar(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_limpiar(v) for v in o]
    return o


def _df(con, sql: str, **p) -> pd.DataFrame:
    return pd.read_sql(text(sql), con, params=p)


def _lluvia2017(df: pd.DataFrame) -> list[dict]:
    """dic-2016..jun-2017 en mm/día: IMERG Final (satélite) frente a POWER (reanálisis), cada uno con su normal. [] si la zona no tiene IMERG."""
    meses: dict[str, dict] = {}
    for r in df.itertuples():
        k = "imerg" if r.variable == "IMERG_PRECIP_M" else "power"
        fila = meses.setdefault(str(r.fecha)[:7], {"mes": str(r.fecha)[:7]})
        fila[k], fila[f"{k}_normal"] = round(r.valor, 2), None if pd.isna(r.normal) else round(r.normal, 2)
    return [meses[m] for m in sorted(meses)]


def exportar(ruta_db: Path = RUTA_DB) -> dict:
    eng = create_engine(f"sqlite:///{ruta_db}")
    with eng.connect() as con:
        zonas = _df(con, "SELECT z.*, r.codigo AS region FROM zona z JOIN region r ON r.id = z.region_id WHERE z.tipo = 'agricola' ORDER BY z.id")
        hoy = {int(r.zona_id): json.loads(r.payload) for r in _df(con, "SELECT zona_id, payload FROM recomendacion_cache").itertuples()}
        val = _df(con, "SELECT zona_id, desde, hasta, nivel_maximo, indicadores, advertencias FROM validacion_quincena ORDER BY hasta")
        smap = _df(con, "SELECT o.zona_id, o.fecha, o.valor FROM observacion o JOIN variable v ON v.id = o.variable_id WHERE v.codigo = 'SMAP_SM' AND o.fecha >= :d ORDER BY o.fecha", d=str(date.today().replace(year=date.today().year - 1)))
        ndvi = _df(con, "SELECT o.zona_id, o.fecha, o.valor FROM observacion o JOIN variable v ON v.id = o.variable_id WHERE v.codigo = 'VNP13A1_NDVI' ORDER BY o.fecha")
        tend = _df(con, "SELECT t.zona_id, v.codigo AS variable, t.pendiente_sen_por_decada AS pendiente, t.p_valor, t.sentido FROM tendencia t JOIN variable v ON v.id = t.variable_id")
        comp = _df(con, "SELECT c.zona_id, c.mes, c.media_nino, c.media_normal, c.razon, c.n_nino, c.n_normal FROM composite_nino c ORDER BY c.mes")
        nino = _df(con, "SELECT fecha, MAX(CASE WHEN codigo='NINO12_ANOM' THEN valor END) AS nino12_anom, MAX(CASE WHEN codigo='NINO34_ANOM' THEN valor END) AS nino34_anom FROM indice_climatico WHERE codigo IN ('NINO12_ANOM','NINO34_ANOM') GROUP BY fecha ORDER BY fecha")
        oni = _df(con, "SELECT fecha, valor FROM indice_climatico WHERE codigo = 'ONI' ORDER BY fecha DESC LIMIT 1")
        eps = _df(con, "SELECT inicio, fin, meses, pico_anomalia_c, pico_fecha FROM episodio_calido ORDER BY inicio")
        mur = _df(con, "SELECT o.fecha, v.codigo AS variable, o.valor FROM observacion o JOIN variable v ON v.id = o.variable_id WHERE o.zona_id = 101 AND v.codigo IN ('MUR_SST','MUR_SST_ANOM') ORDER BY o.fecha")
        contr = _df(con, "SELECT c.par, z.nombre AS zona, z.id AS zona_id, c.variable, c.escala, c.n, c.periodo_ini, c.periodo_fin, c.correlacion, c.sesgo_medio, c.rmse, c.nota FROM contraste_fuentes c LEFT JOIN zona z ON z.id = c.zona_id ORDER BY c.par, z.id")
        im17 = _df(con, """SELECT o.zona_id, o.fecha, v.codigo AS variable, o.valor, n.media AS normal
            FROM observacion o JOIN variable v ON v.id = o.variable_id
            LEFT JOIN normal_mensual n ON n.zona_id = o.zona_id AND n.variable_id = o.variable_id AND n.mes = CAST(SUBSTR(CAST(o.fecha AS VARCHAR(10)), 6, 2) AS INTEGER)
            WHERE o.escala = 'mensual' AND v.codigo IN ('IMERG_PRECIP_M', 'PRECTOTCORR') AND o.fecha BETWEEN '2016-12-01' AND '2017-06-01'
              AND o.zona_id IN (SELECT zona_id FROM observacion WHERE variable_id = (SELECT id FROM variable WHERE codigo = 'IMERG_PRECIP_M'))
            ORDER BY o.fecha""")
        fuentes = _df(con, "SELECT codigo, nombre, institucion, producto, version, doi, resolucion, cobertura, url, acceso, estado, nota FROM fuente_dato ORDER BY id")
        conteos = {t: int(con.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()) for t in ("observacion", "normal_mensual", "indice_climatico", "tendencia", "validacion_quincena", "zona", "fuente_dato")}

    salida_zonas = []
    for z in zonas.itertuples():
        zid = int(z.id)
        h = hoy.get(zid)
        salida_zonas.append(
            {
                "id": zid, "nombre": z.nombre, "region": z.region, "lat": z.lat, "lon": z.lon,
                "elevacion_m": _n(z.elevacion_m), "pendiente_pct": _n(z.pendiente_pct),
                "suelo": {"ph": _n(z.suelo_ph), "carbono_g_kg": _n(z.suelo_carbono_g_kg), "arcilla_pct": _n(z.suelo_arcilla_pct), "arena_pct": _n(z.suelo_arena_pct)},
                "hoy": h,
                "validacion2017": [
                    {"desde": v.desde, "hasta": v.hasta, "nivelMaximo": v.nivel_maximo, "indicadores": json.loads(v.indicadores), "advertencias": json.loads(v.advertencias or "[]")}
                    for v in val[val["zona_id"] == zid].itertuples()
                ],
                "lluvia2017": _lluvia2017(im17[im17["zona_id"] == zid]),
                "smap": [{"fecha": s.fecha, "valor": round(s.valor, 4)} for s in smap[smap["zona_id"] == zid].itertuples()],
                "ndvi": [{"fecha": s.fecha, "ndvi": round(s.valor, 4)} for s in ndvi[ndvi["zona_id"] == zid].itertuples()],
                "tendencias": {t.variable: {"pendiente_decada": round(t.pendiente, 4), "p": round(t.p_valor, 4), "sentido": t.sentido} for t in tend[tend["zona_id"] == zid].itertuples()},
                "composite_lluvia": [{"mes": int(c.mes), "nino": round(c.media_nino, 2), "normal": round(c.media_normal, 2), "razon": None if pd.isna(c.razon) else round(c.razon, 1)} for c in comp[comp["zona_id"] == zid].itertuples()],
            }
        )
    niv = [z["hoy"]["nivelMaximo"] for z in salida_zonas if z["hoy"]]
    ultimo_nino = nino.dropna(subset=["nino12_anom"]).iloc[-1]
    resumen = {
        "fecha_datos": max((z["hoy"]["fecha"] for z in salida_zonas if z["hoy"]), default=None),
        "nino12_anom": {"fecha": ultimo_nino["fecha"], "valor": float(ultimo_nino["nino12_anom"])},
        "nino34_anom": float(ultimo_nino["nino34_anom"]) if pd.notna(ultimo_nino["nino34_anom"]) else None,
        "oni": {"fecha": oni.iloc[0]["fecha"], "valor": float(oni.iloc[0]["valor"])} if len(oni) else None,
        "zonas_total": len(niv), "zonas_alto": niv.count("alto"), "zonas_medio": niv.count("medio"), "zonas_bajo": niv.count("bajo"),
        "filas": conteos,
    }  # fmt: skip
    datos = {
        "generado": date.today().isoformat(),
        "resumen": resumen,
        "zonas": salida_zonas,
        "nino": [{"fecha": r.fecha, "n12": None if pd.isna(r.nino12_anom) else round(r.nino12_anom, 2), "n34": None if pd.isna(r.nino34_anom) else round(r.nino34_anom, 2)} for r in nino.itertuples()],
        "episodios": eps.to_dict("records"),
        "mur": {"punto": "Mar frente a Piura (-5,5; -81,5)", "sst": mur[mur["variable"] == "MUR_SST"][["fecha", "valor"]].to_dict("records"), "anomalia": mur[mur["variable"] == "MUR_SST_ANOM"][["fecha", "valor"]].to_dict("records")},
        "contrastes": contr.where(contr.notna(), None).to_dict("records"),
        "fuentes": fuentes.where(fuentes.notna(), None).to_dict("records"),
    }
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "panel.json").write_text(json.dumps(_limpiar(datos), ensure_ascii=False, default=str, allow_nan=False), encoding="utf-8")
    # el catálogo de PRUEBA para el comparador del panel (marcado como tal en la propia página)
    (BACKUP / "catalogo_prueba.json").write_text(SAMPLE_CATALOGO.read_text(encoding="utf-8"), encoding="utf-8")
    return resumen


def main() -> None:
    r = exportar()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print(f"\nEscrito {BACKUP / 'panel.json'}")


if __name__ == "__main__":
    main()
