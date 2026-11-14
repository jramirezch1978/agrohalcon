# AgroShift – Frontend

Qué sembrar según el riesgo climático, con datos satelitales de la NASA.
NASA Space Apps Challenge · Vue 3 + Vite + TypeScript + Tailwind v4 + Leaflet + Chart.js + Capacitor.

## Correr

```bash
npm install
npm run dev          # http://localhost:5173  (en el celular: http://<IP-de-tu-PC>:5173)
npm run build        # tipos + build de producción en dist/
npm run preview      # sirve dist/ (aquí funciona el modo offline / PWA)
```

## Android (Capacitor)

Requisitos: **Android Studio** (incluye el SDK) y Java 17+.

```bash
npm run android      # build + sync + abre Android Studio  → botón ▶ Run, o Build > Build APK(s)
npm run android:run  # build + sync + instala en el celular conectado por USB
```

El APK queda en `android/app/build/outputs/apk/debug/app-debug.apk`.
Después de cambiar el código web: `npm run android:sync`.

## De dónde salen los datos

`.env` (copiar de `.env.example`). **Modo principal: el servicio de cálculos en Python** (carpeta `calculos/` del repo).

| Variable | Uso |
|---|---|
| `VITE_CALCULOS_URL` | Servicio de cálculos, p. ej. `http://localhost:8001`. **Todos** los datos de pantalla salen de aquí. |
| `VITE_USE_MOCK` | Solo si `VITE_CALCULOS_URL` está vacío: `true` = datos de ejemplo; `false` = backend Java |
| `VITE_API_URL` | Backend Java (todavía no existe) |

> En el celular **no uses `localhost`**: pon la IP de la PC donde corre el servicio (`http://192.168.x.x:8001`).

| Pantalla | Llamada | Datos reales |
|---|---|---|
| ¿Qué hago? / ¿Qué siembro? | `POST /calcular` | NASA POWER (lluvia fuera de Piura, humedad del suelo, calor), GPM IMERG (lluvia en Piura), MUR SST (El Niño) |
| Mapa | `POST /mapa` | Nivel de cada zona = peor indicador real |
| ¿Funciona? | `GET /validacion`, `GET /validacion/anios` | Lluvia GPM IMERG, alerta MUR SST, semanas de anticipación |

**Reglas de honestidad del dato**
- Si el servicio no responde: se usa la recomendación guardada (con su fecha) o datos de **ejemplo**, siempre con
  aviso (toast) y un **banner fijo** "Datos de ejemplo: no son datos reales de la NASA". Nunca en silencio.
- Los datos de ejemplo (`src/services/mocks/`) tienen fuente **"Ejemplo"**, nunca el nombre de un producto de la NASA
  (lo verifica un test del servicio de cálculos).
- Un indicador sin dato real (p. ej. El Niño sin MUR SST) no se muestra; un mes sin dato queda vacío en el gráfico.

### Asistente (sin IA)
Responde con plantillas a partir de la recomendación ya calculada (`src/services/asistentePlantillas.ts`) y cita solo
las fuentes que trae esa recomendación. Si falla o tarda más de 10 s, muestra `queHacer.motivo` como respuesta básica.

### Mapa
OpenStreetMap (© OpenStreetMap contributors) y vista satelital de **NASA GIBS (Blue Marble)**. El buscador
(Nominatim) espera 1 s sin escribir o Enter, con máximo 1 petición por segundo.

## Estructura

