# Propuestas del equipo y estrategia de ramas (2026-11-14, día 1 del hackathon)

## 1. Propuesta capturada por un integrante: recomendación por ciclo completo

- La recomendación evalúa **todo el ciclo del cultivo** (de la siembra a la cosecha), no solo el mes actual.
- Datos:
  - **Clima histórico NASA POWER** (climatología por punto).
  - **Señal de El Niño con MUR SST**, la temperatura del mar frente a Piura.
  - **Pronóstico estacional GEOS-S2S** (opcional).
- **Cultivos permanentes** (mango, limón, banano, cacao, café) → reciben **acciones**, no rotaciones.
- En la app:
  - **"¿Qué hago esta quincena?"**
  - **"Perspectiva de la campaña"**: una barra de meses, de la siembra a la cosecha, con el riesgo de cada mes en verde, ámbar o rojo.

**Prueba de MUR SST (2026-11-14):**
- `coastwatch.pfeg.noaa.gov` respondió 503 (caído).
- ✅ `upwell.pfeg.noaa.gov/erddap/griddap/jplMURSST41` responde 200, sin login. Valor frente a Piura (-5.5, -81.5) el 2026-11-13: **27,1 °C**.
- Respaldo: PO.DAAC con el token Earthdata, o el índice Niño 1+2 / ICEN (ENFEN).

## 2. Resumen "AgroShift: de qué trata nuestro proyecto" (texto del equipo)

- **Qué es:** una app que usa datos satelitales de la NASA para decirle a cualquier agricultor del mundo **qué sembrar y cuándo**, según el riesgo de sequía, lluvias extremas, calor y El Niño. El caso de ejemplo es Piura.
- **Problema:** hoy se siembra por costumbre; si llega una sequía o El Niño, se pierde la cosecha. La app avisa antes y propone un cultivo más resistente.
- **Cómo funciona:**
  1. El agricultor marca su parcela en el mapa.
  2. La app consulta lluvia, humedad del suelo, temperatura, vegetación y temperatura del mar.
  3. Calcula el riesgo y puntúa 3 rotaciones.
  4. Muestra "¿Qué hago esta quincena?", el comparador de rotaciones y un asistente de IA que explica con palabras simples.
- **Diferenciales:**
  - **Máquina del tiempo:** qué habría recomendado la app antes del Niño Costero de 2017.
  - **Global:** funciona con cualquier coordenada.
  - **"IA que explica, no inventa":** los cálculos salen de la NASA y la IA solo los traduce.

✅ **Nombre decidido (2026-11-14): AllpaShift** (*allpa* = tierra en quechua + *Shift* del reto). Reemplaza a AgroHalcón y a la propuesta AgroShift en el repo, el logo, el APK y la web.

## 3. Estrategia de ramas (repo remoto reiniciado el 2026-11-14)

Por pedido de Jhonny se limpió el historial remoto de https://github.com/jramirezch1978/allpashift:
- Ahora tiene **un solo commit** (`e5e4682`) con README, .gitignore y LICENSE.
- Las 7 ramas salen de ese commit.
- La copia local (`allpashift/`, último commit `dbb118a`) quedó intacta, con todo el código anterior.

| Rama | Para qué | Quién |
|---|---|---|
| `main` | Solo la versión que funciona (demo y entrega) | Jhonny la actualiza |
| `develop` | Integración: se juntan las partes para probarlas | Todos hacen merge aquí |
| `feature/api-java` | API Spring Boot, conexión con Groq, despliegue | Jhonny |
| `feature/frontend-vue` | App Vue + Capacitor | Sheila |
| `feature/datos-python` | Indicadores, puntajes de rotación, datos NASA | David |
| `feature/catalogo-cultivos` | Catálogo de cultivos (JSON o SQL) | Alejandro |
| `docs/entrega` | README, textos en inglés, capturas | Edwin |

> La tabla original dice "despliegue en Azure", pero el servidor contratado es **Hetzner** (2.29.101.199). En el README del repo se dejó solo "despliegue".
