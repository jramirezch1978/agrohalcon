# Base de datos (PostgreSQL) · lo que toca a la parte de Python

El dueño de la base de datos y del DDL es **Jhonny** (`04. base de datos/ddl/`). El servidor es el VPS de Hetzner con Docker
(doc `22_servidores_despliegue.md`). **El servicio Python no se conecta a la base de datos** (contrato): solo entrega
datos de respaldo y recibe lo que Java le manda. Esto es lo que David le pasa a Jhonny.

## Tablas del contrato (PDF *Contrato del backend*, p. 4)

| Tabla | Campos principales | Quién la llena |
|---|---|---|
| `cultivos` | id, nombre, tempMinC, tempMaxC, aguaNecesaria (baja/media/alta), mesesSiembra, mesesCosecha, accionesPorEtapa | Alejandro (JSON) |
| `rotaciones` | id, nombre, cultivo1Id, cultivo2Id | Alejandro / Jhonny |
| `zonas` | id, nombre, lat, lon, region | **David** → `data/backup/zonas_seed.sql` |
| `datosNasa` | id, lat, lon, fecha, fuente, variable, valor | **David** → `data/backup/datos_nasa_respaldo.csv` |
| `consultas` | id, lat, lon, fecha, rotacionRecomendadaId | Java (historial de consultas) |

## Archivos que genera David (`python -m etl.build_backup`, `python -m etl.export_zonas_sql`)

| Archivo (`data/backup/`) | Para qué | Quién lo usa |
|---|---|---|
| `zonas_seed.sql` | 16 valles del norte (coordenadas **aproximadas**: Alejandro valida) | Jhonny: carga en `zonas` |
| `datos_nasa_respaldo.csv` | NASA POWER mensual 2016-2017 y del año en curso por zona (columnas `lat,lon,fecha,fuente,variable,valor`) | Jhonny: carga en `datosNasa` (Plan B sin internet) |
| `validacion_2017.json` | Qué habría dicho AgroShift cada quincena de ene-abr 2017, por zona | Jhonny: `/api/validacion?anio=2017`; Alejandro: diapositiva de Impacto |
| `actual.json` | La entrada y el resultado de hoy por zona | Plan B de `/api/mapa` y `/api/recomendacion` |
| `normales_power_1991_2020.json` | Normal histórico por mes y zona | Java, si prefiere no volver a pedirlo a POWER |
| `versiones_datasets.json` | Versión exacta y DOI de cada dataset | Edwin / References |

## Cargar `datosNasa` (ejemplo para Jhonny)

Nombres en snake_case (Spring/JPA los suele mapear así); ajustar si el DDL real usa otros.

```sql
CREATE TABLE IF NOT EXISTS datos_nasa (
  id        BIGSERIAL PRIMARY KEY,
  lat       DOUBLE PRECISION NOT NULL,
  lon       DOUBLE PRECISION NOT NULL,
  fecha     DATE NOT NULL,            -- primer día del mes (valores mensuales) o el día (valores diarios)
  fuente    TEXT NOT NULL,            -- 'NASA POWER', 'SMAP', 'GPM IMERG', 'MODIS NDVI', 'MUR SST'
  variable  TEXT NOT NULL,            -- p. ej. 'PRECTOTCORR:lluviaMm'
  valor     DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_datos_nasa_punto_fecha ON datos_nasa (lat, lon, fecha);

-- desde psql, estando en la carpeta data/backup:
\copy datos_nasa (lat, lon, fecha, fuente, variable, valor) FROM 'datos_nasa_respaldo.csv' WITH (FORMAT csv, HEADER true)
```

La columna `variable` lleva `NOMBRE_NASA:campoDelContrato` (p. ej. `GWETTOP:humedadSuelo`, `PRECTOTCORR:lluviaMm`, `T2M_MAX:tempMaxC`)
para poder reconstruir el cuerpo de `POST /indicadores` desde la base.

## Qué guardar cuando estén SMAP, IMERG, MODIS y MUR SST
Mismo formato, una fila por punto, fecha y variable, con `fuente` real (`SMAP`, `GPM IMERG`, `MODIS NDVI`, `MUR SST`) y la **versión** en el nombre
de la variable o en una columna nueva (`version`). Así la app puede decir *“humedad del suelo 40 % por debajo de lo normal (SMAP v006)”* con respaldo.

## Opciones de alojamiento (por si cambia el plan)
Hetzner VPS + PostgreSQL en Docker (decidido) · alternativa gratis: Neon (PostgreSQL serverless) · PostGIS es opcional (solo si se hacen consultas por polígono).
