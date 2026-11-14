# Comportamiento esperado de AllpaShift: prototipo en video (2026-11-14)

> Video: `01. documentacion/Videos/WhatsApp Video 2026-11-14 at 1.14.58 PM.mp4` (36 s, 1920×926), compartido en el grupo.
> Muestra un **prototipo funcionando en `localhost:5173`** (Vue). Todavía dice **"AgroShift"**: hay que cambiarlo a **AllpaShift**.
> Revisado fotograma a fotograma (cada 1,5 s).

## 1. Estructura de la app

- **Menú lateral:**
  - ¿Qué hago?
  - ¿Qué siembro?
  - Mapa
  - ¿Funciona? (máquina del tiempo)
  - Ayuda
- **Abajo del menú:**
  - La parcela activa (por ejemplo, "Kuantan Singingi…").
  - Selector **ES / EN**.
  - Modo oscuro.
- **Botón flotante:** **"Pregúntale a AllpaShift"** (asistente de IA).

## 2. Flujo que muestra el video

| Seg. | Pantalla | Qué pasa |
|---|---|---|
| 0-5 | **Mapa** (mundial) | Buscador "Buscar un lugar del mundo…", botón **"Usar mi ubicación"** y leyenda **Nivel de riesgo** (Alto, Medio, Bajo). Al tocar el mapa aparece el marcador "Mi parcela" y una tarjeta con el lugar y las coordenadas (Kirguistán, luego Indonesia: demuestra que es **global**). Botón **"Analizar esta parcela →"** |
| 6.5 | **¿Qué hago ahora?** | "La acción para las próximas 2 semanas." Pregunta **¿En qué te ayudamos?**: *Recomiéndame qué sembrar* o *Ya tengo un cultivo permanente (mango, limón, banano…)*. Mientras calcula, muestra un esqueleto de carga |
| 8-13 | **Resultado** | **Banner rojo de alerta** ("lluvia muy baja y humedad del suelo muy baja"). Tarjeta **ACCIÓN RECOMENDADA** con nivel de riesgo climático y una acción grande: **ESPERAR**, *"Todavía no siembres: el suelo está seco. Mejor espera a diciembre"*. **Motivo:** "La humedad del suelo está 38 % por debajo de lo normal". Etiquetas **Dato: Ejemplo** y **Siembra planeada: noviembre (Cambiar)**. Botón **Compartir por WhatsApp**. A la derecha: **Mejor rotación** (81, Frijol - Maíz, "usa poca agua y resiste el calor") y **Pregúntale a AllpaShift** con preguntas sugeridas (*¿Por qué no me conviene sembrar arroz? · ¿Qué rotación tiene menos riesgo? · ¿Cuál es el mes más riesgoso de mi campaña?*). Debajo, **"Lo que ven los satélites"**: toca un indicador para ver por qué |
| 14-22 | **¿Qué me conviene sembrar?** | Fecha y lugar. Selector **¿Cuándo vas a sembrar?** (Noviembre: este mes · Diciembre: el próximo · Enero: en 2 meses). Aviso: *"No predice el clima exacto a meses; estima el riesgo combinando el historial climático de la NASA con señales tempranas como El Niño"*. **3 tarjetas de rotación** con puntaje animado de 0 a 100: **Frijol → Maíz 81** (Recomendada, riesgo bajo, agua baja), **Maíz → Algodón 65** (riesgo medio, agua media), **Arroz → Arroz 43** (riesgo alto, agua alta). Cada una con su motivo y **"¿Por qué este puntaje?"**. Al cambiar el mes, los puntajes se recalculan (79/60/37) |
| 23-29 | ¿Qué hago? (otra vez) | Vuelve a la acción recomendada; se puede cambiar el mes de siembra planeada |
| 30-36 | **Perspectiva de la campaña** (en cada tarjeta) | Siembra, cosecha y duración (5, 9 u 8 meses). **Barra de meses N-D-E-F-M…** en verde, ámbar o rojo, y **"Mes más riesgoso: noviembre"**. Al tocar un mes aparece su detalle: *"Marzo de 2027: temporada de lluvias, exceso de humedad · Fuente: Ejemplo"*. Al final, **"Comparación de puntajes"** |

## 3. Qué datos necesita cada pantalla y dónde están en la base (doc 26)

