# Arquitectura y reglas de AllpaShift (obligatorias)

> Decisión de Jhonny (líder), 2026-11-14. Todo diseño y desarrollo debe cumplir estas reglas.
> Diagrama: `01. documentacion/img/arquitectura_allpashift.png`.

![Arquitectura](img/arquitectura_allpashift.png)

## Reglas

1. **Web y móvil SOLO hablan con la API Java** (`/api/...` a través del api-gateway). Nunca llaman directo a Python, a la NASA ni a la base de datos.
2. **Java (agro-service) es la ÚNICA que lee y graba en PostgreSQL.**
3. **Python (climate-service) SOLO consulta las APIs de la NASA y calcula.** Nunca lee ni graba en la base de datos.
4. **El token de Earthdata vive solo en Python** (`EARTHDATA_TOKEN`). Java no lo necesita.
5. **Primero la base de datos:** si el dato está fresco en PostgreSQL, Java responde desde ahí y no vuelve a pedirlo. Así la demo funciona aunque la NASA tarde o falle.

## Flujo de una consulta

| Paso | Quién | Qué hace |
|---|---|---|
| 1 | Web / móvil → api-gateway → agro-service | `GET /api/recomendacion?lat&lon&mesSiembra` (también `/api/mapa`, `/api/validacion`, `/api/cultivos`, `/api/asistente`) |
| 2 | agro-service → PostgreSQL | Lee: ¿hay datos NASA y un cálculo frescos para ese punto? Si los hay, salta al paso 7 |
| 3 | agro-service → climate-service | Pide el cálculo: envía el punto, la fecha y el catálogo (cultivos y rotaciones leídos de la BD) |
| 4 | climate-service → APIs NASA/NOAA | Descarga POWER, GPM IMERG, SMAP, MODIS/VIIRS, MUR SST, SRTM y HLS |
| 5 | climate-service → agro-service | Devuelve los **datos NASA crudos** (para guardarlos) y los **resultados**: indicadores, rotaciones, qué hacer, riesgo por mes |
| 6 | agro-service → PostgreSQL | Graba en `nasa.datos_nasa`, `agro.consultas` y `agro.riesgo_mensual` |
| 7 | agro-service → web / móvil | Responde el JSON con la forma del contrato (`types/api.ts` del frontend) |

## Responsabilidades

| Componente | Hace | No hace |
|---|---|---|
| **Frontend** (Vue 3, `03. frontend`) y **móvil** (Capacitor) | Muestra datos y llama a `/api/...` | Llamar a la NASA o a Python; guardar datos de negocio |
| **api-gateway** (Spring Cloud Gateway :8080) | Enruta `/api/...` | Lógica de negocio |
| **agro-service** (Spring Boot :8081) | Lee y graba en PostgreSQL, arma la respuesta, decide si el dato está fresco | Descargar de la NASA |
| **climate-service** (FastAPI :8000) | Descarga datos NASA y calcula riesgos, puntajes y perspectiva | Conectarse a PostgreSQL |
| **PostgreSQL 17** | Esquemas `agro`, `nasa` y `ref` (doc 26) | — |

## Frescura de los datos (propuesta)

- Diario reciente (POWER, IMERG, SMAP): **3 horas**.
- MUR SST: **6 horas**.
- Climatología (normales): **30 días**.
- Recomendación calculada por punto y mes de siembra: **3 horas**.

## Asistente de IA (decisión del equipo, 14-nov, propuesta de Sheila)

- **Modelo:** `openai/gpt-oss-20b`, con **licencia Apache 2.0**, aprobada por la OSI. Cumple la cláusula *Use of Third-Party Materials* de los términos de la NASA ([30_terminos_legales_space_apps](30_terminos_legales_space_apps.md)): todo material de terceros debe ser libre o de código abierto. Llama se descartó porque su licencia es propia y no es oficialmente de código abierto.
- **Servicio:** Groq ejecuta el modelo. Lo llama **el backend Java** (`agro-service/.../asistente/GroqClient.java`), nunca la app, así que la clave no queda expuesta en el código público.
- **Clave:** `GROQ_API_KEY`, solo en el `.env` del servidor (no se sube a GitHub). Si no hay clave o Groq falla en 8 s, el asistente responde en **modo respaldo**, con plantillas basadas en el "qué hacer" ya calculado.
- **Qué hace la IA:** solo **explica** la recomendación ya calculada con reglas sobre datos NASA. No calcula, se validan las fuentes que cita y tiene un límite de 10 preguntas por minuto por IP.
- **Declaración en la entrega** (*Use of AI / NASA Data*): "Asistente que explica en lenguaje simple los resultados calculados con reglas sobre datos NASA; modelo abierto gpt-oss-20b (Apache 2.0) servido por Groq y llamado desde nuestro backend. El equipo también usó asistentes de IA para programar y documentar".

## Licencias de terceros que hay que citar (términos de la NASA)

| Material | Licencia |
|---|---|
| Código de AllpaShift (nuestro) | MIT |
| gpt-oss-20b (modelo del asistente) | Apache 2.0 |
| Vue 3, Vite, Pinia, Leaflet, Chart.js, Capacitor, FastAPI, Pydantic, httpx | MIT / BSD-2 |
| Spring Boot, Spring Cloud Gateway | Apache 2.0 |
| PostgreSQL | Licencia PostgreSQL (aprobada por la OSI) |
| Mapa base OpenStreetMap | ODbL (citar "© OpenStreetMap contributors") |
| Datos NASA (POWER, IMERG, SMAP, MODIS/VIIRS, MUR SST, SRTM, HLS) | Datos abiertos de la NASA (citar el DOI de cada dataset, doc 25) |
| Papers MDPI | CC BY 4.0 (doc 25) |

## Estado frente a las reglas (2026-11-14)

- ✅ Web → `/api/...` → agro-service (Java) → servicio de cálculos (Python): funcionando en https://allpashift.crisaor.org, desplegado desde `develop`.
- ✅ Java no descarga de la NASA: lo hace Python. Java lee primero `agro.consultas` y graba `agro.consultas`, `nasa.datos_nasa` y `agro.riesgo_mensual`.
- ✅ Python no se conecta a PostgreSQL en el servidor: se quitó `DATABASE_URL` del climate-service.
- ⚠️ **Hay dos servicios de cálculo en Python:** `calculos` (Sheila, puerto 8001), que es el que usa hoy agro-service, y `climate-service` (David, puerto 8000). El equipo debe decidir con cuál se queda.
- ⏳ El asistente está en modo respaldo hasta que se ponga `GROQ_API_KEY` en el `.env` del servidor.
