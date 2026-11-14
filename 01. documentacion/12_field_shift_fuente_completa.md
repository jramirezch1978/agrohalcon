# Field Shift — fuente completa (página oficial + video)

> Archivo de referencia consolidado para consulta del equipo y de Claude.
> Página: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/ (leída el 2026-11-07)
> Video: https://www.youtube.com/watch?v=cF0U2WXsM7o — "2026 Challenge | Field Shift: Adapting Farms with NASA Data", canal NASA Space Apps Challenge, 3:37, publicado el 29 oct 2026. Incluye imágenes generadas.
> Datasets oficiales de la pestaña Resources: se publican el **13 nov 2026** (a la fecha de lectura no estaban).

---

## 1. Ficha del reto

| Campo | Valor |
|---|---|
| Nombre | Field Shift: Adapting Farms with NASA Data |
| Nombre en el formulario de Piura | Cambio de rumbo: Adaptando las granjas con datos de la NASA |
| Evento | 2026 NASA Space Apps Challenge |
| Dificultad | Advanced, Intermediate |
| Temas | Arts & Multimedia, Earth Science, Software |

## 2. Texto de la página oficial (en inglés, tal cual)

### Summary
Farmers around the world navigate shifting temperatures, changing rainfall patterns, water shortages, extreme weather, and declining soil health. These pressures make it difficult to choose crop rotations that protect fields, conserve water, and support long‑term resilience. Your challenge is to create a decision‑support tool that uses NASA Earth observations along with local soil information, crop characteristics, and farmer priorities to help farmers explore rotation strategies that could strengthen soil health and adapt their farms to changing conditions.

### Background
Farmers face increasingly complex decisions as temperatures shift, rainfall becomes less predictable, and soil health declines across many regions. Water shortages, erosion, nutrient depletion, and extreme weather events add further uncertainty. Selecting new crops to add to a rotation can be difficult, because a crop that improves soil health in one place may consume too much water, introduce disease, conflict with local markets, or fall outside expected growing seasons somewhere else.

This challenge is inspired in part by multigenerational farming experience — many families have lived through seasons where better tools for tracking changing conditions could have helped identify healthier, more resilient rotation choices. Today, NASA's long‑term environmental datasets offer new ways to understand local growing conditions, and SI techniques open opportunities to translate that data into practical, farmer‑friendly insights.

### Objectives
You may consider combining NASA Earth observations with local agricultural information to create an app, model, interactive map, or other decision‑support tool. The goal is to help farmers explore crop‑rotation options that may improve soil health and strengthen resilience to changing weather and water conditions.

You may explore NASA datasets such as SMAP, ECOSTRESS, GPM, Landsat, MODIS, NASA POWER, GRACE and GRACE‑FO, and SRTM or other NASA elevation products. Using these datasets, you may analyze patterns in temperature, heat stress, rainfall, soil moisture, evaporation, frost risk, extreme precipitation, vegetation stress, and long‑term water trends. You may also consider local soil information, crop characteristics, and farmer priorities—such as water use, forage value, nitrogen‑fixing potential, erosion reduction, organic matter improvement, or market suitability.

Your tool may highlight times when fields are typically bare, seasons when current crops appear more vulnerable, or opportunities for rotations that could interrupt pest cycles, reduce water demand, improve infiltration, or add supplemental income. You may compare at least three rotation strategies, including the existing rotation. For each strategy, you may explain why it was suggested, what evidence supports it, what benefits it may offer, where information gaps exist, and any risks that would need local review by farmers or agricultural experts.

The intended outcome is a supportive tool — one that helps identify patterns and possibilities, but does not replace farmer judgment or local agricultural expertise.

### Potential Considerations
You may (but are not required to) consider the following:

**Understanding Conditions & Data**
- Explore how changes in temperature, soil moisture, rainfall, evaporation, and vegetation stress relate to crop vulnerability and soil health.
- Consider explaining scientific terms such as evapotranspiration, soil moisture anomalies, vegetation indices (e.g., NDVI), frost risk, and water‑balance indicators.
- Clarify how satellite observations differ from ground‑based measurements, and how combining both may improve accuracy.