| Elemento | Tabla o campo |
|---|---|
| Parcela, lugar y coordenadas | `agro.parcelas` (lat, lon, zona_id), `agro.zonas` |
| Acción recomendada (ESPERAR / SEMBRAR / REGAR / PROTEGER / COSECHAR) | `agro.consultas.resultado` (JSONB) + `agro.acciones_etapa` |
| Motivo con dato (humedad −38 %) | `agro.consultas.indicadores` + `nasa.normales` (anomalía frente a 1991-2020) |
| "Dato: Ejemplo" frente a dato real | Bandera `es_ejemplo` en el resultado. Hoy el prototipo usa datos de ejemplo |
| Siembra planeada (mes) | `agro.parcelas.fecha_siembra` o un parámetro de la consulta |
| Tarjetas de rotación con puntaje, riesgo, agua y motivo | `agro.rotaciones` + puntaje de climate-service + `agro.cultivos.agua_necesaria` |
| Perspectiva de la campaña (barra de meses) | `agro.riesgo_mensual` (nivel, motivo) + `agro.calendario` (siembra → cosecha) |
| Cultivo permanente (mango, limón, banano) | `agro.cultivos.tipo = 'permanente'` → acciones, no rotación |
| Preguntas a la IA | Usa `consultas.resultado` como contexto; no inventa cálculos |

## 4. Ajustes que salen del video

1. **Nombre:** cambiar "AgroShift" por **AllpaShift** en el prototipo (menú, botón del asistente y textos).
2. **Monocultivo como rotación actual:** el video compara **"Arroz → Arroz"**. Se quitó la restricción `cultivo1_id <> cultivo2_id` de `agro.rotaciones` y se agregó la rotación "Arroz - Arroz (monocultivo actual)".
3. **Datos reales:** la etiqueta "Dato: Ejemplo" debe cambiar a la fuente real (SMAP, IMERG, POWER) cuando climate-service entregue los indicadores.
4. **Mapa:** el prototipo usa un mapa mundial. Para la demo de Piura conviene sumar la **capa de los 18 valles** y la superficie agrícola (doc 24, sección 4).
5. **Cultivos:** las tarjetas usan frijol, maíz, algodón y arroz. El catálogo ya tiene 37 (doc 17), con uva, mango y limón para la opción "Ya tengo un cultivo permanente".

## 5. Implementado en AllpaShift (2026-11-14, desplegado en http://2.29.101.199)

Interfaz reconstruida con el mismo diseño del prototipo: menú lateral verde, acento lima, tarjetas blancas, tarjeta de acción oscura, ES/EN y modo oscuro. Pantallas:
- **Mapa:** buscador mundial (OpenStreetMap Nominatim), "Usar mi ubicación", leyenda de riesgo, los **18 valles** marcados y la tarjeta "Mi parcela" con "Analizar esta parcela".
- **¿Qué hago?:**
  - Elección entre sembrar o cultivo permanente, con 7 permanentes.
  - Alerta, acción recomendada (ESPERAR / SEMBRAR / PROTEGER / REGAR / COSECHAR) con su motivo y el dato que la respalda.
  - Mes de siembra cambiable, compartir por WhatsApp y mejor rotación.
  - Preguntas al asistente y **"Lo que ven los satélites"** (humedad del suelo, lluvia de 30 días, calor y mar).
- **¿Qué siembro?:**
  - Selector de mes (Nov, Dic, Ene) y 3 rotaciones con puntaje animado, riesgo, uso de agua y "¿Por qué este puntaje?".
  - **Perspectiva de la campaña** (barra de meses en verde, ámbar o rojo, mes más riesgoso y detalle al tocar) y comparación de puntajes (ECharts).
- **¿Funciona?:** máquina del tiempo 2016 frente a 2017 con NASA POWER de la parcela, más la tabla IMERG por valle.
- **Ayuda** y botón flotante **"Pregúntale a AllpaShift"**. El asistente responde solo con los resultados ya calculados.

**Datos reales:**
- NASA POWER: normal climatológica y últimos 30 días.
- MUR SST: anomalía del mar, vía el proxy `/nasa/erddap/` de Nginx, porque ERDDAP no permite CORS.
- Si NASA no responde, se usan datos de ejemplo y la etiqueta lo dice ("Dato: Ejemplo").

⚠️ **Hallazgo del 14-nov (Medio Piura, NASA POWER):**
- **240 mm de lluvia en 30 días**, cuando lo normal son unos 5 mm.
- Humedad del suelo +91 %.
- Mar **+8,5 °C** (MUR SST, en un punto a ~100 km de la costa).

Coincide con el ONI +2,46 que reportó David y apunta a un **El Niño fuerte en curso**. **Contrastarlo con el comunicado del ENFEN** antes de mostrarlo en la demo.
