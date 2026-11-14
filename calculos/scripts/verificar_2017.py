"""Revisión a mano de la validación 2017 (El Niño costero en Piura), con el MISMO cálculo de /validacion.

    python -m scripts.verificar_2017 [--anio 2017 --lat -5.19 --lon -80.63]

Imprime la serie semanal de MUR SST (dic.-abr.), la lluvia mensual vs. lo normal, la fecha de alerta y las
semanas de anticipación.
"""
from __future__ import annotations

import argparse
import asyncio

import pandas as pd

from app.calculos.validacion import calcular_validacion
from app.config import umbrales
from app.dependencias import cliente_power
from app.fuentes.precalculado import serie_mur


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio", type=int, default=2017)
    ap.add_argument("--lat", type=float, default=-5.19)
    ap.add_argument("--lon", type=float, default=-80.63)
    a = ap.parse_args()
    u = umbrales()

    mur = serie_mur()
    if mur is not None:
        print(f"=== MUR SST Niño 1+2, semanal (medio > {u['el_nino']['medio']} °C, alto > {u['el_nino']['alto']} °C)")
        for semana, f in mur.semanas.loc[f"{a.anio - 1}-11-28":f"{a.anio}-04-30"].iterrows():
            barra = "█" * max(0, int(round(f.anomalia * 4))) if pd.notna(f.anomalia) else ""
            print(f"  {semana:%Y-%m-%d}  SST {f.sst:5.2f} °C  anomalía {f.anomalia:+5.2f} °C  {barra}")
    else:
        print("(sin MUR SST: la alerta se calcula solo con lluvia)")

    r = asyncio.run(calcular_validacion(a.anio, a.lat, a.lon, "es", cliente_power()))
    ll = r["series"]["lluvia"]
    print(f"\n=== Lluvia {a.anio} en ({a.lat}, {a.lon}) — {ll['fuente']} · {ll.get('producto')} · {ll.get('punto')}")
    for m, (v, n) in enumerate(zip(ll["valores"], ll["normal"]), start=1):
        veces = f"{v / n:5.1f}×" if v is not None and n else "   - "
        v_txt = f"{v:7.1f}" if v is not None else "   null"
        print(f"  {a.anio}-{m:02d}  {v_txt} mm   normal {n:6.1f} mm   {veces}")

    print(f"\nMes de lluvia máxima: {r['mesLluviaMaxima']}")
    print(f"Alerta: {r['alerta']}")
    print(f"Semanas de anticipación: {r['semanasAnticipacion']}")
    print(f"Humedad del suelo: {r['series']['humedadSuelo']['fuente']} · NDVI: {r['series']['ndvi']['fuente']}")
    print(f"\nResumen: {r['resumen']}")
    if r["realidad"]:
        print(f"Realidad ({r['realidad']['fuente']}): {r['realidad']['resumen']}")


if __name__ == "__main__":
    main()
