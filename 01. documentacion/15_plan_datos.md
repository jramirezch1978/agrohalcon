# Plan de datos — AllpaShift (Field Shift)

## ✅ Datasets OFICIALES publicados por NASA (pestaña Resources, leída el 2026-11-13)

**NASA (sirven para Perú, cobertura global):**
| Dataset | Lo que dice NASA que aporta |
|---|---|
| **SMAP** | Humedad superficial del suelo cada 2–3 días: estrés por sequía, infiltración, señales tempranas de estrés |
| **GPM / IMERG** | Lluvia global: confiabilidad de lluvias, tormentas extremas, riesgo de erosión, tendencias (capas descargables en Worldview) |
| **Landsat (30 m) y MODIS/VIIRS (250–1000 m)** | NDVI e índices de vegetación: vigor, transiciones estacionales, suelo desnudo, periodos de estrés |
| **NASA POWER** | Temperatura, humedad, radiación e indicadores para uso de agua del cultivo, temporada, heladas, aptitud climática |
| **SRTM** | Elevación y pendiente: escorrentía, erosión, flujo de agua |
| **ECOSTRESS** | Temperatura de superficie y evapotranspiración de alta resolución: puntos calientes de estrés, demanda de agua |
| **NLDAS / GLDAS** | Temperatura, lluvia, humedad del suelo, evapotranspiración en series continuas (**GLDAS es global**; buscar en Earthdata Search) |

**Complementarios globales (útiles para el norte del Perú):**
| Dataset | Uso |
|---|---|
| **FAO GAEZ** (Global Agro-Ecological Zones) | ⭐ Aptitud agroclimática **por cultivo** a nivel mundial, limitaciones de suelo, agua, rendimiento potencial → **base ideal del mapa de aptitud por colores** |

**Solo Estados Unidos (no aplican a Perú; usar como referencia de método):** USDA Ag Data Commons, Web Soil Survey, CropScape (CDL), PRISM, SSURGO/STATSGO2, NAIP, NLCD, CoCoRaHS, NWIS, USDA AMS Market News, NASS QuickStats, OpenET, LANDFIRE.
→ Equivalentes peruanos: MIDAGRI (calendarios, SISAP precios), SENAMHI (estaciones), INEI, ISRIC SoilGrids (suelos, global).

**Conclusión:** nuestra selección (POWER, MODIS, SMAP, GPM, ECOSTRESS, SRTM) **coincide con la lista oficial**. Añadir **FAO GAEZ** para el mapa de aptitud y **GLDAS** como respaldo de humedad del suelo.

---

> Borrador del 2026-11-10. Se ajusta el 13 nov cuando NASA publique los datasets oficiales (pestaña Resources del reto).
> Regla: el código del proyecto empieza el 14 nov; antes solo se prepara (cuentas, fuentes, información local).

## 1. Qué tiene que poder responder la app

Para una parcela de Piura (coordenadas) y las prioridades del agricultor:
1. ¿Cómo han sido el clima y el agua aquí en los últimos 20–40 años? ¿Hay tendencia?
2. ¿En qué meses el campo queda descubierto y cuándo el cultivo actual sufre más (calor, sequía, exceso de lluvia)?
3. ¿Qué pasa en un año El Niño frente a un año normal?
4. Comparar **3 rotaciones (incluida la actual)**: beneficios, sacrificios, riesgos, vacíos de información e **incertidumbre**.

## 2. Datos de NASA

| Prioridad | Dataset | Variable | Para qué en la app | Acceso | Estado |
|---|---|---|---|---|---|
| ⭐ Imprescindible | **NASA POWER** | `PRECTOTCORR` lluvia · `T2M`, `T2M_MAX`, `T2M_MIN` temperatura · `GWETROOT`, `GWETTOP` humedad del suelo · `ALLSKY_SFC_SW_DWN` radiación · `EVPTRNS` / `EVLAND` evapotranspiración · `RH2M` humedad | Historial 1981–hoy, tendencias, estrés por calor, balance hídrico, años El Niño | API JSON sin clave | ✅ Probado |
| ⭐ Imprescindible | **MODIS MOD13Q1** (ORNL DAAC) | NDVI / EVI 250 m cada 16 días | Salud de la vegetación, meses de campo descubierto, estrés del cultivo | API REST sin clave | ✅ Probado |
| ⭐ Imprescindible | **SMAP** (SPL3SMP_E / SPL4SMGP) | Humedad del suelo superficial y de raíz | Anomalías de humedad, riesgo de sequía | Earthdata Login | ✅ Metadatos probados |
| 🟡 Recomendado | **GPM IMERG** | Lluvia diaria/mensual ~10 km | Lluvias extremas (El Niño), validar POWER | Earthdata Login | ✅ Metadatos probados |
| 🟡 Recomendado | **ECOSTRESS** | Temperatura de superficie, evapotranspiración, estrés hídrico | Estrés térmico del cultivo, uso de agua | Earthdata / AppEEARS | ⏳ Por probar |
| 🟡 Recomendado | **SRTM** (o ASTER GDEM) | Elevación y pendiente | Riesgo de erosión e inundación por parcela | Earthdata Login | ✅ Metadatos probados |
| 🔵 Opcional | **Landsat 8/9** | NDVI 30 m | Detalle a nivel de parcela | Earthdata / USGS | ⏳ |
| 🔵 Opcional | **GRACE / GRACE-FO** | Agua almacenada total | Tendencia del agua subterránea en la región | Earthdata Login | ⏳ |
| 🔵 Opcional | **GEDI** | Biomasa | Contribución de materia orgánica | Earthdata Login | ⏳ |
| 🔵 Opcional | **NASA FIRMS** | Focos de quema | Quemas agrícolas (riesgo para el suelo) | CSV público | ✅ Probado |

