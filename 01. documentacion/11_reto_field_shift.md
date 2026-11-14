# Challenge Statement — Field Shift: Adapting Farms with NASA Data

> Fuente: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/ (leído el 2026-11-07)
> Dificultad: Advanced / Intermediate · Temas: Arts & Multimedia, Earth Science, Software
> **Datasets oficiales (pestaña Resources): los publica NASA el 13 nov** según la sesión de orientación. Al 7 nov la pestaña aún no los lista.

**Video oficial del reto:** "2026 Challenge | Field Shift: Adapting Farms with NASA Data" (canal NASA Space Apps Challenge) → https://www.youtube.com/watch?v=cF0U2WXsM7o

Duración: 3 min 37 s. Descripción: "This video includes generated imagery" y remite a la página del reto para la explicación detallada. Tiene subtítulos automáticos (inglés y español, entre otros).

### Contenido del video (subtítulos automáticos en español, capturados el 2026-11-07)

**Parte 1 — narración (0:00–1:55):**
- "Incluso aquí, las condiciones bajo nuestros pies están cambiando: el calor cambia, las lluvias varían, el agua es menos segura, el suelo pierde nutrientes, y los agricultores deben decidir qué sigue."
- "La Tierra nos envía señales constantemente, y los datos públicos de observación terrestre de la NASA nos dan nuevas formas de escuchar: **lluvias, humedad del suelo, calor, vegetación, agua**. Diferentes observaciones, diferentes escalas, piezas de la misma historia."
- **Misión:** "convertir estas observaciones en una herramienta que ayude a explorar lo que podría venir después. **Comparen rotaciones, revelen beneficios y sacrificios, entiendan los riesgos, hagan visible la incertidumbre.** Creen un modelo de IA (SI), un mapa interactivo, una visualización, una herramienta de apoyo a decisiones, o construyan algo que ninguno de nosotros ha imaginado aún."
- "No necesitamos viajar a otro mundo para encontrar un desafío digno de exploración. La misión está aquí."

**Parte 2 — expertos del Centro Espacial Johnson de la NASA (2:00–3:37):**

| Persona | Rol |
|---|---|
| Autora del reto (nombre no captado en los subtítulos) | Ingeniera y desarrolladora: integración de la misión Artemis, carga útil de la base lunar, órbita baja, reactor espacial Freedom |
| Manideep Gogineni | Arquitecto de soluciones de datos: Artemis, aplicaciones web personalizadas |
| William Stefanov | Científico principal del sistema terrestre; imágenes de la Tierra desde la ISS para respuesta a desastres y teledetección. **Experto en la materia (SME) del reto** |
| Alex Token | Científico de datos (Ciencias de la Tierra y Teledetección): machine learning sobre fotografías de la Tierra tomadas por astronautas |

**Lectura para el equipo:** el jurado valorará (1) comparar rotaciones con **beneficios y sacrificios**, (2) **riesgos e incertidumbre visibles**, (3) IA y mapas bien explicados. El perfil de los expertos (arquitectura de datos, apps web, ML, teledetección) coincide con el del equipo.

## Qué pide el reto

Crear una **herramienta de apoyo a la decisión** (app, modelo, mapa interactivo u otra) que combine **observaciones de la Tierra de NASA** con **información local de suelos, características de cultivos y prioridades del agricultor**, para explorar **estrategias de rotación de cultivos** que mejoren la salud del suelo y la resiliencia frente a cambios de clima y agua.

**Es una herramienta de apoyo: no reemplaza el criterio del agricultor ni de expertos locales.**

## Datasets NASA que menciona el reto (sugeridos)

SMAP · ECOSTRESS · GPM · Landsat · MODIS · NASA POWER · GRACE y GRACE-FO · SRTM (u otros de elevación) · GEDI (biomasa, en la sección de fusión de datos).

Variables a analizar: temperatura, estrés por calor, lluvia, humedad del suelo, evaporación, riesgo de heladas, precipitación extrema, estrés de vegetación, tendencias de agua a largo plazo.

## Prioridades del agricultor a considerar

Uso de agua · valor forrajero · fijación de nitrógeno · reducción de erosión · materia orgánica · aptitud de mercado.

## Lo que la herramienta puede mostrar

- Épocas en que los campos suelen quedar **descubiertos** (bare fields).
- Temporadas en que los cultivos actuales son **más vulnerables**.
- Oportunidades de rotación que **corten ciclos de plagas**, **reduzcan la demanda de agua**, **mejoren la infiltración** o den **ingresos extra**.
- **Comparar al menos 3 estrategias de rotación, incluida la actual.** Para cada una: por qué se sugiere, qué evidencia la respalda, qué beneficios ofrece, dónde faltan datos y qué riesgos deben revisar agricultores o expertos.

## Consideraciones opcionales (suman puntos)

- **Datos:** explicar evapotranspiración, anomalías de humedad del suelo, NDVI, riesgo de heladas, balance hídrico; diferencia entre datos satelitales y de campo.
- **IA (SI), modelos y fusión de datos:** comparar enfoques de IA/estadística; detectar transiciones estacionales y estrés; explicar la incertidumbre; **armonizar datasets** de distinta resolución en una grilla común (SMAP, ECOSTRESS, GPM, Landsat/MODIS, GEDI, suelos).
- **Rotaciones:** ciclo de nutrientes, erosión, materia orgánica, plagas, agua, forraje, mercado; explicar cultivos fijadores de nitrógeno, de cobertura, de raíz profunda y tolerantes a sequía.
- **Mapas:** tendencias de humedad, olas de calor, pérdida de agua almacenada; zonas de erosión, estrés hídrico, heladas; líneas de tiempo, capas comparativas, **sliders de escenarios** de lluvia/temperatura.
- **Diseño centrado en el agricultor:** fácil de entender, que el agricultor ingrese sus prioridades y limitaciones (agua, equipos, mercado), recordatorios de que apoya y no reemplaza el criterio humano.

## Implicancias para AllpaShift

- El resumen (09) ya encaja; añadir **"compara 3 rotaciones, incluida la actual, con evidencia, beneficios, vacíos y riesgos"**.
- Datos ya probados: NASA POWER, MODIS (ORNL), SMAP y GPM (vía Earthdata). Faltan probar: **ECOSTRESS, Landsat, GRACE, SRTM, GEDI**.
- Roles: Lucía (suelos, cultivos, mapas), David (IA y armonización), Sheila y Jhonny (app), Edwin (narrativa centrada en el agricultor).
