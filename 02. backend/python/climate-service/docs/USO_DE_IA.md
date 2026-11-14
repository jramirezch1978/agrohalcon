# Uso de IA en la parte Python (insumo para el campo *Use of AI* de la entrega)

El PDF *AgroShift: Uso de IA y datos de la NASA* dice: *“Declaramos todas las herramientas de IA usadas durante el proyecto”* y deja la tabla
con la fila `[Completar]`. Esta es la fila que corresponde a la parte de David (Python), para que **Edwin** la pase a inglés y la copie al formulario.
Ajústala al final del hackatón con lo que realmente se haya usado.

| Herramienta | Para qué la usamos | Cómo la aplicamos |
|---|---|---|
| Claude Code (Anthropic) | Asistente de código durante el desarrollo del servicio de cálculo en Python (FastAPI): estructura del servicio, pruebas automáticas, scripts de descarga de datos NASA y NOAA, capa de bases de datos (SQLite y SQL de PostgreSQL), panel técnico, guardas del asistente de IA y documentación técnica | David le pidió el código y los scripts, **revisó y validó** lo generado y lo probó con pruebas automáticas y con datos reales de NASA POWER. Las reglas de riesgo y los umbrales los define y verifica el equipo (`app/thresholds.py`). Claude Code **no** calcula ni decide nada dentro de la app en funcionamiento |

## Cómo se controla la IA que sí corre dentro de la app (Llama vía Groq, a cargo de Jhonny)
El servicio Python no usa IA para calcular; rodea a la IA de la app con guardas verificables (`app/asistente.py`, con pruebas en `tests/test_asistente.py`):
1. **Prompt cerrado:** reglas del sistema + solo los datos ya calculados + la pregunta del agricultor, que no puede cerrar las etiquetas ni dar órdenes.
2. **Validación de la respuesta:** se rechaza todo número, cultivo o satélite que no esté en los datos calculados.
3. **Plan B sin IA:** si Groq falla o la respuesta no pasa la validación, la app muestra una explicación armada con plantillas a partir de los mismos datos.

## Límite de la IA en AgroShift (no cambia)
Todos los indicadores, puntajes y recomendaciones los calcula el servicio Python con reglas verificables y datos de la NASA. La IA en producción (Llama vía Groq,
a cargo de Jhonny) **solo redacta** en lenguaje sencillo lo que la app ya calculó. Lo generado con asistentes de código fue **revisado y validado** por el equipo.

> Antes del Submit: confirmar con el equipo qué otras herramientas de IA se usaron (chatbots, generación de imágenes, traducción) y agregarlas a esta tabla y al campo *References → Herramientas de inteligencia artificial*.