## 3. Datos complementarios (no NASA)

| Dato | Fuente | Para qué | Responsable |
|---|---|---|---|
| Suelos: pH, carbono orgánico, textura | **ISRIC SoilGrids** (API) | Aptitud del suelo y salud del suelo | Lucía / Jhonny |
| Calendario de siembra y cosecha de cultivos de Piura | **MIDAGRI** (calendarios agrícolas), Agencia Agraria Piura | Meses de campo descubierto, rotación realista | Lucía |
| Requerimiento de agua por cultivo (coeficiente Kc) | **FAO-56** | Demanda de agua de cada rotación | Lucía / David |
| Características de cultivos (fijador de nitrógeno, cobertura, raíz profunda, tolerancia a sequía) | FAO, INIA | Beneficios de cada rotación | Lucía |
| Índice El Niño (ONI) | **NOAA** CPC / **ENFEN** Perú | Marcar años El Niño / La Niña | David |
| Precios y mercados | **MIDAGRI – SISAP** | Aptitud de mercado e ingreso extra | Edwin / David |
| Estaciones meteorológicas | **SENAMHI** | Validar datos satelitales con datos de campo | David (opcional) |
| Límites de distritos y valles (Chira, Piura, San Lorenzo) | INEI / GeoGPS Perú | Mapa base | Lucía |

## 4. Indicadores que calcula el backend

| Indicador | Cómo | Datos |
|---|---|---|
| Balance hídrico mensual | lluvia − evapotranspiración | POWER / GPM / ECOSTRESS |
| Anomalía de humedad del suelo | valor del mes − promedio histórico del mes | SMAP / POWER `GWETROOT` |
| Estrés por calor | días con `T2M_MAX` sobre el umbral del cultivo | POWER |
| Meses de campo descubierto | NDVI bajo de forma sostenida | MODIS |
| Tendencia significativa | Mann-Kendall + pendiente de Sen | POWER (1981–hoy) |
| Riesgo El Niño | comportamiento en años ONI ≥ +0.5 vs normales | POWER + ONI |
| Riesgo de erosión | pendiente + lluvia extrema + meses descubiertos | SRTM + GPM + MODIS |
| Puntaje de rotación | ponderado según prioridades del agricultor (agua, suelo, ingreso) | todos |
| Incertidumbre | variabilidad entre años y diferencia entre fuentes (POWER vs GPM) | todos |

## 5. Cobertura de los 7 puntos de la demo

| # | Punto | Datos / evidencia |
|---|---|---|
| 01 | Problema | Lluvia de El Niño 1998 y 2017 vs año normal (POWER); tendencia de temperatura (POWER) |
| 02 | Desafío | Texto oficial del reto Field Shift (archivo 12) |
| 03 | Datos NASA | Tabla de la sección 2 (dataset, variable, uso, enlace) |
| 04 | Solución | 3 rotaciones comparadas con su puntaje e incertidumbre |
| 05 | Funcionamiento | Diagrama: coordenadas → APIs NASA → indicadores (sección 4) → recomendación |
| 06 | Demostración | Caso real: parcela de mango o limón en el valle de San Lorenzo / Chira |
| 07 | Impacto | Agua ahorrada, meses de suelo protegido, riesgo reducido; escalable a otras regiones |

## 6. Preparación antes del 14 nov

- [ ] Todos: cuenta en **Earthdata Login** (urs.earthdata.nasa.gov).
- [ ] Lucía: calendarios de siembra de Piura, cultivos principales por valle, rotaciones que se usan hoy, Kc de FAO-56.
- [ ] David: serie del índice ONI (años El Niño / La Niña) y repaso de Mann-Kendall.
- [ ] Jhonny: probar ECOSTRESS y SMAP con Earthdata; definir la caché del backend.
- [ ] 13 nov: revisar los datasets oficiales publicados y ajustar este plan.
