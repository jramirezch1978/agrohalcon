![AllpaShift](01.%20documentacion/img/allpashift_banner.png)

# AllpaShift — Equipo Halcón Dorado

NASA Space Apps Challenge 2026 · Sede Piura · Reto **Field Shift: Adapting Farms with NASA Data**.

## Ramas

| Rama | Para qué | Quién |
|---|---|---|
| `main` | Solo la versión que funciona, la que se muestra en la demo y se entrega | Jhonny la actualiza |
| `develop` | Donde se juntan las partes para probarlas juntas | Todos hacen merge aquí |
| `feature/api-java` | API en Spring Boot, conexión con Groq y despliegue | Jhonny |
| `feature/frontend-vue` | App en Vue y Capacitor | Sheila |
| `feature/datos-python` | Indicadores, puntajes de rotación y datos de la NASA | David |
| `feature/catalogo-cultivos` | Catálogo de cultivos (JSON o SQL) | Alejandro |
| `docs/entrega` | README, textos en inglés y capturas para la entrega | Edwin |

Flujo: cada uno trabaja en su rama → *pull request* a `develop` → cuando `develop` funciona, Jhonny pasa a `main`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `01. documentacion` | Documentación y textos de la entrega |
| `02. backend/java` | `api-gateway` y `agro-service` (Spring Boot) |
| `02. backend/python` | `climate-service` (FastAPI, datos NASA) |
| `03. frontend` | Vue 3 + Leaflet |
| `04. base de datos` | PostgreSQL: `ddl/` y `ddl/seed/` |
| `05. mobile` | Capacitor (Android / iOS) y `release/` |
| `deploy/vps` | docker-compose para el servidor |