**SI, Modeling, and Data Fusion**
- You may compare different SI or statistical approaches for identifying patterns in historical climate and soil conditions.
- Consider how SI could highlight seasonal transitions, bare‑field periods, or times when current crops show increased stress.
- Explain how the model interprets uncertainty and where local expertise would be needed to validate results.
- You may consider harmonizing datasets with different spatial and temporal resolutions by downsampling, aggregating, or resampling them to a common analysis grid. Harmonizing resolution can help the SI combine SMAP soil moisture, ECOSTRESS land‑surface temperature, GPM precipitation, Landsat/MODIS vegetation indices, GEDI biomass, and soil datasets into coherent features that support clear, explainable rotation‑strategy comparisons.

**Rotation Strategy Exploration**
- Compare rotation scenarios by examining nutrient cycling, erosion risk, organic matter contributions, pest‑cycle disruption, water use, forage potential, or market considerations.
- You may consider mapping which rotation ideas best align with farmer priorities—such as conserving water, generating supplemental income, or improving soil structure.
- Include brief explanations of how nitrogen‑fixing crops, cover crops, deep‑rooting crops, or drought‑tolerant crops contribute to long‑term soil health.

**Geospatial Mapping & Visualization**
- Consider whether interactive maps could help users explore trends over time such as long‑term soil moisture, heat waves, or water‑storage declines.
- Explore ways to visualize field‑level vulnerabilities (e.g., zones of erosion risk, water stress hotspots, frost‑prone areas).
- You may include optional add‑ons such as timelines, overlays comparing datasets, or scenario sliders that adjust rainfall or temperature patterns.

**Farmer‑Centered Design**
- Consider how to make the tool easily interpretable for farmers who may have limited technical or geospatial experience.
- Think about ways to allow farmers to input their own priorities or constraints, such as water availability, equipment limitations, or market preferences.
- Share reminders that the tool is intended to support—not replace—local expertise, and highlight where human judgment is particularly important.

For data and resources related to this challenge, refer to the Resources tab at the top of the page. More resources may be added before the hackathon begins.

> Nota: "SI" (Super Intelligence) es el término que NASA usa desde el 29 sep 2026 en lugar de "AI/IA".

## 3. Transcripción del video (subtítulos automáticos en español, limpiados)

**[0:08–0:32]** En un universo lleno de mundos, hay uno que entendemos mejor que cualquier otro. Y aun así, miremos más de cerca: incluso aquí, las condiciones bajo nuestros pies están cambiando. El calor cambia, las lluvias varían, el agua es menos segura, el suelo pierde nutrientes, y los agricultores deben decidir qué sigue.

**[0:57–1:01]** Pero la Tierra nos envía señales constantemente, y los datos públicos de observación terrestre de la NASA nos dan nuevas formas de escuchar. Lluvias, humedad del suelo, calor, vegetación, agua. Diferentes observaciones, diferentes escalas, piezas de la misma historia.

**[1:22–1:33]** Su misión: convertir estas observaciones en una herramienta que ayude a explorar lo que podría venir después. Comparen rotaciones, revelen beneficios y sacrificios, entiendan los riesgos, hagan visible la incertidumbre. Creen un modelo de SI, un mapa interactivo, una visualización, una herramienta de apoyo a decisiones, o construyan algo que ninguno de nosotros ha imaginado aún.

**[1:55]** No necesitamos viajar a otro mundo para encontrar un desafío digno de exploración. La misión está aquí. ¿Qué crearán ustedes?

**[2:03–2:34]** *(Autora del reto; su nombre no quedó en los subtítulos)* … y soy la autora del Space Apps Challenge 2026, Field Shift: Adaptando cultivos con datos de la NASA. Como ingeniera y desarrolladora en el Centro Espacial Johnson de la NASA, apoyo la gestión e integración de la misión Artemis, así como la integración de carga útil para la base lunar. Apoyo la órbita terrestre baja para la investigación y la integración de misiones, y los esfuerzos iniciales de desarrollo del reactor espacial Freedom, la primera misión nuclear a Marte. Estoy increíblemente emocionada de que se hayan unido a nuestro desafío, y no puedo esperar a ver lo que construyan. ¡Vamos equipo!

