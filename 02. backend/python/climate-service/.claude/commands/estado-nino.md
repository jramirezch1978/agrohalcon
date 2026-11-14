---
description: Estado actual de El Niño costero y de las 16 zonas, con datos reales de la base
allowed-tools: Bash(python -m db.build:*), Read
---

Consulta `data/agroshift.sqlite` (si no existe o es de otro día, corre `python -m db.build`). Reporta, con cifras y fechas:
1. Última anomalía de Niño 1+2 y Niño 3.4 (tabla `indice_climatico`) y el último ONI; compáralos con los episodios de la tabla `episodio_calido`.
2. SST de MUR frente a Piura y su anomalía (`observacion`, variables `MUR_SST` y `MUR_SST_ANOM`) y por qué difiere del índice mensual de NOAA.
3. Cuántas zonas están en nivel alto hoy (`recomendacion_cache`) y las 3 con más lluvia sobre lo normal.
4. Un párrafo de 3 frases para un agricultor, sin jerga, y otro para el jurado, sin exagerar.
Aclara siempre qué datos son de la NASA y cuáles de NOAA, y recuerda contrastar con SENAMHI/ENFEN antes de la demo. $ARGUMENTS
