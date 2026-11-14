"""Anota la versión EXACTA de cada dato NASA (para el campo References y 'Uso de IA / datos NASA').

    python -m etl.verificar_versiones

Escribe data/backup/versiones_datasets.json. No necesita token.
"""

import json
from datetime import date

from . import cmr
from .config import BACKUP


def main() -> None:
    filas = cmr.versiones_usadas()
    BACKUP.mkdir(parents=True, exist_ok=True)
    salida = {"consultado": date.today().isoformat(), "fuente": "NASA CMR (cmr.earthdata.nasa.gov)", "datasets": filas}
    (BACKUP / "versiones_datasets.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    for f in filas:
        estado = f.get("error") or f"v{f['version']} · {f['desde']} -> {f['hasta']} · {f['doiUrl']}"
        print(f"{f['uso']:<48} {estado}")
    print("\nNASA POWER no tiene versión en CMR: citar https://power.larc.nasa.gov/ y la fecha de consulta.")


if __name__ == "__main__":
    main()
