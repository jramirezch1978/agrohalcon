# Frontend de AllpaShift (Vue 3 + Vite + TypeScript)

Interfaz basada en el prototipo del equipo (ver `01. documentacion/28_prototipo_video_comportamiento.md`). Responsable: **Sheila** (`feature/frontend-vue`).

## Ejecutar

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # genera dist/ (lo usa el Dockerfile con Nginx)
```

## Estructura

| Ruta | Contenido |
|---|---|
| `src/App.vue` | Menú lateral, idioma ES/EN, modo oscuro, botón "Pregúntale a AllpaShift" |
| `src/estado.ts` | Estado global: parcela, ruta (`#/mapa`, `#/campana`, `#/siembro`, `#/funciona`, `#/ayuda`), resultado |
| `src/i18n.ts` | Textos en español e inglés |
| `src/vistas/Mapa.vue` | Mapa Leaflet (OpenStreetMap), buscador Nominatim, 18 valles, "Mi parcela" |
| `src/vistas/QueHago.vue` | Acción recomendada de la quincena, alerta, indicadores satelitales |
| `src/vistas/QueSiembro.vue` | 3 rotaciones con puntaje y "Perspectiva de la campaña" (barra de meses) |
| `src/vistas/Funciona.vue` | Máquina del tiempo: Niño Costero 2017 (POWER + IMERG) |
| `src/vistas/Ayuda.vue` | Cómo se usa y datasets NASA |
| `src/motor/nasa.ts` | Lectura de NASA POWER (climatología y diario) y MUR SST (ERDDAP vía `/nasa/erddap/`) |
| `src/motor/riesgo.ts` | Reglas de riesgo: indicadores, puntaje de rotaciones, riesgo por mes, acción recomendada |
| `src/data/catalogo.ts` | Valles, cultivos y rotaciones (subconjunto de la BD, doc 26) |

## Proxies

- `/nasa/erddap/` → `https://coastwatch.pfeg.noaa.gov/erddap/` (ERDDAP no permite CORS). Está en `nginx.conf` y en `vite.config.ts`.
- `/api/` → api-gateway (en desarrollo apunta al VPS).

## Pendiente

- Mover el motor de riesgo a `climate-service` (David) y consumirlo por `/api/climate/...`.
- Leer el catálogo desde la BD (`agro.v_cultivos_contrato`) por `/api/agro/...`.
- Cambiar NASA POWER por IMERG y SMAP cuando el backend los entregue por valle.
