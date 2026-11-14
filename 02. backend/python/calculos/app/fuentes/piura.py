"""Puntos del piloto de Piura (los mismos de las zonas del mapa de la app) y distancias."""
from __future__ import annotations

import math

# id, nombre, lat, lon. Zonas del mapa (config/zonas_piura.yaml) + las del frontend + la ciudad de Piura.
PUNTOS_PIURA: list[dict] = [
    {"id": "piura", "nombre": "Piura (ciudad)", "lat": -5.19, "lon": -80.63},
    {"id": "bajo_piura", "nombre": "Bajo Piura", "lat": -5.35, "lon": -80.70},
    {"id": "medio_piura", "nombre": "Medio Piura", "lat": -5.20, "lon": -80.45},
    {"id": "alto_piura", "nombre": "Alto Piura", "lat": -5.18, "lon": -79.97},   # Morropón
    {"id": "chulucanas", "nombre": "Chulucanas", "lat": -5.09, "lon": -80.16},
    {"id": "sullana", "nombre": "Sullana", "lat": -4.90, "lon": -80.69},
    {"id": "tambogrande", "nombre": "Tambogrande", "lat": -4.93, "lon": -80.34},
    {"id": "valle_chira", "nombre": "Valle del Chira", "lat": -4.90, "lon": -80.85},
    {"id": "sechura", "nombre": "Sechura", "lat": -5.56, "lon": -80.82},
    {"id": "san_lorenzo", "nombre": "San Lorenzo", "lat": -4.72, "lon": -80.25},
    {"id": "huancabamba", "nombre": "Huancabamba", "lat": -5.24, "lon": -79.45},
    {"id": "ayabaca", "nombre": "Ayabaca", "lat": -4.64, "lon": -79.71},
]

# Caja que cubre todos los puntos (con margen de una celda de IMERG)
CAJA_PIURA = {"lat": (-6.5, -4.0), "lon": (-81.3, -79.3)}
DISTANCIA_MAX_KM = 25.0


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia de gran círculo (haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def punto_cercano(lat: float, lon: float, max_km: float = DISTANCIA_MAX_KM) -> tuple[dict, float] | None:
    """Punto del piloto más cercano si está a menos de `max_km`; si no, None (se usa NASA POWER)."""
    mejor = min(PUNTOS_PIURA, key=lambda p: distancia_km(lat, lon, p["lat"], p["lon"]))
    d = distancia_km(lat, lon, mejor["lat"], mejor["lon"])
    return (mejor, d) if d <= max_km else None
