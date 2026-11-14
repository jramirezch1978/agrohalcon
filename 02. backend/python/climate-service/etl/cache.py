"""Caché en disco de las descargas (data/raw/cache/*.json, ignorado por git). Las descargas largas se
guardan aquí y db/build.py las vuelca a la base de datos: así una descarga lenta no se repite."""

import json
from pathlib import Path

from .config import RAW

CACHE = RAW / "cache"


def ruta(nombre: str) -> Path:
    return CACHE / f"{nombre}.json"


def guardar(nombre: str, datos) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = ruta(nombre)
    p.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return p


def leer(nombre: str, defecto=None):
    p = ruta(nombre)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else defecto