```
src/
  assets/main.css            Tema: colores, tipografías, superficies, animaciones
  components/
    layout/                  TopBar, BottomNav (móvil: ¿Qué hago? · ¿Qué siembro? · Mapa · ¿Funciona? · Ayuda), SideBar (escritorio)
    home/                    RecommendationHero, IndicatorCard, InfoBottomSheet, LoadingSkeleton, AlertSummary
    map/                     MapLegend, ZonePopup
    rotations/               RotationCard, ScoreRing, RotationsChart, RotationSheet ("¿Por qué este puntaje?")
    campaign/                SeasonTimeline, PlantingMonthSelector, CropTypeSelector, PerennialPlan, HonestyNote
    assistant/               ChatPanel, ChatBubble, SuggestedQuestions, TypingIndicator, AssistantFab, AssistantSheet
    datasets/                DatasetCard
    charts/                  Lluvia mensual vs. normal (Chart.js) para «¿Funciona?»
    ui/                      Botones, tarjetas, badges, skeletons, estados, bottom sheet
  composables/               Riesgo, indicadores, rotaciones, animaciones, gráficos, compartir
  data/nasaDatasets.ts       Lista editable de datos NASA (textos en i18n: datos.items.<id>)
  i18n/locales/              es.ts / en.ts (en tipado contra es)
  router/                    Rutas hash + bienvenida la primera vez
  services/api.ts            Modo de datos (Python / Java / ejemplo) con respaldo y avisos
  services/calculos.ts       Cliente del servicio de cálculos (Python)
  stores/origen.ts           Origen de los datos en pantalla (real / ejemplo / guardado) y avisos
  services/mocks/            Datos de ejemplo (varían por ubicación) + asistente simulado
  services/nasaPower.ts      Climatología REAL de NASA POWER (lluvia y temperatura por mes)
  services/ubicacion.ts      GPS (web y Android) + buscador de lugares (OpenStreetMap)
  stores/app.ts              Parcela, idioma, tema, última recomendación (offline)
  stores/asistente.ts        Historial del chat + respaldo
  views/                     Una vista por pantalla
public/sw.js                 Service worker (offline)
android/                     Proyecto nativo de Capacitor
```

## Checklist para la demo

**El día anterior**
- [ ] `npm run build` sin errores
- [ ] Correr el servicio de cálculos y actualizar datos: `python -m scripts.descargar_imerg --actualizar` y `python -m scripts.descargar_mur_sst --actualizar`
- [ ] Probar con `VITE_CALCULOS_URL` apuntando a la IP de la PC; no debe aparecer el banner amarillo de datos de ejemplo
- [ ] Instalar el APK en el celular de la demo y abrirlo una vez con internet
- [ ] Borrar los datos de la app para que arranque en la bienvenida (Ajustes > Apps > AgroShift > Borrar datos)
- [ ] Cargar el celular; brillo al máximo; modo No molestar

**Guion (en inglés, ~3 min)** — pestañas: *What to do? · What to plant? · Map · Does it work? · Help*
1. **Bienvenida** → 3 pasos → *Pick on the map*
2. **Map** → zonas de Piura (tocar una roja: popup) → buscar "Nairobi" → tocar el mapa → *Analyze this plot*
3. **What to do?** → *What should I do now?* → tipo de acción (WAIT / PLANT…) → tocar *Rainfall* → *Why does it matter?* (GPM IMERG, escala ~10 km)
4. Tocar *Rainfall* → "Normal is the average for this same month in recent years (since 2001)" (**dato real**)
5. **What to plant?** → *When will you plant?* → cambiar el mes → la barra de meses y los puntajes cambian → tocar el mes rojo → *Riskiest month*
6. Tocar una rotación → *Why this score?* → fórmula `100 − descuentos = puntaje`
7. *I already have a permanent crop* → Mango → plan por etapas
8. **Ask AgroShift** (botón flotante) → *What is the riskiest month of my season?*
9. **Does it work?** → El Niño 2017: el mar avisa el 16 de enero (+1.9 °C, MUR SST) y la lluvia máxima llega en marzo (5.2× lo normal, GPM IMERG): 6 semanas antes
10. **Help** → *How it works* en 4 pasos (para el jurado: *Technical details* en cada satélite)
11. *Share on WhatsApp* · modo avión → sigue mostrando la última recomendación

**Plan B**
- Sin internet en el lugar: el mapa no carga capas, pero la recomendación guardada sí se ve
- Video de respaldo grabado con la demo completa
