"""Genera los DATOS DE RESPALDO (Plan B de la demo) y la VALIDACIÓN de El Niño costero 2017.

    python -m etl.build_backup                         # Piura (7 zonas): normales, 2016-2017, actual
    python -m etl.build_backup --todas                 # los 16 valles del norte
    python -m etl.build_backup --catalogo ../../../data/crops/cultivos.json   # añade rotaciones y "qué hacer"
    python -m etl.build_backup --sst-csv sst_2017.csv  # anomalía del mar a mano (fecha,anomaliaC)
    python -m etl.build_backup --ndvi                  # añade la caída del NDVI de MODIS en 2017 (lento)

Salida (data/backup/, pequeña, se sube al repo):
  zonas.json · normales_power_1991_2020.json · datos_nasa_respaldo.csv (tabla `datosNasa` del contrato)
  validacion_2017.json  -> qué habría dicho AgroShift cada quincena de ene-abr 2017, zona por zona
  actual.json           -> la entrada y el resultado de hoy por zona
Necesita internet (NASA POWER). La temperatura del mar es opcional: si no responde, se avisa en el JSON.
"""

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path

from app.crops import cargar_catalogo
from app.indicators import calcular_indicadores
from app.que_hacer import construir_que_hacer
from app.rotations import rotaciones_para
from app.schemas import IndicadoresRequest

from . import mur_sst, nasa_power
from .config import BACKUP
from .inputs import BASE_NORMAL, construir_entrada, normales_mensuales
from .zonas import ZONAS, Zona, por_region

VARIABLES_CSV = {"PRECTOTCORR": "lluviaMm", "T2M_MAX": "tempMaxC", "T2M_MIN": "tempMinC", "GWETTOP": "humedadSuelo"}


def quincenas(anio: int, mes_ini: int, mes_fin: int) -> list[tuple[date, date]]:
    salida = []
    for mes in range(mes_ini, mes_fin + 1):
        siguiente = date(anio + (mes == 12), mes % 12 + 1, 1)
        salida += [(date(anio, mes, 1), date(anio, mes, 15)), (date(anio, mes, 16), siguiente - timedelta(days=1))]
    return salida


def leer_sst_csv(ruta: Path | None) -> list[tuple[date, float]]:
    if not ruta:
        return []
    with open(ruta, encoding="utf-8") as f:
        return sorted((date.fromisoformat(r["fecha"]), float(r["anomaliaC"])) for r in csv.DictReader(f))


def sst_para(dia: date, manual: list[tuple[date, float]], estado: dict) -> float | None:
    """Anomalía del mar: primero el CSV manual, luego MUR SST en línea (se prueba una vez; si cae, no se insiste)."""
    previos = [v for d, v in manual if d <= dia]
    if previos:
        return previos[-1]
    if estado["sst_caido"]:
        return None
    r = mur_sst.anomalia_sst(dia)
    if r is None:
        estado["sst_caido"] = True
        print("  ⚠ MUR SST no responde: la anomalía del mar quedará en 0 y se avisa en el JSON")
        return None
    return r["anomaliaC"]


def evaluar(cuerpo: dict, fecha: date, catalogo) -> dict:
    """Corre el MISMO código que el servicio (indicadores + rotaciones + qué hacer), sin HTTP."""
    ind = calcular_indicadores(IndicadoresRequest.model_validate(cuerpo))
    salida = {"indicadores": ind.model_dump()}
    if catalogo:
        elegidas, todas = rotaciones_para(ind, catalogo, None, fecha, 3, None)
        salida["rotaciones"] = [e.resultado.model_dump() for e in elegidas]
        salida["queHacer"] = construir_que_hacer(ind, elegidas, todas).model_dump()
    return salida


