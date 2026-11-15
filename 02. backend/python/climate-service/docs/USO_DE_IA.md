# Uso de IA en la parte Python (insumo para el campo *Use of AI* de la entrega)

El PDF *AgroShift: Uso de IA y datos de la NASA* dice: *“Declaramos todas las herramientas de IA usadas durante el proyecto”* y deja la tabla
con la fila `[Completar]`. Esta es la fila que corresponde a la parte de David (Python), para que **Edwin** la pase a inglés y la copie al formulario.
Ajústala al final del hackatón con lo que realmente se haya usado.

| Herramienta | Para qué la usamos | Cómo la aplicamos |
|---|---|---|
| Claude Code (Anthropic) | Asistente de código durante el desarrollo del servicio de cálculo en Python (FastAPI): estructura del servicio, pruebas automáticas, scripts de descarga de datos NASA y NOAA, capa de bases de datos (SQLite y SQL de PostgreSQL), panel técnico, guardas del asistente de IA y documentación técnica | David le pidió el código y los scripts, **revisó y validó** lo generado y lo probó con pruebas automáticas y con datos reales de NASA POWER. Las reglas de riesgo y los umbrales los define y verifica el equipo (`app/thresholds.py`). Claude Code **no** calcula ni decide nada dentro de la app en funcionamiento |

## La IA que sí corre dentro de la app: Groq con `openai/gpt-oss-20b`
> **Dónde corre hoy (14-nov, noche):** en la API **Java** (`AsistenteService` y `GroqClient` de `agro-service`; la clave `GROQ_API_KEY` en ese contenedor). Lo de abajo describe además la versión de este servicio Python (`POST /asistente/preguntar`), que quedó como alternativa no usada. Groq es el servicio de inferencia (groq.com), no Grok (la IA de xAI): el modelo es `openai/gpt-oss-20b` y se usa su plan gratuito porque el equipo no tiene capacidad para ejecutar el modelo. El plan gratuito tiene topes bajos (8 000 tokens/min, 200 000/día, por clave); ver el punto 30 de `DECISIONES_ABIERTAS.md`.
**Decisión del equipo (14-nov-2026):** seguimos con Groq, pero con el modelo `openai/gpt-oss-20b` porque su licencia es **Apache 2.0** (código abierto, como piden los términos de la NASA para lo de terceros), y se llama **desde el servicio Python** y no desde la app: el código del proyecto es público y la clave de la API no puede quedar expuesta. La clave `GROQ_API_KEY` vive solo en el servidor (`.env` / `deploy/vps/.env`); sin ella el asistente responde con plantillas.
Controles de abuso (con el código público, cualquiera que llegue al servicio podría gastar la cuota): máximo 400 caracteres por pregunta, límite por cliente y por minuto, límite global y tope diario (`GROQ_MAX_*`), y todo fallo de Groq (HTTP 429/5xx, tiempo agotado, respuesta vacía) cae al Plan B sin romper la app. La clave nunca aparece en respuestas, registros ni mensajes de error (hay pruebas que lo verifican).

### Cómo se controla la IA (guardas)
El servicio Python no usa IA para calcular; rodea a la IA de la app con guardas verificables (`app/asistente.py`, con pruebas en `tests/test_asistente.py`):
1. **Prompt cerrado:** reglas del sistema + solo los datos ya calculados + la pregunta del agricultor, que no puede cerrar las etiquetas ni dar órdenes.
2. **Validación de la respuesta:** se rechaza todo número, cultivo o satélite que no esté en los datos calculados.
3. **Plan B sin IA:** si Groq falla o la respuesta no pasa la validación, la app muestra una explicación armada con plantillas a partir de los mismos datos.

## Límite de la IA en AgroShift (no cambia)
Todos los indicadores, puntajes y recomendaciones los calcula el servicio Python con reglas verificables y datos de la NASA. La IA en producción (Groq, `openai/gpt-oss-20b`,
llamada desde el servicio Python) **solo redacta** en lenguaje sencillo lo que la app ya calculó. Lo generado con asistentes de código fue **revisado y validado** por el equipo.

> Antes del Submit: confirmar con el equipo qué otras herramientas de IA se usaron (chatbots, generación de imágenes, traducción) y agregarlas a esta tabla y al campo *References → Herramientas de inteligencia artificial*.
