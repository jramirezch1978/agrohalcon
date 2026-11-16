# Tareas tras la auditoría técnica (15-nov-2026)

Origen: diagnóstico de la versión publicada (`AllpaShift_Diagnostico_Auditoria_261115.pdf`). Cada responsable trabaja en **su rama asignada**
(ver `23_propuestas_equipo_y_ramas.md`) y abre Pull Request a `develop`.

## Sheila — `feature/frontend-vue`

| # | Tarea | Dónde | Cómo se sabe que está lista |
|---|-------|-------|-----------------------------|
| S1 | **Leyenda de riesgo plegable.** Pasarla a un botón circular con la "i" de información que despliega la tarjeta; colapsada por defecto en el celular | `src/components/map/MapLegend.vue`, `src/views/MapView.vue` | En 375 px, el buscador y el popup de la zona se leen completos, y la leyenda se cierra con un toque |
| S2 | **Coordenadas imposibles.** Limitar el mapa (`maxBounds` de ±85° de latitud, `minZoom` 2) y normalizar la longitud a ±180° al marcar; si el punto no es válido, avisar | `src/views/MapView.vue` (`L.map`, `marcarParcela`) | No se puede marcar un punto como -90 / -196; en el mapa nunca sale "Punto elegido" con coordenadas fuera del mundo |
| S3 | **El botón flotante "Pregúntale a AllpaShift" no debe tapar texto.** Reservar espacio al final de las pantallas o moverlo | Vistas "¿Qué hago?" y "¿Qué siembro?" | Se puede leer el final de cada tarjeta en el celular sin que el botón la cubra |
| S4 | **Velocidad al navegar.** Precargar las pantallas en segundo plano y mostrar un indicador de carga al cambiar de pestaña | Router y carga de vistas | "Omitir" y el cambio de pestaña responden en menos de 1 s con buena señal |
| S5 | **Textos que confunden.** (a) Aclarar "72 de 100" frente a "Riesgo: Alto"; (b) unificar "6 semanas" (Ayuda) y "12 semanas" (¿Funciona?); (c) idioma: español por defecto o selector visible desde la primera pantalla (acordar con Jhonny) | `src/i18n`, vistas de rotaciones y ayuda | Un agricultor entiende la tarjeta sin explicación |
| S6 | **Aviso del escenario.** Mientras David no resuelva D1, mostrar que con El Niño extraordinario el escenario Seco/Húmedo no cambia el puntaje | Pantalla "¿Qué siembro?" | El aviso aparece solo cuando el puntaje no cambia entre escenarios |
| S7 | **PWA (después de que el dominio HTTPS esté activo).** Service worker con `vite-plugin-pwa`, guardar la última recomendación para verla sin conexión e invitar a instalar la app | `03. frontend` | Desde el dominio HTTPS, la app se puede instalar y abre la última recomendación sin internet |

## David — `feature/datos-python`

| # | Tarea | Dónde | Cómo se sabe que está lista |
|---|-------|-------|-----------------------------|
| D1 | **El escenario Seco/Húmedo debe mover los puntajes.** Hoy, con la señal de El Niño extraordinario, cambia solo la lluvia mensual de los textos; los puntajes y el orden de las rotaciones salen idénticos (72 / 72 / 15) | Servicio de cálculos (`rotaciones.py` y reglas) | Con la misma parcela, Seco, Normal y Húmedo dan puntajes distintos, o se documenta por qué no |
| D2 | **Confirmar la anomalía de +6,0 °C del mar (semana 2026-11-09).** Es 3 veces el pico de 2017 (+1,9 °C); comprobar que no sea un artefacto del dato MUR SST y contrastar con otra fuente | Datos de `climate-service` | Nota escrita con el valor verificado, o el dato corregido |
| D3 | *(Opcional)* **Rendimiento relativo.** Hoy la app da puntajes de riesgo, no rendimientos; evaluar si se puede estimar el impacto relativo en rendimiento con los datos disponibles | Servicio de cálculos | Propuesta breve de si se puede hacer con el tiempo que queda |

## Jhonny — `feature/api-java`

| # | Tarea | Estado |
|---|-------|--------|
| J1 | HTTPS con Cloudflare en `allpashift.crisaor.org` | Archivos listos; faltan los pasos 1 a 5 de `deploy/vps/HTTPS_CLOUDFLARE.md` (DNS, token, firewall, certificado, despliegue) |
| J2 | APK y iOS nuevos apuntando al dominio HTTPS, quitando `allowMixedContent` | Después de J1 |
| J3 | Decidir con Sheila el idioma por defecto (S5c) | Pendiente |
| J4 | Evaluar compresión gzip en nginx para el acceso por IP (el dominio ya la trae de Cloudflare) | Sugerencia |
