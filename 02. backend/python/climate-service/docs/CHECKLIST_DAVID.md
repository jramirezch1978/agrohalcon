# Checklist de David (Python + datos NASA)

Estado al **14-nov-2026**, tarde. Marca lo que vayas haciendo.

## A. Ya está listo en tu PC (lo hizo Claude Code)
- [x] Repo clonado en `D:\NASA SPACE APPS\AgroShift`, rama `feature/datos-python` (con permiso de escritura en `jramirezch1978/agrohalcon`).
- [x] Entorno Python 3.11 en `climate-service/.venv` con todas las librerías. VS Code abierto en el proyecto.
- [x] **Token de Earthdata** guardado en `climate-service/.env` (ignorado por git; vence el **2027-01-13**). Verificado contra NSIDC, LP DAAC y PO.DAAC.
- [x] Servicio `/salud`, `/indicadores`, `/rotaciones`, `/recomendacion` + asistente con guardas (`/asistente/*`) + incertidumbre opcional. ~120 pruebas en verde.
- [x] **Base de datos** (SQLite + SQL de PostgreSQL) con POWER (16 valles, 1981-hoy), Niño 1+2/3.4/ONI, MUR SST, SRTM, SoilGrids, tendencias, validación 2017 y estado de hoy.
- [x] **Panel técnico** en http://localhost:8000/panel/ y **4 agentes + 4 comandos** de Claude Code en `.claude/`.

## B. Lo que SOLO puedes hacer tú
1. ⛔ **Aceptar el acuerdo de GES DISC** (desbloquea IMERG y GLDAS; 1 clic con la sesión de Earthdata iniciada):
   https://urs.earthdata.nasa.gov/approve_app?client_id=e2WVk8Pw6weeLUKZYOxvTQ → *Approve*. Luego: `python -m etl.jobs imerg` y `python -m db.build`.
2. 🔐 **El token quedó escrito en un chat.** Al terminar el hackatón (o ya, si prefieres): Earthdata → *My Profile → Generate Token* → *Revoke* el anterior y pega el nuevo en `.env`. Nunca lo pegues en el repo ni en capturas.
3. **Decidir el nombre** con el equipo: la web en línea dice **AllpaShift**, el repo **agrohalcon**, tú elegiste **AgroShift**.
4. **Aceptar la invitación al repo** si GitHub la pide: https://github.com/jramirezch1978/agrohalcon
5. *(Opcional)* Cuenta en AppEEARS: **no hace falta** (acepta solo usuario/clave, no el token); SMAP, VIIRS, SRTM y MUR ya se leen directo con el token.

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
Después: Pull Request `feature/datos-python → develop` (`gh pr create --base develop`). Jhonny pasa `develop` a `main`. Si `develop` cambió: `git fetch origin && git merge origin/develop` antes del PR.

## D. Comandos del día
```powershell
cd "02. backend\python\climate-service"; .venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000     # servicio + panel en /panel/
python -m etl.jobs power nino mur srtm        # descargas (usa el token)
python -m db.build; python -m db.export_panel # base y panel
claude                                        # agentes y /comandos
```

## E. Tu lista de tareas
- [ ] **Primera hora (todos juntos):** aprobar el contrato. Llevar [`DECISIONES_ABIERTAS.md`](DECISIONES_ABIERTAS.md) (campos extra, asistente, nombre).
- [x] `/indicadores` y `/rotaciones` con los ejemplos del contrato · [x] datos reales de Piura · [x] validación Niño costero 2017 (con la señal del mar).
- [ ] Conectar con Jhonny: `POST /recomendacion` y la secuencia del asistente (prompt 11).
- [ ] **Catálogo de Alejandro** → `python -m db.build --catalogo <ruta>` (prompt 5).
- [ ] IMERG tras aceptar el acuerdo (prompt 1) · SMAP como fuente real de humedad (prompt 2).
- [ ] Diapositiva de **Impacto** con la validación 2017 (prompt 4) · **tabla de datasets NASA en inglés** (prompt 10).
- [ ] Completar en *Use of AI* la fila de **Claude Code** ([`USO_DE_IA.md`](USO_DE_IA.md)) y declarar que **NOAA CPC y SoilGrids no son NASA** y que **VIIRS reemplaza a MODIS**.
- [ ] Domingo 12:00 congelar funcionalidades · 15:00 `auditor-de-entrega` · **20:00 último merge y Submit** · después de las 23:59 no se toca el repo.

## F. Lo que debes tener claro para el jurado
- Python **no** calcula con IA: son reglas verificables (`app/thresholds.py`). La IA solo redacta, y sus respuestas pasan por `asistente.validar_respuesta()` (nada de números ni cultivos inventados).
- Lo sugerido por una IA debe ser **revisado y validado por ti**: lee el código, corre las pruebas y los datos reales antes de subirlo.
- La herramienta **apoya, no reemplaza** al agricultor ni al técnico: ya lo dice cuando todo es riesgo alto o hay una señal de El Niño extraordinaria.
- Lo que está `planeado` o `bloqueado` en la tabla `fuente_dato` se presenta como *planned* en la entrega.
