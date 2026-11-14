---
description: Reconstruye la base de datos desde la caché y exporta PostgreSQL y el panel
allowed-tools: Bash(python -m db.build:*), Bash(python -m db.export_postgres), Bash(python -m db.export_panel), Bash(pytest:*), Read
---

Ejecuta en orden: `python -m db.build`, `python -m db.export_postgres`, `python -m db.export_panel` y `pytest`.
Resume: filas por tabla, qué fuentes quedaron `en_uso` y cuáles `bloqueado`/`probado` (mira `fuente_dato.estado`), violaciones de claves foráneas (debe ser 0) y cualquier advertencia. Si falta una caché (SMAP, NDVI, IMERG), dime qué comando de `python -m etl.jobs ...` la genera. $ARGUMENTS
