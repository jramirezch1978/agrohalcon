# Preparación del entorno — AgroHalcón

> **Regla:** el código del proyecto empieza con el hackathon (la sede dice sáb 14, 00:00; el FAQ de NASA dice 9:00 hora local → empezamos a programar a las **9:00** para no arriesgar).
> **Antes** se permite y se recomienda: instalar software, crear cuentas y probar herramientas ("Software listo antes del sábado", guía de la sede, p. 5).

## 1. Todos

- [ ] Cuenta en **spaceappschallenge.org** (ya en Members ✅)
- [ ] Cuenta en **GitHub** y aceptar la invitación a https://github.com/jramirezch1978/agrohalcon
- [ ] **Git** instalado: `git --version`
- [ ] **VS Code** (o IntelliJ para Java)
- [ ] **Earthdata Login** (gratis): https://urs.earthdata.nasa.gov
- [ ] WhatsApp del equipo con notificaciones activas · audífonos · cargador

### Earthdata Login — estado
- ✅ **Jhonny:** cuenta creada el 14-11-2026 · usuario `jhonny.ramirez` · organización INDEPENDIENTE · país Perú.
- ⏳ David: pendiente.
- Para el backend: **Generate Token** en el perfil → guardarlo como variable de entorno `EARTHDATA_TOKEN` (nunca en el repositorio).
- Autorizar en *Applications → Authorized Apps* la app **NASA GESDISC DATA ARCHIVE** (necesaria para descargar GPM/IMERG y GLDAS).

## 2. Por rol

| Rol | Instalar / preparar | Comprobar |
|---|---|---|
| **Jhonny** (API Spring Boot + Azure) | JDK 21 (Temurin) · Maven 3.9 · IntelliJ o VS Code + Extension Pack for Java · Azure CLI · cuenta Azure con suscripción activa | `java -version` · `mvn -v` · `az login` |
| **Sheila** (Vue + Capacitor) | Node.js 20 LTS · npm · VS Code + extensión **Vue - Official** · Android Studio (SDK y un emulador o celular con depuración USB) | `node -v` · `npm -v` · abrir Android Studio sin errores |
| **David** (Python + datos) | Python 3.12 · pip · VS Code + extensión Python/Jupyter · librerías: `fastapi uvicorn pandas numpy scipy pymannkendall httpx` | `python --version` · `pip install …` sin errores · probar una llamada a NASA POWER |
| **Alejandro** (catálogo de cultivos) | Excel o Google Sheets · Python básico opcional | Tener a mano los calendarios agrícolas de MIDAGRI y fuentes FAO |
| **Edwin** (comunicación) | Canva (cuenta) · CapCut o editor de video · Grammarly/DeepL para revisar inglés | Plantilla de Canva con colores y logo de AgroHalcón (`logo/agrohalcon_logo.png`) |

Colores de la identidad: verde `#78CD6E` · oro `#E8B740` · fondo verde oscuro `#0E1E14`.

## 3. Estructura del repositorio (se crea al iniciar el hackathon)

```
agrohalcon/
├── README.md              # descripción en inglés (requisito de la entrega)
├── docs/                  # diagramas, capturas, tabla de datasets NASA, uso de IA
│   └── img/
├── api/                   # Java 21 + Spring Boot 3 (Jhonny)
├── analytics/             # Python + FastAPI (David)
├── web/                   # Vue 3 + Vite + Leaflet + Capacitor (Sheila)
└── data/
    └── crops/             # catálogo de cultivos del norte en JSON (Alejandro)
```

## 4. Forma de trabajar en GitHub

- Rama `main` protegida: **solo se integra con Pull Request**.
- Cada uno trabaja en su rama: `feat/api-…`, `feat/web-…`, `feat/analytics-…`, `data/crops-…`.
- Commits pequeños y frecuentes; Jhonny revisa e integra.
- **Domingo 20:00: último merge.** Después de las 23:59 no se puede tocar el repositorio (regla de la guía).

## 5. Comandos de arranque (ejecutar el sábado al inicio, no antes)

```bash
# API (Jhonny)
curl https://start.spring.io/starter.zip -d type=maven-project -d javaVersion=21 \
  -d dependencies=web,validation,actuator,cache -d groupId=pe.halcondorado \
  -d artifactId=api -o api.zip

# Web (Sheila)
npm create vue@latest web
cd web && npm install leaflet @vue-leaflet/vue-leaflet echarts @capacitor/core @capacitor/cli @capacitor/android

# Analytics (David)
python -m venv .venv && pip install fastapi uvicorn pandas numpy scipy pymannkendall httpx
```

## 6. Despliegue previsto

| Pieza | Servicio |
|---|---|
| Web | Azure Static Web Apps (gratis) |
| API Spring Boot | Azure App Service (Linux, Java 21) |
| Analytics Python | Azure App Service (Python) o Container Apps |
| Datos de cultivos | JSON dentro del repositorio (sin base de datos para la primera versión) |
