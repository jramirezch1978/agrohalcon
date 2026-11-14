"""Datos históricos que viajan DENTRO del servicio (app/datos_respaldo/) para el respaldo de El Niño y la "máquina del tiempo".

    python -m db.build                    # primero la base (de ahí sale el índice mensual de NOAA)
    python -m etl.respaldo_validacion     # escribe app/datos_respaldo/nino12_historico.json e imerg_piura_mensual.json

Por qué dentro de `app/`: la imagen de Docker solo copia esa carpeta y el servicio Python no puede leer la base de datos (regla 3 del doc 29).
Son series pequeñas (~30 KB cada una), ya descargadas de fuentes reales:

  nino12_historico.json     MUR SST v4.1 (NASA) semanal de la caja Niño 1+2, 2016-05 a hoy  ·  NOAA CPC Niño 1+2 mensual, 1982 a hoy (NO es NASA)
  imerg_piura_mensual.json  GPM IMERG V07 Final mensual 2001-2025 de 12 puntos de Piura (mm/mes) y su normal 2001-2020

Los datos de MUR e IMERG los bajó Sheila (calculos/data/precalculado). Sin la base o sin sus archivos, el servicio sigue funcionando
sin esos extras (usa NASA POWER y no muestra el respaldo de El Niño).
"""

import json
import sqlite3
import sys
from pathlib import Path

from db.aportes import ARCHIVO_IMERG, ARCHIVO_MUR, localizar
from db.build import RUTA_DB
from etl.config import RAIZ

SALIDA = RAIZ / "app" / "datos_respaldo"


def _json(datos: dict) -> str:
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":"))


def nino12(carpeta: Path, ruta_db: Path = RUTA_DB) -> dict:
    mur = json.loads((carpeta / ARCHIVO_MUR).read_text(encoding="utf-8"))
    semanas = [[s["semana"], s["sst"], s["anomalia"]] for s in mur["semanas"] if s.get("anomalia") is not None and s.get("sst") is not None]
    meta = mur["metadatos"]
    con = sqlite3.connect(ruta_db)
    cpc = {f[:7]: round(v, 2) for f, v in con.execute("SELECT fecha, valor FROM indice_climatico WHERE codigo = 'NINO12_ANOM' ORDER BY fecha")}
    con.close()
    return {
        "mur": {
            "producto": "MUR SST v4.1 (NASA JPL, PO.DAAC), promedio semanal de la caja Niño 1+2 (0-10°S, 90-80°O)", "doi": meta.get("doi_producto"),
            "metodo": meta.get("metodo"), "anomalia_vs": "climatología MUR 2003-2014 (producto de NOAA ERD)", "descargado": meta.get("descargado"),
            "origen": "Sheila (rama feature/calculos-sheila): calculos/data/precalculado/mur_sst_nino12.json", "columnas": ["semana (lunes)", "sst °C", "anomalía °C"],
            "semanas": semanas,
        },
        "cpc": {
            "producto": "NOAA CPC índice Niño 1+2 (OISST), anomalía mensual. NO es un producto de la NASA", "anomalia_vs": "1991-2020",
            "url": "https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices", "meses": cpc,
        },
    }  # fmt: skip


def imerg(carpeta: Path) -> dict:
    im = json.loads((carpeta / ARCHIVO_IMERG).read_text(encoding="utf-8"))
    prod = im["metadatos"]["productos"]["mensual"]
    return {
        "producto": f"{prod['nombre']} ({prod['short_name']} V{prod['version']})", "doi": prod["doi"], "url": prod["url"], "unidad": "mm/mes",
        "desde": im["mensual"]["meses"][0], "hasta": im["mensual"]["meses"][-1], "normal_periodo": im["climatologia"]["periodo"],
        "origen": "Sheila (rama feature/calculos-sheila): calculos/data/precalculado/imerg_piura.json",
        "puntos": [
            {"id": p["id"], "nombre": p["nombre"], "lat": p["lat"], "lon": p["lon"], "mm_mes": im["mensual"]["mm_mes"][p["id"]], "normal_mm_mes": im["climatologia"]["mm_mes"][p["id"]]}
            for p in im["puntos"]
        ],
    }  # fmt: skip


def main() -> int:
    carpeta = localizar()
    if carpeta is None or not RUTA_DB.exists():
        print("Faltan los datos de Sheila (calculos/data/precalculado o data/backup/sheila) o la base: corre antes `python -m db.build`")
        return 2
    SALIDA.mkdir(parents=True, exist_ok=True)
    n, i = nino12(carpeta), imerg(carpeta)
    (SALIDA / "nino12_historico.json").write_text(_json(n), encoding="utf-8", newline="\n")
    (SALIDA / "imerg_piura_mensual.json").write_text(_json(i), encoding="utf-8", newline="\n")
    ultima = n["mur"]["semanas"][-1]
    print(f"nino12_historico.json: MUR {len(n['mur']['semanas'])} semanas (última {ultima[0]}: {ultima[2]:+.2f} °C) · CPC {len(n['cpc']['meses'])} meses")
    print(f"imerg_piura_mensual.json: {len(i['puntos'])} puntos, {i['desde']} a {i['hasta']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