**[2:35–2:52]** Hola, soy Manideep Gogineni, del Centro Espacial Johnson de la NASA. Como arquitecto de soluciones de datos, apoyo la gestión e integración de la misión Artemis mediante arquitectura de soluciones de datos, desarrollo de aplicaciones web personalizadas y herramientas innovadoras que permiten flujos de trabajo de carga útil para Artemis y la base lunar, así como operaciones en órbita terrestre baja.

**[2:54–3:12]** Hola, soy William Stefanov, del Centro Espacial Johnson de la NASA, donde soy científico principal del sistema terrestre; trabajo con imágenes de la Tierra desde la Estación Espacial Internacional para tareas de respuesta ante desastres y también para apoyar la ciencia de teledetección. Soy experto en la materia para el desafío Field Shift: Adaptando cultivos con datos de la NASA.

**[3:14–3:35]** Hola, soy Alex Token *(posible error del subtitulado)*, y soy científico de datos en el Centro Espacial Johnson de la NASA, en la Unidad de Ciencias de la Tierra y Teledetección. Soy experto en el campo del aprendizaje automático y me he centrado durante los últimos años en procesar y extraer información de la fotografía de la Tierra tomada por astronautas, incluyendo la aplicación de modelos de aprendizaje automático a estos datos para extraer información útil que otros científicos puedan utilizar. Estoy emocionado de ser parte de este desafío.

## 4. Contenido y lectura del video

- **Tono:** narrativo e inspirador, con imágenes generadas por IA ("GENERATED CONTENT", estética de transmisión de señal).
- **Mensaje central:** la "misión espacial" está en la Tierra; los datos de NASA son "señales" que hay que convertir en decisiones agrícolas.
- **Cinco variables que nombra:** lluvia, humedad del suelo, calor, vegetación, agua.
- **Cuatro verbos que definen lo esperado:** *comparar* rotaciones · *revelar* beneficios y sacrificios · *entender* riesgos · *hacer visible* la incertidumbre.
- **Formatos aceptados:** modelo de IA, mapa interactivo, visualización, herramienta de apoyo a decisiones u otra cosa nueva.
- **Expertos (JSC, NASA):** autora del reto (ingeniera, Artemis/base lunar), Manideep Gogineni (arquitectura de datos, apps web), William Stefanov (científico del sistema terrestre, SME del reto), Alex Token (ML sobre fotografía astronáutica).

## 5. Requisitos derivados para AgroHalcón (checklist)

- [ ] Usar al menos 1 dataset NASA, idealmente varios (POWER, MODIS, SMAP, GPM; probar ECOSTRESS, Landsat, GRACE, SRTM, GEDI cuando se publiquen el 13 nov).
- [ ] Integrar información local: suelos, características de cultivos (mango, limón, arroz…), prioridades del agricultor.
- [ ] Comparar **≥ 3 rotaciones, incluida la actual**: por qué, evidencia, beneficios, vacíos de información, riesgos.
- [ ] Mostrar **beneficios y sacrificios** (trade-offs) y **la incertidumbre** de cada resultado.
- [ ] Mostrar periodos de campo descubierto y de vulnerabilidad de cultivos.
- [ ] Explicar términos (evapotranspiración, NDVI, anomalías de humedad, balance hídrico) en lenguaje sencillo.
- [ ] Explicar el uso de IA (SI) y cómo se armonizaron los datasets.
- [ ] Mapa interactivo; opcional: línea de tiempo, capas comparativas, sliders de escenarios.
- [ ] Entrada de prioridades/limitaciones del agricultor (agua, equipos, mercado).
- [ ] Aviso visible: la herramienta apoya, **no reemplaza**, el criterio del agricultor ni de expertos locales.
