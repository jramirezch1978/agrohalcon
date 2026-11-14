# Base de datos (PostgreSQL) · lo que toca a la parte de Python

El dueño de la base de datos del VPS y del DDL oficial es **Jhonny** (`04. base de datos/ddl/`). David entrega, listo para usar: el **esquema** (`db/postgres/01_schema.sql`), las **semillas** (`db/postgres/seed/`) y los **datos de respaldo**.
El servicio Python **no se conecta a la base de datos** (contrato). La base existe para: el Plan B de la demo, los análisis, la validación 2017 y el panel.

## Un esquema, dos motores

[`db/schema.py`](../db/schema.py) (SQLAlchemy Core) genera SQLite (`data/agroshift.sqlite`, para trabajar sin Docker) y SQL de PostgreSQL (tipos `JSONB`, `BIGSERIAL`, vistas `CREATE OR REPLACE VIEW`).
No había PostgreSQL ni Docker en la PC de David, así que el SQL se comprobó de tres formas: con **sqlglot** (gramática de PostgreSQL), en SQLite con claves foráneas activas y, sobre todo, contra un **PostgreSQL 16.2 real embebido** (`pgserver`): `python -m db.probar_postgres`
ejecuta `01_schema.sql`, carga **todas** las semillas (164 mil observaciones, JSONB, booleanos, fechas), compara los conteos de cada tabla con SQLite y consulta las vistas. Resultado del 14-nov: **todo coincide**. Jhonny solo debe repetirlo en su servidor.

```powershell
python -m db.build              # SQLite desde la caché de descargas (python -m etl.jobs ...)
python -m db.export_postgres    # db/postgres/01_schema.sql + 02_seed.sql + seed/*.csv
```
Cargar en PostgreSQL (Jhonny): `psql -d agroshift -f db/postgres/01_schema.sql`, luego, **desde `db/postgres/`**: `gunzip -k seed/observacion.csv.gz` y `psql -d agroshift -f 02_seed.sql`.

## Modelo (estrella)

| Tabla | Tipo | Contenido |
|---|---|---|
| `region`, `zona` | dimensión | 7 regiones del norte + mar; 16 valles agrícolas + 2 puntos de mar. `zona` trae elevación y pendiente (SRTM) y suelo (SoilGrids) |
| `fuente_dato`, `variable` | dimensión | 16 fuentes con **versión, DOI y estado** (`en_uso / probado / bloqueado / planeado`) y 15 variables con su unidad |
| `cultivo`, `rotacion` | dimensión | el catálogo de Alejandro (`es_prueba` = 1 mientras sea el de prueba) y todas las parejas con ids estables |
| `observacion` | hecho | zona · fecha · escala (`diaria / mensual / compuesta16d`) · variable · valor · calidad (única por combinación) |
| `normal_mensual` | hecho | media y desviación 1991-2020 por zona, variable y mes |
| `indice_climatico`, `episodio_calido` | hecho | ONI y Niño 1+2/3/3.4/4 (valor y anomalía) desde 1982; episodios calculados (≥ +1,0 °C, ≥ 3 meses) |
| `sst_clima` | hecho | climatología de MUR SST por día del año (2003-2022) |
| `tendencia`, `composite_nino` | hecho | Mann-Kendall + Sen por zona y variable · lluvia en años Niño vs normales |
| `validacion_quincena` | hecho | qué habría dicho AgroShift cada quincena de ene-abr 2017, por zona (entrada, indicadores, nivel máximo) |
| `recomendacion_cache` | hecho | el estado de hoy por zona (Plan B si falla internet) |
| `consulta` | contrato | historial de consultas de la API |

Vistas: **`v_datos_nasa`** (= tabla `datosNasa` del contrato: `id, lat, lon, fecha, fuente, variable, valor`), `v_anomalia_mensual` (valor, normal y puntaje z), `v_ultimo_dato`, `v_validacion_resumen`.

