"""Descarga MUR SST v4.1 (temperatura y anomalía) de la caja Niño 1+2 vía ERDDAP de NOAA CoastWatch
y guarda el promedio semanal en data/precalculado/mur_sst_nino12.json.

No necesita cuenta de Earthdata (ERDDAP es público).

Uso (desde la carpeta agroshift-calculos):
    python -m scripts.descargar_mur_sst                 # todo, desde 2016-06 (~15-20 min la primera vez)
    python -m scripts.descargar_mur_sst --actualizar    # solo los meses recientes (antes de la demo, ~1 min)

Es reanudable: cada mes ya procesado queda en data/crudo/mur/ (promedios diarios, unos KB) y no se
vuelve a pedir. --actualizar vuelve a pedir el mes anterior y el actual.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.fuentes.mur_sst import (
    CAJA_NINO12, DATASET_ANOM, DATASET_SST, ERDDAP, MIN_DIAS_SEMANA, STRIDE, VAR_ANOM, VAR_SST, a_semanas, media_caja,
)

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "crudo" / "mur"
SALIDA = RAIZ / "data" / "precalculado" / "mur_sst_nino12.json"


def url_mes(dataset: str, variable: str, mes: pd.Period, ultimo: bool) -> str:
    (la0, la1), (lo0, lo1) = CAJA_NINO12["lat"], CAJA_NINO12["lon"]
    t0 = f"({mes.start_time:%Y-%m-%d}T09:00:00Z)"
    t1 = "(last)" if ultimo else f"({mes.end_time:%Y-%m-%d}T09:00:00Z)"
    q = f"{variable}[{t0}:1:{t1}][({la0}):{STRIDE}:({la1})][({lo0}):{STRIDE}:({lo1})]"
    return f"{ERDDAP}/{dataset}.csv?{q}"


def bajar_mes(dataset: str, variable: str, mes: pd.Period, ultimo: bool, forzar: bool) -> pd.Series | None:
    archivo = CRUDO / f"{dataset}_{mes}.csv"
    if archivo.exists() and not forzar:
        s = pd.read_csv(archivo, index_col=0, parse_dates=True).iloc[:, 0]
        return s.rename(variable)
    url = url_mes(dataset, variable, mes, ultimo)
    for intento in range(4):
        try:
            r = httpx.get(url, timeout=300)
            if r.status_code == 404 or (r.status_code == 500 and "outside" in r.text.lower()):
                return None  # el mes aún no existe en el dataset
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text), skiprows=[1])  # fila 2 = unidades
            s = media_caja(df, variable)
            archivo.parent.mkdir(parents=True, exist_ok=True)
            s.to_csv(archivo)
            return s
        except (httpx.HTTPError, pd.errors.ParserError) as e:
            print(f"  ! {dataset} {mes}: {type(e).__name__}, reintento {intento + 1}", file=sys.stderr)
            time.sleep(5 * 2**intento)
    raise RuntimeError(f"No se pudo descargar {dataset} {mes}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", default="2016-06")
    ap.add_argument("--actualizar", action="store_true", help="vuelve a pedir el mes anterior y el actual")
    ap.add_argument("--hilos", type=int, default=2)
    ap.add_argument("--solo-cache", action="store_true",
                    help="no descarga: arma el JSON con los meses ya guardados en data/crudo/mur (los demás quedan fuera)")
    a = ap.parse_args()

    meses = list(pd.period_range(a.desde, pd.Period(date.today(), "M"), freq="M"))
    recientes = set(meses[-2:])
    t0 = time.time()

    def tarea(args):
        dataset, variable, mes = args
        if a.solo_cache:
            archivo = CRUDO / f"{dataset}_{mes}.csv"
            if not archivo.exists():
                return dataset, None
            return dataset, pd.read_csv(archivo, index_col=0, parse_dates=True).iloc[:, 0].rename(variable)
        s = bajar_mes(dataset, variable, mes, ultimo=mes == meses[-1], forzar=a.actualizar and mes in recientes)
        print(f"  {dataset:22} {mes}  {'sin datos' if s is None else f'{len(s)} días'}", flush=True)
        return dataset, s

    trabajos = [(ds, var, m) for m in meses for ds, var in ((DATASET_SST, VAR_SST), (DATASET_ANOM, VAR_ANOM))]
    with ThreadPoolExecutor(a.hilos) as ex:  # pocos hilos: ERDDAP es un servicio compartido
        resultados = list(ex.map(tarea, trabajos))

    sst = pd.concat([s for ds, s in resultados if ds == DATASET_SST and s is not None])
    anom = pd.concat([s for ds, s in resultados if ds == DATASET_ANOM and s is not None])
    diaria = pd.DataFrame({"sst": sst[~sst.index.duplicated()], "anomalia": anom[~anom.index.duplicated()]}).sort_index()
    semanas = a_semanas(diaria)

    salida = {
        "metadatos": {
            "producto": "MUR SST (Multi-scale Ultra-high Resolution SST Analysis), GHRSST L4",
            "version": "v4.1 (fv04.1)",
            "proveedor": "NASA JPL PO.DAAC; accedido vía ERDDAP de NOAA CoastWatch (West Coast Node)",
            "datasets": {
                "sst": {"id": DATASET_SST, "variable": VAR_SST, "url": f"{ERDDAP}/{DATASET_SST}.html"},
                "anomalia": {
                    "id": DATASET_ANOM, "variable": VAR_ANOM, "url": f"{ERDDAP}/{DATASET_ANOM}.html",
                    "climatologia_base": "JPL MUR 2003-2014 (anomalía calculada por NOAA ERD)",
                },
            },
            "doi_producto": "10.5067/GHGMR-4FJ04",
            "zona": {"nombre": "Niño 1+2", "lat": list(CAJA_NINO12["lat"]), "lon": list(CAJA_NINO12["lon"])},
            "resolucion_usada": f"0.25° (cada {STRIDE} celdas de la rejilla de 0.01°)",
            "metodo": "Promedio diario de la caja ponderado por cos(lat), solo océano; luego promedio por "
                      f"semana ISO (lunes a domingo). Semanas con menos de {MIN_DIAS_SEMANA} días válidos se omiten.",
            "unidades": {"sst": "°C", "anomalia": "°C"},
            "periodo": {"inicio": str(semanas.index.min().date()), "fin": str(semanas.index.max().date())},
            "ultimo_dia_con_datos": str(diaria["anomalia"].dropna().index.max().date()),
            "descargado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "semanas": [
            {"semana": str(i.date()),
             "sst": None if pd.isna(r.sst) else round(float(r.sst), 3),
             "anomalia": None if pd.isna(r.anomalia) else round(float(r.anomalia), 3),
             "dias": int(r.dias)}
            for i, r in semanas.iterrows()
        ],
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(semanas)} semanas → {SALIDA} ({SALIDA.stat().st_size / 1024:.0f} KB) en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
