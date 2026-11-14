"""Escribe data/backup/zonas_seed.sql: los valles del norte para la tabla `zonas` del contrato.

    python -m etl.export_zonas_sql

No necesita internet. Las coordenadas son aproximadas (Alejandro las valida). Nombres de columnas en snake_case:
si Jhonny usa otro estilo, es un buscar-y-reemplazar.
"""

from .config import BACKUP
from .zonas import ZONAS


def sql() -> str:
    filas = ",\n".join(
        f"  ({z.id}, '{z.nombre.replace(chr(39), chr(39) * 2)}', {z.lat}, {z.lon}, '{z.region}')" for z in ZONAS
    )
    return (
        "-- Semilla de la tabla zonas (AgroShift). Coordenadas aproximadas: validar con el catálogo.\n"
        "INSERT INTO zonas (id, nombre, lat, lon, region) VALUES\n"
        f"{filas}\n"
        "ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre, lat = EXCLUDED.lat, lon = EXCLUDED.lon, region = EXCLUDED.region;\n"
    )


def main() -> None:
    BACKUP.mkdir(parents=True, exist_ok=True)
    (BACKUP / "zonas_seed.sql").write_text(sql(), encoding="utf-8")
    print(f"Escrito {BACKUP / 'zonas_seed.sql'} ({len(ZONAS)} zonas)")


if __name__ == "__main__":
    main()
