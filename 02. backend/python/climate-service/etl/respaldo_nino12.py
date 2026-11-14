"""Respaldo del indicador El Niño para el servicio (app/datos_respaldo/mur_nino12_semanal.json).

    python -m etl.respaldo_nino12            # lo regenera desde los datos de Sheila (calculos/data/precalculado o data/backup/sheila)

Por qué: el indicador de El Niño en vivo sale del ERDDAP de NOAA CoastWatch, que a veces no responde (desde la red de David
nunca respondió). Sin respaldo, la tarjeta de El Niño DESAPARECE de la app justo cuando es la señal principal de la demo.
Sheila ya bajó la serie semanal MUR SST de la caja Niño 1+2 (NASA JPL, v4.1): aquí se guardan sus últimas semanas dentro de
`app/` (así viaja dentro de la imagen de Docker, que solo copia esa carpeta). El servicio la usa SOLO si la consulta en vivo
falla y SOLO si la última semana tiene 21 días o menos; el indicador lo avisa con el campo opcional `aviso`.
"""

import json
import sys
from pathlib import Path

from db.aportes import ARCHIVO_MUR, localizar
from etl.config import RAIZ

SALIDA = RAIZ / "app" / "datos_respaldo" / "mur_nino12_semanal.json"
SEMANAS = 26  # medio año: de sobra para la regla de 21 días y para ver la tendencia reciente


def generar(carpeta: Path | None = None) -> dict:
    carpeta = carpeta or localizar()
    if carpeta is None:
        raise FileNotFoundError("No encuentro mur_sst_nino12.json (calculos/data/precalculado o data/backup/sheila)")
    origen = json.loads((carpeta / ARCHIVO_MUR).read_text(encoding="utf-8"))
    semanas = [s for s in origen["semanas"] if s.get("anomalia") is not None and s.get("sst") is not None][-SEMANAS:]
    meta = origen["metadatos"]
    return {
        "producto": "MUR SST v4.1 (NASA JPL, PO.DAAC), promedio semanal de la caja Niño 1+2 (0-10°S, 90-80°O)",
        "doi": meta.get("doi_producto"),
        "metodo": meta.get("metodo"),
        "anomalia_vs": "climatología MUR 2003-2014 (producto de NOAA ERD)",
        "descargado": meta.get("descargado"),
        "origen": "Sheila (rama feature/calculos-sheila): calculos/data/precalculado/mur_sst_nino12.json",
        "semanas": [{"semana": s["semana"], "sst": s["sst"], "anomalia": s["anomalia"], "dias": s.get("dias")} for s in semanas],
    }


def main() -> int:
    datos = generar()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    ultima = datos["semanas"][-1]
    print(f"{SALIDA}\n  {len(datos['semanas'])} semanas · última {ultima['semana']}: anomalía {ultima['anomalia']:+.2f} °C")
    return 0


if __name__ == "__main__":
    sys.exit(main())