## Consultas útiles
```sql
-- ¿Cuántas veces más llovió en marzo de 2017 que lo normal, por valle?
SELECT z.nombre, a.valor AS mm_dia, a.normal, ROUND(a.z, 1) AS z
FROM v_anomalia_mensual a JOIN zona z ON z.id = a.zona_id JOIN variable v ON v.id = a.variable_id
WHERE v.codigo = 'PRECTOTCORR' AND a.fecha = '2017-03-01' ORDER BY a.z DESC;

-- ¿Qué fuentes están realmente en uso?
SELECT codigo, producto, version, estado FROM fuente_dato ORDER BY estado, codigo;

-- Primera quincena de 2017 con alerta alta, por valle
SELECT zona, MIN(hasta) AS primera_alerta_alta FROM v_validacion_resumen WHERE nivel_maximo = 'alto' GROUP BY zona;
```

## El esquema oficial es el de Jhonny: `agro`, `nasa`, `ref`

Hay dos esquemas de PostgreSQL. El de David (`db/postgres/01_schema.sql`, en estrella) sirve para trabajar sin Docker y para el panel. **El que lee y graba Java es el de Jhonny** (`04. base de datos/ddl/00-schema.sql`).
Sus zonas 1-16 tienen los mismos ids que los valles de David, así que los datos se pueden pasar sin traducir ids. `db/export_allpashift.py` lo hace:

```powershell
python -m db.build                # arma data/agroshift.sqlite (incluye los aportes de Sheila)
python -m db.export_allpashift    # escribe 04. base de datos/ddl/seed/02-datos-nasa.sql (1,3 MB)
python -m db.probar_allpashift    # 00-schema + 01-catalogo-norte + 02-datos-nasa en un PostgreSQL 16.2 real, dos veces
```

| Tabla del equipo | Qué recibe | Filas |
|---|---|---|
| `nasa.datos_nasa` | POWER (2017 y últimos 60 días), SMAP, NDVI VIIRS, MUR SST, IMERG; `variable` = `NOMBRE_NASA:campoContrato` (+ `:mensual` o `:16d` si no es diaria) | 18 818 |
| `nasa.normales` | normal mensual por valle: POWER 1991-2020 (lluvia, humedad, Tmax, Tmin) e IMERG 2001-2020 | 840 |
| `nasa.datasets` | suma `VNP13A1` (el NDVI que se usa es de VIIRS, no de MODIS) | 1 |

Reglas: el SQL es autocontenido (`COPY … FROM STDIN` en una tabla temporal y `INSERT … WHERE NOT EXISTS`), así que **correrlo dos veces no duplica**; los valles sin id en `agro.zonas` quedan con `zona_id` NULL (se identifican por lat/lon);
el NDVI se rotula `VIIRS NDVI`, nunca `MODIS`. `database-deploy.bat` todavía ejecuta solo `01-catalogo-norte.sql`: ver `REVISION_CALCULOS_SHEILA.md`, sección 6.

### Aportes de Sheila (`db/aportes.py`)

Lee `calculos/data/precalculado/{imerg_piura,mur_sst_nino12}.json` (o `02. backend/python/calculos/…`, o la copia `data/backup/sheila/`, o la carpeta de `CALCULOS_PRECALCULADO`) y agrega:
GPM IMERG V07 de 12 puntos de Piura (mensual Final 2001-2025 y diario Late de 45 días, en mm/día, con su normal 2001-2020), la serie semanal MUR SST de la caja Niño 1+2 (`indice_climatico`: `MUR_NINO12`, `MUR_NINO12_ANOM`)
y la tabla **`contraste_fuentes`** (correlación, sesgo y RMSE entre fuentes independientes). Los puntos a menos de 5 km de un valle se asignan a él; los otros 6 son zonas `referencia` (ids 201-206).

```sql
-- ¿Qué tanto coinciden las fuentes?
SELECT par, z.nombre AS valle, variable, n, correlacion, sesgo_medio
FROM contraste_fuentes c LEFT JOIN zona z ON z.id = c.zona_id ORDER BY par, correlacion DESC;
```

## Regla de honestidad
`fuente_dato.estado` solo dice `en_uso` si hay datos reales de esa fuente en `observacion` (lo decide `db/build.py` mirando la caché). Lo que no esté en uso debe presentarse como *planned* en la entrega.
