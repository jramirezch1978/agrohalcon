![AllpaShift](01.%20documentacion/img/allpashift_banner.png)

# AllpaShift — Equipo Halcón Dorado

NASA Space Apps Challenge 2026 · Sede Piura · Reto **Field Shift: Adapting Farms with NASA Data**.

## ¿Qué hace AllpaShift?

**AllpaShift le dice al agricultor qué sembrar, cuándo y qué hacer esta quincena, según el riesgo climático que muestran los satélites de la NASA para su valle.** (*Allpa* = tierra en quechua · *Shift* = el cambio del reto Field Shift).

1. **Ubica la parcela** en el mapa y su valle (18 valles del norte del Perú: Bajo Piura, Chira, San Lorenzo, Alto Piura, Sechura, sierra...).
2. **Lee los satélites:** lluvia (GPM IMERG), humedad del suelo (SMAP), clima (NASA POWER), vegetación (MODIS NDVI), temperatura del mar (MUR SST) y relieve (SRTM).
3. **Calcula el riesgo** de sequía, lluvia extrema, calor y El Niño costero, frente a lo normal (1991-2020).
4. **"¿Qué hago esta quincena?":** la fase de cada cultivo y las acciones a tomar, con la alerta NASA que las justifica.
5. **Compara rotaciones** (la actual frente a 2 alternativas) con beneficios, sacrificios e incertidumbre. Los cultivos permanentes (mango, limón, uva, banano, café, cacao) reciben acciones, no rotaciones.
6. **Perspectiva de la campaña:** una barra de meses de la siembra a la cosecha en 🟢 verde, 🟡 ámbar o 🔴 rojo.
7. **Máquina del tiempo:** qué habría recomendado antes del Niño Costero 2017, cuando en marzo llovió entre 5 y 9 veces lo normal en los valles de Piura.

Catálogo: **37 cultivos** (cereales, menestras, frutales, hortalizas, tubérculos, industriales). Detalle en [27_que_hace_allpashift](01.%20documentacion/27_que_hace_allpashift.md) y modelo de datos en [26_modelo_base_de_datos](01.%20documentacion/26_modelo_base_de_datos.md).

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
