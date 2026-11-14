# AgroShift · climate-service (contexto para Claude Code)

Proyecto: **AgroShift** (nombre final; el repo y algunos textos aún dicen "AgroHalcón"). NASA Space Apps Challenge 2026,
sede Piura, reto *Field Shift: Adapting Farms with NASA Data*. Equipo **Halcón Dorado**. Idioma del equipo: español
(la entrega a NASA es en inglés: la redacta Edwin).

Este directorio es el **servicio de cálculo en Python** (FastAPI). Dueño: David, rama `feature/datos-python`.

## Reglas que no se rompen
1. **Contrato del backend**: JSON en **camelCase**, fechas `YYYY-MM-DD`, coordenadas en grados decimales, unidades en el
   nombre del campo (`lluviaMm`). **Nadie cambia ni quita un campo sin avisar al equipo.** Agregar campos opcionales sí se puede,
   y hay que anotarlo en `docs/DECISIONES_ABIERTAS.md`.
2. **Python consulta la NASA y calcula; nunca toca la base de datos** (decisión de Jhonny, 14-nov, `01. documentacion/29_arquitectura_reglas.md`). Las descargas en línea viven en `app/nasa_cliente.py` y los endpoints para Java en `app/allpashift_api.py` (`/calcular`, `/indicadores-punto`, `/validacion`). Java es la única que lee y graba PostgreSQL. `db/` queda solo para pruebas locales.
3. **Cero IA en los cálculos.** Indicadores, puntajes y recomendaciones salen de reglas verificables con números en
   `app/thresholds.py`. La IA (Groq, `openai/gpt-oss-20b`, Apache 2.0) solo redacta y se llama desde este servicio (`app/groq_cliente.py`): la clave `GROQ_API_KEY` vive solo en el servidor.
4. **Transparencia**: cada resultado muestra el dato que lo respalda y su fuente real. Si un dato viene de respaldo (p. ej. POWER en vez
   de SMAP), se declara en `meta`; nunca se escribe "SMAP" si no es SMAP.
5. **Nunca subir secretos**: `.env`, tokens, claves. Nunca subir `data/raw/` (descargas pesadas).
6. Toda regla nueva lleva su prueba en `tests/`. Antes de commitear: `pytest` y `ruff check .`.

## Comandos
```powershell
.venv\Scripts\Activate.ps1
pytest                      # sin internet (~120 pruebas)
pytest -m live              # con internet: NASA POWER, CMR, ONI
ruff check --fix .
uvicorn app.main:app --reload --port 8000
python -m etl.build_backup  # datos de respaldo + validación 2017
```
Python **3.11** (venv en `.venv`). El 3.14 del sistema no se usa.

## Mapa del código
- `app/schemas.py` contrato (Pydantic) · `app/indicators.py` 4 indicadores · `app/rotations.py` puntaje ·
  `app/que_hacer.py` acción/motivo/fuente · `app/thresholds.py` TODOS los umbrales y pesos · `app/main.py` endpoints.
- `etl/` descargas y armado de entradas (`inputs.py`), respaldo y validación 2017 (`build_backup.py`).
- `samples/` ejemplos del contrato. El catálogo de ahí es **de prueba**; el real es de Alejandro (`data/crops/`).

## Datos y bases de datos (`etl/` y `db/`)
- `python -m etl.jobs <power|nino|mur|mur-clima|smap|smap-clima|srtm|ndvi|suelos|imerg>` → caché `data/raw/cache`; `python -m db.build` → `data/agroshift.sqlite`;
  `python -m db.export_postgres` (SQL de PostgreSQL) y `python -m db.export_panel` (panel en `/panel/`).
- El token `EARTHDATA_TOKEN` está en `.env`: **nunca** leerlo, imprimirlo ni copiarlo. El código lo carga con `python-dotenv`.
- Aportes de Sheila (`calculos/data/precalculado/` o `02. backend/python/calculos/data/precalculado/`, copia en `data/backup/sheila/`): IMERG y MUR Niño 1+2 → `db/aportes.py` (tablas `observacion`, `normal_mensual`, `indice_climatico`, `contraste_fuentes`). Revisión completa en `docs/REVISION_CALCULOS_SHEILA.md`.
- La base de Java es la de Jhonny (`04. base de datos/ddl/00-schema.sql`): `python -m db.export_allpashift` genera `seed/02-datos-nasa.sql` y `python -m db.probar_allpashift` lo prueba en PostgreSQL 16.2 real.
- Respaldo de El Niño (`app/datos_respaldo/`): se regenera con `python -m etl.respaldo_validacion` (serie MUR semanal, NOAA CPC mensual e IMERG de Piura); el respaldo de El Niño vence a los 21 días (última semana: 2026-11-09).
- `fuente_dato.estado` solo es `en_uso` si hay datos reales de esa fuente. Lo demás se presenta como *planned* en la entrega.
- Agentes (`.claude/agents/`): ingeniero-datos-nasa, guardian-del-contrato, revisor-agronomico, auditor-de-entrega. Comandos: /probar, /base-de-datos, /estado-nino, /revisar-contrato.

## Estado honesto (14-nov-2026)
- ✅ Probado con datos reales: NASA POWER, NOAA Niño 1+2/ONI, MUR SST (OPeNDAP de PO.DAAC), SRTM, SoilGrids (parcial), CMR, validación 2017, base de datos, panel.
- ⏳ SMAP y VIIRS NDVI: se leen del HDF5 remoto; mira `fuente_dato.estado` para saber si ya están ingeridos.
- ⛔ IMERG y GLDAS: bloqueados hasta que David acepte el acuerdo de GES DISC (`403 EULA Acceptance Failure`). ECOSTRESS: planeado.
- ✅ SQL de PostgreSQL verificado contra un PostgreSQL 16.2 real embebido (`python -m db.probar_postgres`, `pytest -m postgres`); falta repetirlo en el servidor de Jhonny.
- ❌ Sin probar: Dockerfile (no hay Docker), asistente contra Groq real (no hay `GROQ_API_KEY`; el cliente, las guardas y los límites sí tienen pruebas con un transporte simulado), IMERG (bloqueado por el acuerdo de GES DISC).
- La señal de El Niño del servicio es el **índice Niño 1+2 de NOAA CPC** (no NASA); MUR SST da el valor y una anomalía propia. El NDVI es de **VIIRS** (el PDF dice MODIS).
- POWER `T2M_MAX` en Piura da ~37-39 °C en marzo (parece sesgado al calor): compárense solo anomalías. Ver `docs/DECISIONES_ABIERTAS.md`.

## Git
Trabajar en `feature/datos-python` → Pull Request a `develop` → Jhonny pasa a `main`. Commits pequeños en español, p. ej.
`feat(indicadores): ...`, `fix(rotaciones): ...`, `data(respaldo): ...`. No hacer push a `main`.
