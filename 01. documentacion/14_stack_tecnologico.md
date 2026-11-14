# Stack tecnológico propuesto — AllpaShift

> Requisitos de Jhonny: frontend que dibuje mapas · backend que se conecte de forma transparente a NASA · uso híbrido en celular y tablet (con conexión).
> Propuesta de Sheila en el grupo: Flutter + FastAPI + Render + Neon.

## Recomendación: web app responsive instalable (PWA) + API en Python

```
 Celular / tablet / PC  (navegador o app instalada como PWA)
            │  HTTPS
            ▼
 ┌──────────────────────────────┐
 │ FRONTEND  React + Vite + TS  │  Mapas: Leaflet (react-leaflet) o MapLibre GL
 │ Tailwind · Recharts · PWA    │  Gráficos, sliders de escenarios, comparador de rotaciones
 └──────────────┬───────────────┘
                │ REST/JSON  (/api/parcela, /api/clima, /api/ndvi, /api/rotaciones)
                ▼
 ┌──────────────────────────────┐
 │ BACKEND  FastAPI (Python)    │  "Puerta única" a NASA: el frontend nunca llama a NASA directo
 │ httpx async · pandas         │  Normaliza, armoniza y cachea los datos
 │ scikit-learn · pymannkendall │  Tendencias, riesgo, puntaje de rotaciones (David)
 │ LLM (Claude / Gemini / Azure)│  Explicaciones en lenguaje sencillo (declarar uso de IA)
 └──────┬──────────────┬────────┘
        │              │
        ▼              ▼
  APIs NASA        PostgreSQL (Neon) + PostGIS opcional
  POWER · MODIS     caché de respuestas, parcelas, catálogo de cultivos (Lucía)
  (ORNL) · FIRMS
  Earthdata (SMAP, GPM, ECOSTRESS…)
```

## Por qué PWA y no app nativa / Flutter (para 48 h)

| Criterio | PWA (React) | Flutter (web + móvil) |
|---|---|---|
| Funciona en celular y tablet | ✅ Se instala desde el navegador ("Agregar a pantalla de inicio") | ✅ |
| Los jueces abren un **enlace público** | ✅ Directo | 🟡 Flutter Web pesa más y carga lento |
| Mapas y datos geográficos | ✅ Leaflet/MapLibre: el ecosistema GIS más grande; carga GeoJSON de QGIS (Lucía) | 🟡 flutter_map funciona, pero con menos ejemplos |
| Curva de aprendizaje del equipo | ✅ Mucha documentación, ejemplos y ayuda de IA | 🟡 Dart es nuevo para casi todos |
| Velocidad para un prototipo de 48 h | ✅ Alta | 🟡 Media |

> Si Sheila ya domina Flutter, es una opción válida; lo importante es que el backend sea el mismo (FastAPI).

## Por qué FastAPI (Python) en el backend
- Todas las librerías de datos satelitales y científicas están en Python (pandas, xarray, rasterio, earthaccess).
- David (ML) y Lucía (análisis) trabajan en Python; Sheila también conoce Python.
- Documentación automática de la API (`/docs`), útil para la demo y para el campo "Detalles".

## Despliegue (enlace público, gratis o casi gratis)

| Pieza | Opción A | Opción B (Azure, experiencia de Jhonny) |
|---|---|---|
| Frontend | Vercel / Netlify | Azure Static Web Apps (gratis) |
| Backend | Render (gratis, pero "se duerme": ~50 s al despertar) | Azure App Service / Container Apps |
| Base de datos | Neon PostgreSQL (gratis) | Azure Database for PostgreSQL |
| Código | GitHub (repositorio **público**) | GitHub |

⚠️ La evaluación es del 16 al 20 nov: el servicio debe seguir encendido esos días. Si se usa Render gratis, avisar en la entrega que la primera carga tarda unos segundos, o usar Azure con créditos.

## Reparto sugerido

| Integrante | Parte del stack |
|---|---|
| Jhonny | Arquitectura, backend FastAPI, integración APIs NASA, despliegue |
| Sheila | Frontend React (o Flutter), pantallas y mapa |
| David | Modelos: tendencias, riesgo y puntaje de las 3 rotaciones; explicación de la incertidumbre |
| Lucía | Capas GIS (QGIS → GeoJSON), catálogo de cultivos y suelos de Piura, validación ambiental |
| Edwin | Textos de la app, demo y pitch |

## Preparación permitida antes del 14 nov
- Crear cuentas: GitHub, Vercel/Azure, Neon, Earthdata Login, clave de api.nasa.gov, FIRMS MAP_KEY.
- Instalar herramientas (Node, Python, VS Code) y hacer tutoriales de React-Leaflet y FastAPI.
- **No** escribir código del proyecto antes del 14 nov a las 9:00 (regla oficial).
