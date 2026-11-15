# Revisión de `calculos/` de Sheila frente al backend (14-nov-2026)

Se revisó la rama `feature/calculos-sheila` (commit `f1143f6`, carpeta `calculos/`) contra lo que el backend de verdad usa:
Java (`agro-service`) → `climate-service` (puerto 8000) → PostgreSQL de Jhonny. Todo lo de abajo se **ejecutó**, no se supuso.

> **Estado final (14-nov, noche): la integración de Sheila ya está en `develop`.** Java llama a `calculos`; se levantó toda la plataforma en una PC (Java 17, PostgreSQL embebido, frontend) y funciona de punta a punta;
> `climate-service` ya no está en el flujo de la app (decisión 29 de `DECISIONES_ABIERTAS.md`). Lo que sigue es la revisión que se hizo ANTES de esa integración.
>
> **Actualización (14-nov, 15:48): Sheila subió `feature/integracion-sheila`** (3 commits sobre `develop`, 0 de retraso, 0 conflictos con las demás ramas).
> Mueve su servicio a `02. backend/python/calculos/` (:8001), agrega `CalculosClient.java` y adapta `agro-service` para llamarlo, suma un asistente con Groq
> en Java (`AsistenteService`, `GroqClient`) y agrega el contenedor `calculos` a `docker-compose.app.yml`. **Con esa rama, el "no cuadra" de las secciones 1 y 2
> deja de aplicar a Java ↔ `calculos/`**: Java ya envía su forma de pedido (`lang`, `catalogo`) y ella agregó `/indicadores-punto`. Lo que dicen las secciones 1 y 2
> vale para `develop` y para `feature/calculos-sheila`, que es lo que se revisó con ejecución. **No se probó la rama nueva** (no hay Java 17 ni Maven en la PC de David):
> solo se leyó su código y se verificó que sus datos (`imerg_piura.json`, `mur_sst_nino12.json`) tienen el mismo contenido que los usados aquí.
> Consecuencias a decidir con Jhonny: (a) en esa rama Java **ya no llama a `climate-service`**, así que el respaldo de El Niño, las pruebas de `allpashift_api.py` y las
> correcciones de `tipo_accion()` de este servicio no estarían en el flujo de la app; hay que elegir **un** servicio de cálculo (y entonces los umbrales del punto 22 dejan de ser una discusión teórica);
> (b) `feature/calculos-sheila` y `feature/frontend-sheila` quedan superseded: abrir solo el PR de `feature/integracion-sheila` evita duplicar `calculos/` y `Frontend/`.
> Lo que se hizo con los datos (secciones 4 y 6) y la base de datos no depende de esa decisión.

## 1. Veredicto

| Pregunta | Respuesta |
|---|---|
| ¿Funciona `calculos/`? | **Sí.** Sus 94 pruebas pasan (también después de traer `develop`). Código ordenado, umbrales en YAML, fuentes honestas ("sin dato" en vez de rellenar). |
| ¿Cuadra con el backend? | **No como reemplazo.** Java no puede llamarlo: rutas, cuerpo y forma de la respuesta son distintos (sección 2). Por eso **no se despliega**; es la referencia de Sheila y su fuente de datos. |
| ¿Sirve? | **Sí, mucho.** Trae dos descargas reales de la NASA que David no pudo hacer (IMERG y MUR Niño 1+2) y reglas de campaña que se pueden aprovechar. Lo ya aprovechado está en la sección 4. |
| ¿Hay conflictos para el Pull Request? | **No.** Se probó con `git merge-tree` contra `develop` en las tres ramas (sección 5). |

## 2. Qué espera Java frente a lo que ofrece `calculos/`

Java llama **cuatro** rutas de `climate-service` (`RecomendacionService.java`, `ApiController.java`):

| Java llama | `calculos/` (Sheila, :8001) | `climate-service` (:8000) |
|---|---|---|
| `POST /calcular` con `cultivos[]` (`tempMinC`, `aguaNecesaria`, `mesesSiembra`…), `rotaciones[]`, `rotacionActualId` | Existe, pero lee `catalogo[]` con `temp_min`, `agua`, `duracion_meses`. **Ignora `cultivos` en silencio** y usa `data/catalogo_ejemplo.json`: el catálogo de Alejandro nunca llegaría. | ✅ Cuerpo de Java tal cual |
| Respuesta `{datosNasa, recomendacion, contrato}` | Respuesta plana (`indicadores`, `rotaciones`, `queHacer`…) sin esos tres campos: Java leería `recomendacion = null`. | ✅ |
| `POST /indicadores-punto` (mapa por valle) | No existe (tiene `POST /mapa` con zonas fijas de un YAML) | ✅ |
| `POST /validacion` con `eventos[]` | Es `GET /validacion?anio&lat&lon` | ✅ |
| `POST /asistente/plan-b` | No existe | ✅ |

