"""Caché en disco simple: un archivo JSON por petición, con vencimiento."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


class CacheDisco:
    def __init__(self, carpeta: Path, ttl_horas: float = 24) -> None:
        self.carpeta = Path(carpeta)
        self.ttl_s = ttl_horas * 3600
        self.carpeta.mkdir(parents=True, exist_ok=True)

    def _ruta(self, clave: str) -> Path:
        return self.carpeta / (hashlib.sha256(clave.encode()).hexdigest()[:32] + ".json")

    def leer(self, clave: str) -> Any | None:
        ruta = self._ruta(clave)
        if not ruta.exists():
            return None
        try:
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - contenido["guardado"] > self.ttl_s:
            return None
        return contenido["datos"]

    def guardar(self, clave: str, datos: Any) -> None:
        ruta = self._ruta(clave)
        tmp = ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps({"clave": clave, "guardado": time.time(), "datos": datos}), encoding="utf-8")
        tmp.replace(ruta)  # escritura atómica
