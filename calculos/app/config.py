"""Configuración: variables de entorno y umbrales de config/umbrales.yaml."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parent.parent


class Ajustes:
    def __init__(self) -> None:
        self.cache_dir = Path(os.getenv("CACHE_DIR", RAIZ / ".cache"))
        self.cache_ttl_horas = float(os.getenv("CACHE_TTL_HORAS", "24"))
        self.power_timeout_s = float(os.getenv("POWER_TIMEOUT_S", "30"))
        self.umbrales_path = Path(os.getenv("UMBRALES_PATH", RAIZ / "config" / "umbrales.yaml"))
        self.precalculado_dir = Path(os.getenv("PRECALCULADO_DIR", RAIZ / "data" / "precalculado"))


@lru_cache
def ajustes() -> Ajustes:
    return Ajustes()


@lru_cache
def umbrales() -> dict[str, Any]:
    with open(ajustes().umbrales_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