Otras diferencias: su servicio es asíncrono y consulta NASA POWER por dentro (Java no recibe los datos crudos para grabarlos en
`nasa.datos_nasa`, que es la regla 5 del doc 29); usa `pandas` y `PyYAML` (no están en la imagen de Docker); escucha en el 8001.

**Conclusión técnica:** no hay que "arreglar" `calculos/` para que Java lo llame. El servicio que Java llama es `climate-service`
(con los endpoints `/calcular`, `/indicadores-punto`, `/validacion` que agregó Jhonny en `app/allpashift_api.py`). `calculos/` se queda
como referencia y fuente de datos.

## 3. Reglas distintas: hay que decidir una (ver `DECISIONES_ABIERTAS.md`, punto 22)

| Regla | `calculos/` (Sheila) | `climate-service` (David, en producción) |
|---|---|---|
| Lluvia: nivel medio / alto | anomalía ≥ 20 % / > 40 % | ≥ 25 % / ≥ 50 % |
| Lluvia: "sin señal" si el valor y la normal están bajo | 1 mm/día | 3 mm/día |
| Humedad del suelo (solo déficit) | 20 % / 40 % | 15 % / 30 % |
| Calor (°C sobre lo normal) | +1,5 / +3,0 | +1,5 / +4,0 |
| El Niño (°C de anomalía del mar) | +0,5 / +1,5 | +0,5 / +1,5 (igual) |
| Normal climática | POWER 2001-2025 (y T2M_MAX diario de los mismos días) | POWER 1991-2020 (30 años, estándar OMM) |
| Lluvia en Piura | GPM IMERG (si hay dato) | NASA POWER |
| Riesgo por puntaje | ≥ 70 bajo · 45-69 medio · < 45 alto (igual) | igual |
| Puntaje de rotación | 100 − descuentos fijos (agua −40/−20, temperatura −10/mes, riesgo alto −10/mes, fuera de mes −15) | 100 − descuentos ponderados 65/35 por cultivo, monocultivo −5, inundación extrema −60, El Niño extraordinario −35 |

No se cambió ningún umbral: es una decisión del equipo (afecta lo que ve el agricultor). Ambos conjuntos marcan "supuesto" los valores.

## 4. Qué se tomó de `calculos/` (ya hecho y probado)

1. **GPM IMERG V07 → base de datos** (`db/aportes.py`). 12 puntos de Piura: mensual Final 2001-01…2025-09 (3 564 valores, convertidos de mm/mes a
   mm/día), diario Late de 45 días (540) y normal 2001-2020 (144). Seis puntos caen a < 5 km de un valle (Bajo, Medio y Alto Piura, Chira,
   Tambogrande, Huancabamba); los otros seis se guardan como zonas de *referencia* (ids 201-206), sin inventarles valle.
   `fuente_dato`: IMERG pasa a `en_uso`, con la nota de que **lo bajó Sheila, no David** (el token de David sigue bloqueado por el acuerdo de GES DISC).
2. **MUR SST, caja Niño 1+2, semanal 2016-05…2026-11** → `indice_climatico` (`MUR_NINO12`, `MUR_NINO12_ANOM`, 1 092 filas).
3. **Respaldo de El Niño en el servicio** (`app/datos_respaldo/nino12_historico.json`: MUR semanal 2016-2026 y NOAA CPC mensual 1982-2026). El indicador en vivo usa el ERDDAP de
   NOAA, que **no responde desde la red de David** (y puede fallar en el VPS): sin respaldo la tarjeta de El Niño desaparecía de la app.
   Ahora, si NOAA falla y la última semana tiene ≤ 21 días, se usa ese dato y el indicador lo dice en `aviso`
   (la fuente sigue siendo `MUR SST`, que es lo que el frontend reconoce). Probado en vivo: `POST /indicadores-punto` da El Niño **alto, +6,0 °C**.
4. **Contraste entre fuentes independientes** (nueva tabla `contraste_fuentes`, visible en el panel):
   - Niño 1+2: **MUR (NASA) vs NOAA CPC, r = 0,987 en anomalía y 0,993 en temperatura**, 126 meses (2016-05 a 2026-10). Dos fuentes sin relación
     cuentan el mismo Niño; MUR da +0,40 °C más de anomalía por usar otra base climática (2003-2014 vs 1991-2020).
   - Lluvia mensual: **IMERG vs POWER, r = 0,69 a 0,91** en los 6 valles, 297 meses. IMERG llueve más (+0,2 a +1,0 mm/día).
     En marzo de 2017 (Bajo Piura): IMERG 18,6 mm/día (6,1 veces su normal) y POWER 14,2 (8,6 veces la suya).
     **Lección: comparar siempre anomalías de la misma fuente, no valores entre fuentes.**
