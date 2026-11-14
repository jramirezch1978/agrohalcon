# Comparativa de tecnologías por capa — AgroHalcón

> Requisito de Jhonny (2026-11-10): el proyecto debe tener **backend + frontend web + app móvil**.
> Contexto: 48 horas, equipo de 5 (Jhonny: Java/Azure/arquitectura · Sheila: Java y Python · David: Python/ML · Lucía: GIS · Edwin: comunicación).

## 1. Backend

| Opción | Pros | Contras |
|---|---|---|
| **Java + Spring Boot** (propuesta de Jhonny) | Jhonny y Sheila lo dominan · robusto, tipado, arquitectura limpia · excelente para APIs REST, caché y seguridad · despliegue fácil en Azure App Service | Más código y configuración que Python para un prototipo de 48 h · **casi no hay librerías de datos satelitales y ciencia de datos** (pandas, xarray, scikit-learn, Mann-Kendall son de Python) · David (ML) no trabaja en Java |
| **Python + FastAPI** | Todas las librerías científicas y de NASA (earthaccess, xarray, rasterio) · David, Sheila y Lucía saben Python · muy rápido de escribir · documentación automática `/docs` | Menos estructura que Spring si el proyecto crece · Jhonny lo usaría menos que Java |
| **Node.js (Express/NestJS)** | Mismo lenguaje que el frontend · rápido | Débil en ciencia de datos · nadie del equipo lo propuso |
| **Híbrido: Java (API principal) + Python (servicio de análisis)** | Cada uno trabaja en su lenguaje fuerte: Jhonny/Sheila en Spring Boot; David en Python para modelos | Dos servicios que desplegar, comunicar y depurar en 48 h · más riesgo de integración |

**Recomendación:** si el equipo se siente cómodo, **Spring Boot como API principal** + **un microservicio Python mínimo** solo para los cálculos de David (tendencias, puntaje de rotaciones). Si se quiere minimizar riesgo: **todo en FastAPI**.

## 2. Frontend web

| Opción | Pros | Contras |
|---|---|---|
| **Vue 3 (+ Vite)** | Curva de aprendizaje suave · rápido de prototipar · ligero · buena integración con Leaflet (`vue-leaflet`) y gráficos (Chart.js, ECharts) · sirve de base para la app móvil con Capacitor | Ecosistema algo menor que React · menos "estándar empresarial" que Angular |
| **Angular** | Muy estructurado (módulos, servicios, inyección de dependencias), parecido a Spring · TypeScript obligatorio · ideal para equipos grandes y proyectos largos | Curva de aprendizaje alta · mucho código repetitivo para 48 h · más pesado · si alguien no lo conoce, se bloquea |
| **React** (referencia) | Ecosistema más grande · más ejemplos de mapas (react-leaflet, MapLibre) · React Native para móvil | JSX y hooks requieren práctica · ninguno de los dos que propones |

**Recomendación:** **Vue 3**. Para un prototipo de 48 h es el más productivo y el más fácil de aprender para quien no lo conozca. Angular conviene solo si Sheila o Jhonny ya lo dominan.

**Mapas (cualquier framework):** Leaflet o MapLibre GL · capas GeoJSON exportadas por Lucía desde QGIS · gráficos con ECharts o Chart.js.

## 3. App móvil

| Opción | Plataformas | Pros | Contras |
|---|---|---|---|
| **Android Studio (Kotlin/Java nativo)** | Solo Android | Máximo rendimiento y acceso al hardware · Java ya lo conocen | **Solo Android** · tercera base de código distinta · rehacer pantallas y mapas que ya hizo la web · lento para 48 h |
| **Flutter (Dart)** | Android, iOS y web | Una sola base de código · UI muy fluida y bonita · buen soporte (`flutter_map`) | Dart es nuevo para el equipo · **no reutiliza el frontend Vue/Angular**: sería otro proyecto completo |
| **Xamarin (C#)** | Android, iOS | Fue la opción de Microsoft para C# | ⚠️ **Microsoft le retiró el soporte en mayo de 2024**; su sucesor es .NET MAUI · no recomendable para un proyecto nuevo |
| **Apache Cordova** | Android, iOS | Envuelve una web en una app | Tecnología antigua y en declive · plugins desactualizados · reemplazada en la práctica por Capacitor |
| **React Native** *(probablemente lo que llamas "React Designer")* | Android, iOS | Una base de código · muy popular | Exige React (no Vue ni Angular) · otro proyecto aparte |
| **Capacitor (de Ionic)** ⭐ | Android, iOS (y la misma web) | **Convierte el mismo frontend Vue o Angular en app de Android e iOS** · casi sin código extra · acceso a GPS y cámara · sucesor moderno de Cordova | Rendimiento algo menor que nativo (irrelevante para mapas y gráficos) · requiere Android Studio solo para compilar el APK |
| **PWA (app web instalable)** | Cualquier celular con navegador | Cero código extra · se instala desde el navegador · los jueces solo abren un enlace | No se publica en Play Store · acceso limitado al hardware en iOS |

**Recomendación:** **Vue + Capacitor**. Una sola base de código para web, Android e iOS; Android Studio se usa solo para generar el APK. Como respaldo, la misma web funciona como PWA.

## 4. Propuesta final

```
          ┌──────────────────────────────┐
          │ Vue 3 + Vite + Leaflet       │ ← web (Azure Static Web Apps)
          │ + Capacitor                  │ ← APK Android (e iOS)
          └──────────────┬───────────────┘
                         │ REST/JSON
          ┌──────────────▼───────────────┐
          │ Spring Boot (Java) — API     │ ← Azure App Service
          │ caché, parcelas, rotaciones  │
          └──────┬───────────────┬───────┘
                 │               │ HTTP interno
                 ▼               ▼
            APIs NASA     Servicio Python (FastAPI) — David
            (POWER,       tendencias, Mann-Kendall, puntajes
             MODIS,       + PostgreSQL (Neon / Azure)
             SMAP…)
```

| Capa | Tecnología | Responsable |
|---|---|---|
| Backend principal | Java 21 + Spring Boot 3 | Jhonny + Sheila |
| Análisis de datos | Python + FastAPI (mínimo) | David |
| Frontend web | Vue 3 + Vite + Leaflet + ECharts | Sheila (+ Jhonny) |
| App móvil | Capacitor (mismo código Vue) | Sheila / Jhonny |
| Datos GIS y locales | QGIS → GeoJSON | Lucía |
| Despliegue | Azure (App Service + Static Web Apps) + GitHub público | Jhonny |

⚠️ Riesgo principal: tres piezas (Spring, Python, Vue/Capacitor) en 48 h. Plan B: si el sábado por la tarde la integración Java ↔ Python se complica, mover los cálculos a Java o todo el backend a FastAPI.
