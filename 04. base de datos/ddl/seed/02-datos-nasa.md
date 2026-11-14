# `02-datos-nasa.sql` · datos NASA reales para el esquema `nasa`

Generado por David (`python -m db.export_allpashift`, en `02. backend/python/climate-service`). **No editar a mano**: se regenera con los datos nuevos.

| Carga | Filas | Detalle |
|---|---|---|
| `nasa.datos_nasa` | 18 818 | NASA POWER (2017 y últimos 60 días), SMAP v006, NDVI **VIIRS** VNP13A1 v002, MUR SST v4.1 (mar frente a Piura y Paita), GPM IMERG V07 (6 valles, 2001-2025) |
| `nasa.normales` | 840 | normal mensual por valle: POWER 1991-2020 (lluvia, humedad, Tmax, Tmin) e IMERG 2001-2020 |
| `nasa.datasets` | 1 | `VNP13A1` (el NDVI que usa AllpaShift; MODIS MOD13Q1 no se pudo leer) |

- **Orden:** `00-schema.sql` → `01-catalogo-norte.sql` (necesita `agro.zonas`) → este archivo.
- **Se puede ejecutar varias veces sin duplicar.**
- **Cómo cargarlo:** `psql -U <usuario> -d allpashift -v ON_ERROR_STOP=1 < "04. base de datos/ddl/seed/02-datos-nasa.sql"`.
  `database-deploy.bat seed` solo ejecuta `01-catalogo-norte.sql`; para incluir este archivo, agregar `call :run_sql "seed\02-datos-nasa.sql" || goto :fail` después de cada línea de `01-catalogo-norte.sql` (rutas `create` y `seed`).
- **Convención de `variable`:** `NOMBRE_NASA:campoContrato`, más `:mensual` o `:16d` si el dato no es diario (ej.: `PRECTOTCORR:lluviaMm`, `precipitation:lluviaMm:mensual`, `NDVI:ndvi:16d`).
- **Probado** en PostgreSQL 16.2 real (`python -m db.probar_allpashift`): ejecuta los tres archivos con psql por stdin, como `database-deploy.bat`, dos veces, sin duplicar y sin datos huérfanos.
- **Fuentes:** IMERG y la caja Niño 1+2 de MUR los bajó **Sheila** (rama `feature/calculos-sheila`); el resto lo bajó David. El NDVI es de VIIRS: en *References* no se debe escribir MODIS.
