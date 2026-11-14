"""Valles y zonas agrícolas del norte del Perú (tabla `zonas` del contrato: id, nombre, lat, lon, region).

⚠️ Coordenadas APROXIMADAS (centro del valle), tomadas de 24_exploracion_apis_nasa.md y del ejemplo
de /api/mapa del contrato. Alejandro debe validarlas con el catálogo (rama feature/catalogo-cultivos).
Nota: NASA POWER tiene celdas de 0,5° (~55 km): varios valles de Piura reciben el mismo dato de POWER.
"""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Zona:
    id: int
    nombre: str
    region: str  # piura | tumbes | lambayeque | la_libertad | cajamarca | amazonas | san_martin
    lat: float
    lon: float

    def a_dict(self) -> dict:
        return asdict(self)


ZONAS: list[Zona] = [
    # --- Piura (caso piloto; /api/mapa?region=piura) ---
    Zona(1, "Bajo Piura", "piura", -5.35, -80.70),  # coordenadas del ejemplo del contrato
    Zona(2, "Valle del Chira", "piura", -4.90, -80.85),  # coordenadas del ejemplo del contrato
    Zona(3, "Medio Piura - Castilla", "piura", -5.20, -80.62),
    Zona(4, "San Lorenzo - Tambogrande", "piura", -4.93, -80.34),
    Zona(5, "Alto Piura - Chulucanas", "piura", -5.10, -80.16),
    Zona(6, "Sechura - Bernal / Vice", "piura", -5.45, -80.80),
    Zona(7, "Sierra - Huancabamba", "piura", -5.24, -79.45),
    # --- Resto del norte ---
    Zona(8, "Valle de Tumbes", "tumbes", -3.57, -80.45),
    Zona(9, "Chancay-Lambayeque", "lambayeque", -6.70, -79.90),
    Zona(10, "Olmos", "lambayeque", -5.99, -79.74),
    Zona(11, "Jequetepeque", "la_libertad", -7.20, -79.45),
    Zona(12, "Chavimochic - Virú", "la_libertad", -8.41, -78.75),
    Zona(13, "Jaén", "cajamarca", -5.71, -78.81),
    Zona(14, "Valle de Cajamarca", "cajamarca", -7.16, -78.50),
    Zona(15, "Bagua - Utcubamba", "amazonas", -5.64, -78.53),
    Zona(16, "Alto Mayo - Moyobamba", "san_martin", -6.03, -76.97),
]

# Parcela de ejemplo del contrato (Piura): se usa en las pruebas y en la demo.
PUNTO_DEMO = (-5.19, -80.63)

# Punto de mar frente a Piura para la señal de El Niño costero (dentro de la región Niño 1+2).
# MUR SST a 1 km: un punto en la costa puede caer en tierra y dar vacío, por eso es mar adentro.
PUNTO_MAR_PIURA = (-5.5, -81.5)


def por_region(region: str) -> list[Zona]:
    return [z for z in ZONAS if z.region == region]