def procesar_zona(z: Zona, catalogo, sst_manual, estado, hoy: date) -> tuple[dict, list[dict]]:
    print(f"- {z.nombre} ({z.lat}, {z.lon})")
    mensual = nasa_power.mensual(z.lat, z.lon, BASE_NORMAL[0], hoy.year)
    normales = normales_mensuales(mensual)
    diario_2017 = nasa_power.diario(z.lat, z.lon, date(2016, 12, 1), date(2017, 4, 30))
    diario_hoy = nasa_power.diario(z.lat, z.lon, hoy - timedelta(days=40), hoy)

    validacion = []
    for ini, fin in quincenas(2017, 1, 4):
        cuerpo, traza = construir_entrada(z.lat, z.lon, fin, diario_2017, normales, sst_para(fin, sst_manual, estado))
        validacion.append(
            {"quincena": {"desde": ini.isoformat(), "hasta": fin.isoformat()}, "entrada": cuerpo,
             "trazabilidad": traza, **evaluar(cuerpo, fin, catalogo)}
        )  # fmt: skip

    cuerpo_hoy, traza_hoy = construir_entrada(z.lat, z.lon, hoy, diario_hoy, normales, sst_para(hoy, sst_manual, estado))
    actual = {"zona": z.a_dict(), "entrada": cuerpo_hoy, "trazabilidad": traza_hoy, **evaluar(cuerpo_hoy, hoy, catalogo)}

    filas_csv = []
    for param, nombre in VARIABLES_CSV.items():
        for clave, valor in mensual.get(param, {}).items():
            anio = int(clave[:4])
            if anio in (2016, 2017) or anio == hoy.year:
                filas_csv.append(
                    {"lat": z.lat, "lon": z.lon, "fecha": f"{clave[:4]}-{clave[4:]}-01",
                     "fuente": "NASA POWER", "variable": f"{param}:{nombre}", "valor": round(valor, 4)}
                )  # fmt: skip
    return {
        "zona": z.a_dict(),
        "normales": {str(m): {k: round(v, 4) for k, v in n.items()} for m, n in normales.items()},
        "validacion2017": validacion,
        "actual": actual,
    }, filas_csv


def agregar_ndvi(resultados: list[dict]) -> None:
    from . import ndvi_modis

    for r in resultados:
        z = r["zona"]
        print(f"- NDVI {z['nombre']} (MODIS, lento)…")
        try:
            s = ndvi_modis.serie(z["lat"], z["lon"], date(2016, 11, 1), date(2017, 7, 31))
        except RuntimeError as e:
            r["ndvi2017"] = {"error": str(e)[:200]}
            continue
        r["ndvi2017"] = {
            "serie": s,
            "caidaPct": ndvi_modis.caida_pct(s, ("2016-12-01", "2017-01-31"), ("2017-03-01", "2017-05-31")),
            "nota": "caidaPct = NDVI mar-may 2017 frente a dic 2016-ene 2017 (negativo = vegetación que cae)",
        }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regiones", nargs="+", default=["piura"])
    ap.add_argument("--todas", action="store_true", help="los 16 valles del norte")
    ap.add_argument("--catalogo", type=Path, help="JSON del catálogo de cultivos (si falta, solo indicadores)")
    ap.add_argument("--sst-csv", type=Path, help="CSV fecha,anomaliaC con la anomalía del mar (opcional)")
    ap.add_argument("--ndvi", action="store_true", help="añade MODIS NDVI 2017 (40-60 s por zona)")
    ap.add_argument("--salida", type=Path, default=BACKUP)
    args = ap.parse_args()

    zonas = ZONAS if args.todas else [z for r in args.regiones for z in por_region(r)]
    catalogo = cargar_catalogo(args.catalogo) if args.catalogo else None
    sst_manual = leer_sst_csv(args.sst_csv)
    hoy = date.today()
    estado = {"sst_caido": False}

    print(f"Procesando {len(zonas)} zonas con NASA POWER…")
    resultados, filas = [], []
    for z in zonas:
        r, f = procesar_zona(z, catalogo, sst_manual, estado, hoy)
        resultados.append(r)
        filas += f
    if args.ndvi:
        agregar_ndvi(resultados)

    out = args.salida
    out.mkdir(parents=True, exist_ok=True)

    def guardar(nombre: str, datos) -> None:
        (out / nombre).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")

    guardar("zonas.json", [z.a_dict() for z in zonas])
    guardar("normales_power_1991_2020.json", {r["zona"]["nombre"]: r["normales"] for r in resultados})
    guardar("validacion_2017.json", {
        "descripcion": "Qué habría dicho AgroShift cada quincena de ene-abr 2017 (El Niño costero), por zona.",
        "generado": hoy.isoformat(),
        "sstDisponible": not estado["sst_caido"] or bool(sst_manual),
        "zonas": [{"zona": r["zona"], "quincenas": r["validacion2017"], **({"ndvi2017": r["ndvi2017"]} if "ndvi2017" in r else {})} for r in resultados],
    })  # fmt: skip
    guardar("actual.json", {"generado": hoy.isoformat(), "zonas": [r["actual"] for r in resultados]})
    with open(out / "datos_nasa_respaldo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["lat", "lon", "fecha", "fuente", "variable", "valor"])
        w.writeheader()
        w.writerows(filas)
    print(f"\nListo: {len(zonas)} zonas, {len(filas)} filas en datos_nasa_respaldo.csv -> {out}")


if __name__ == "__main__":
    main()