5. **Exportación al esquema del equipo** (`db/export_allpashift.py` → `04. base de datos/ddl/seed/02-datos-nasa.sql`): 18 818 datos NASA y 840 normales
   en `nasa.datos_nasa` y `nasa.normales`. **Verificado en un PostgreSQL 16.2 real** con `00-schema.sql` + `01-catalogo-norte.sql` + `02-datos-nasa.sql`,
   ejecutado con psql por stdin como `database-deploy.bat` (y dos veces seguidas: no duplica). Ver `BASE_DE_DATOS.md`.

## 5. Estado de las ramas y conflictos (`git merge-tree`, `develop` = `cd7eab4`)

| Rama | Commits propios | Conflictos al unir con `develop` | Qué se hizo |
|---|---|---|---|
| `feature/datos-python` (David) | ya estaba en `develop` (PR #1) | — | Avance rápido a `develop`; el trabajo nuevo va encima |
| `feature/calculos-sheila` | 1 (`f1143f6`), sale de `main` viejo | **0** | `develop` traído con un commit de unión (`8a2dd75`, solo local) |
| `feature/frontend-sheila` | 1 (`b30d3bf`) | **0** | `develop` traído (`194c80d`, solo local) |
| `feature/api-java`, `feature/frontend-vue`, `feature/catalogo-cultivos`, `docs/entrega` | 0 (ya están en `develop`) | — | Solo les falta avanzar a `develop` |

⚠ **`feature/frontend-sheila` no aporta nada nuevo.** Su carpeta `Frontend/` es idéntica a `03. frontend/` de `develop` salvo el renombre
AgroShift → AllpaShift, un `||` por `??` en `services/api.ts` y el `Dockerfile`/`nginx.conf` que agregó Jhonny. Hacer ese Pull Request
sumaría 158 archivos duplicados (incluido `android/`). Recomendación: **no abrirlo**; Sheila sigue en `03. frontend/`.

⚠ **`calculos/` y `Frontend/` quedan en la raíz del repositorio**, fuera de la numeración (`01.`…`05.`). Para `calculos/` se sugiere
moverla a `02. backend/python/calculos-sheila/` (Git lo registra como renombre y no pierde historia). No se movió: es su carpeta.

## 6. Pendiente (no se hizo a propósito)

- **Usar IMERG en el cálculo en vivo** (lo que hace `calculos/` para Piura). Es posible, pero cambia la lluvia que ve el agricultor y mezcla la regla de
  umbrales con otra fuente (ver el contraste de arriba). Primero decidir el punto 22.
- **`/validacion/anios` real.** Java devuelve años fijos (1998, 2017, 2023 y el último); `calculos/` calcula los años con dato real. Es cambio de Java.
- **Campaña mes a mes de Sheila** (`campana.py`: temperatura y lluvia contra lo que tolera el cultivo, con El Niño). Es más fina que `ciclo()` de Jhonny, pero
  necesita el catálogo real de Alejandro (`temp_min`, `agua_mm`, etapas); con el de prueba no se puede validar.
- **`database-deploy.bat` solo ejecuta `01-catalogo-norte.sql`.** Para que `database-deploy.bat seed` cargue también los datos NASA, hay que agregar una
  línea `call :run_sql "seed\02-datos-nasa.sql" || goto :fail` después de cada `01-catalogo-norte.sql` (rutas `create` y `seed`). No se tocó: es archivo de Jhonny.
  Mientras tanto: `psql -U <usuario> -d allpashift -v ON_ERROR_STOP=1 < "04. base de datos/ddl/seed/02-datos-nasa.sql"`.

## 7. Hallazgos en `app/allpashift_api.py` (código de Jhonny) mientras se revisaba

| Hallazgo | Estado |
|---|---|
| No tenía pruebas | Se agregaron `tests/test_allpashift_api.py` (los 3 endpoints contra el contrato de `types/api.ts`, con el cuerpo exacto que arma Java) |
| `tipo_accion()` rotulaba "sembrar" el aviso de **El Niño extraordinario** ("…consulta a un técnico agrario antes de sembrar") y no reconocía "Riega" | Corregido: esos casos ahora son `esperar` / `regar` |
| `ruff` fallaba en 2 archivos | Corregido (`ruff check .` limpio) |
| El Niño dependía solo del ERDDAP de NOAA | Respaldo agregado (punto 3 de la sección 4) |
