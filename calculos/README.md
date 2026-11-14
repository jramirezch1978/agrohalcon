# AgroShift – Servicio de cálculos (Python)

Calcula indicadores de riesgo climático con datos de la NASA. Reglas simples y explicables, sin IA.
Lo llama la API en Java (no la app).

## Correr (Windows / PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8001
.\.venv\Scripts\python -m pytest -q
```

Documentación interactiva: http://localhost:8001/docs

## Ejemplos

```bash
curl http://localhost:8001/salud
curl -X POST http://localhost:8001/calcular -H "Content-Type: application/json" \
  -d '{"lat":-5.19,"lon":-80.63,"lang":"es","tipoCultivo":"temporal","mesSiembra":"2026-12"}'
```

## Datos precalculados (Piura / El Niño)

El servicio solo lee `data/precalculado/*.json`. Si un archivo falta, el indicador dice `"fuente": "sin dato"`.

```powershell
# MUR SST, caja Niño 1+2 (sin cuenta, vía ERDDAP). Primera vez: ~15-20 min, JSON de ~40 KB.
.\.venv\Scripts\python -m scripts.descargar_mur_sst
# Antes de la demo: solo los 2 últimos meses (~30 s)
.\.venv\Scripts\python -m scripts.descargar_mur_sst --actualizar
# GPM IMERG, puntos de Piura (requiere cuenta Earthdata + app "NASA GESDISC DATA ARCHIVE" autorizada)
.\.venv\Scripts\python -m pip install -r requirements-scripts.txt
.\.venv\Scripts\python -m scripts.descargar_imerg               # ~2 min, JSON de ~30 KB
.\.venv\Scripts\python -m scripts.descargar_imerg --actualizar  # antes de la demo: últimos 45 días
# Revisar a mano el caso 2017
.\.venv\Scripts\python -m scripts.verificar_2017
```

## References

- **MUR SST v4.1.** JPL MUR MEaSUREs Project (2015). *GHRSST Level 4 MUR Global Foundation Sea Surface
  Temperature Analysis (v4.1).* NASA PO.DAAC. doi:10.5067/GHGMR-4FJ04. Variable `analysed_sst` (°C). Anomalía:
  `sstAnom` (°C, frente a la climatología JPL MUR 2003-2014, producto de NOAA ERD). Accedido vía ERDDAP de
  NOAA CoastWatch: https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.html y
  https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41anom1day.html. Promedio semanal de la caja
  Niño 1+2 (0°-10° S, 90°-80° O) a 0.25°, ponderado por cos(lat).
- **GPM IMERG V07.** Huffman, G.J., et al. (2023). *GPM IMERG Final Precipitation L3 1 month 0.1° x 0.1° V07*
  (GPM_3IMERGM), doi:10.5067/GPM/IMERG/3B-MONTH/07, y *GPM IMERG Late Precipitation L3 1 day 0.1° x 0.1° V07*
  (GPM_3IMERGDL), doi:10.5067/GPM/IMERGDL/DAY/07. NASA GES DISC, accedido por OPeNDAP de NASA Earthdata.
  Variable `precipitation` (mensual en mm/hr → mm/mes; diario en mm/día). Celda de 0.1° más cercana a cada
  punto de Piura; normal = media 2001-2020 del Final mensual. El Final termina en 2025-09, por eso los
  últimos 30 días usan el Late (sin corrección con pluviómetros).
- **NASA POWER.** NASA Langley Research Center, POWER Project, API v2.10, comunidad AG:
  https://power.larc.nasa.gov/. Parámetros PRECTOTCORR, GWETTOP, T2M_MAX; climatología 2001-2025.

## Método (fase 1)

| Indicador | Actual (últimos 30 días) | Normal (climatología 2001-2025) | Nivel |
|---|---|---|---|
| lluvia | media de `PRECTOTCORR` | `PRECTOTCORR` del mes | \|anomalía %\| 20 / 40; sin señal si ambos < 1 mm/día |
| humedadSuelo | media de `GWETTOP` | `GWETTOP` del mes | solo el déficit %: 20 / 40 |
| calor | media de `T2M_MAX` | media de `T2M_MAX` diario en los mismos días, 2001-2025 | +1.5 / +3 °C |
| elNino | MUR SST Niño 1+2 (fase 3) | 0 | +0.5 / +1.5 °C |

- Si la ventana cruza dos meses, la normal se pondera por días.
- `T2M_MAX` climatológico de POWER es el **extremo** del mes y `T2M_MAX_AVG` el **promedio de esos extremos**
  (Iowa, octubre: 27.1 °C vs 17.2 °C de máxima diaria media). Por eso la normal del calor se calcula con la serie diaria.
- `GWETTOP` es una fracción de saturación (0-1), no m³/m³ como SMAP.
- Los umbrales están en `config/umbrales.yaml`; los marcados "supuesto" son decisiones del equipo.
