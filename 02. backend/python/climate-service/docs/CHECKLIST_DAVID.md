# Checklist de David (Python + datos NASA)

Estado al **14-nov-2026**. Marca lo que vayas haciendo.

## A. Ya está listo en tu PC (lo hizo Claude Code)
- [x] Repo clonado en `D:\NASA SPACE APPS\AgroShift` (remoto `jramirezch1978/agrohalcon`, tienes permiso de escritura).
- [x] Rama `feature/datos-python` activa, con seguimiento de `origin/feature/datos-python`.
- [x] Git con tu nombre/correo y `gh` con sesión iniciada.
- [x] Entorno Python 3.11 en `climate-service/.venv` con todas las librerías (FastAPI, pandas, scipy, pymannkendall, earthaccess…).
- [x] Servicio `/salud`, `/indicadores`, `/rotaciones` (+ `/recomendacion`) con 65 pruebas en verde.
- [x] Scripts de NASA POWER, CMR/versiones, ONI, respaldo y validación 2017.
- [x] VS Code ya tiene Python, Pylance, Jupyter y Claude Code (no hace falta instalar nada).

## B. Lo que SOLO puedes hacer tú (necesitan tu cuenta)
1. **Cuenta NASA Earthdata** (gratis, ~3 min): https://urs.earthdata.nasa.gov/users/new
   (Jhonny ya creó la suya; la tuya figura como pendiente.)
2. **Generar el token**: inicia sesión → tu nombre arriba a la derecha → *My Profile* → **Generate Token**.
   Pégalo en `climate-service/.env` como `EARTHDATA_TOKEN=...` (copia antes `env.example` a `.env`).
   ⚠️ No lo pegues en el chat, en capturas ni en el repo. El token vence (~60 días): se vuelve a generar.
3. **Autorizar aplicaciones** (si no, las descargas dan 401/403): Earthdata → *Applications → Authorized Apps → Approve More Applications*:
   **NASA GESDISC DATA ARCHIVE** (IMERG, GLDAS), **LP DAAC Data Pool** (MODIS, ECOSTRESS), **NSIDC DAAC** / **NSIDC_DATAPOOL_OPS** (SMAP).
4. **AppEEARS** (recomendado para SMAP/MODIS por punto): https://appeears.earthdatacloud.nasa.gov/ → *Sign in* con Earthdata
   y acepta los términos. Para usar su API desde Python pon también `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` en `.env` (solo tu `.env` local).
5. **Aceptar la invitación al repo** si GitHub la pide: https://github.com/jramirezch1978/agrohalcon

## C. Flujo de Git (cada vez)
```powershell
cd "D:\NASA SPACE APPS\AgroShift"
git checkout feature/datos-python
git pull origin feature/datos-python         # trae lo que haya
# ...trabaja, y antes de commitear:
cd "02. backend\python\climate-service"; pytest; ruff check .; cd ..\..\..
git add "02. backend/python/climate-service"
git commit -m "feat(indicadores): descripción corta"
git push origin feature/datos-python         # tu rama; NUNCA a main
```
Después: Pull Request `feature/datos-python → develop` (`gh pr create --base develop`). Jhonny pasa `develop` a `main`.
Si Jhonny cambió `develop`: `git fetch origin && git merge origin/develop` en tu rama antes del PR.

## D. Tu lista de tareas (del plan del equipo y del contrato)
- [ ] **Primera hora (todos juntos):** aprobar el contrato. Llevar [`DECISIONES_ABIERTAS.md`](DECISIONES_ABIERTAS.md).
- [x] `/indicadores` y `/rotaciones` con los ejemplos de entrada del contrato.
- [ ] Conectar con Jhonny: él llama a `/recomendacion` (o a `/indicadores` + `/rotaciones`); probar con `curl` y con su API.
- [ ] Recibir el **catálogo de Alejandro** (JSON con los campos de la tabla `cultivos`) y correr `pytest` + `build_backup --catalogo`.
- [ ] Descargar antes de la demo: **SMAP, GPM IMERG, MODIS NDVI, MUR SST** (David, según el contrato) y guardarlos en la base de datos.
- [ ] Validación **Niño costero 2017** (diapositiva de Impacto con Alejandro).
- [ ] **Tabla de datasets NASA** (campo *Use of AI / NASA Data*): ver prompt 11.
- [ ] Completar en *Use of AI* la fila de **Claude Code** (ver [`USO_DE_IA.md`](USO_DE_IA.md)).
- [ ] Domingo 12:00 congelar funcionalidades · **20:00 último merge y Submit** · después de las 23:59 no se toca el repo.

## E. Cosas que debes tener claras para el jurado
- Python **no** calcula con IA: son reglas verificables (`app/thresholds.py`).
- Lo que sugiere una herramienta de IA debe ser **revisado y validado por ti**: lee el código y corre las pruebas antes de subirlo.
- La herramienta **apoya**, no reemplaza al agricultor ni al técnico: el servicio ya lo dice cuando todo es riesgo alto.
