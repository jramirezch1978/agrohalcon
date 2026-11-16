# ¿Qué hace AllpaShift?

> *Allpa* = tierra (quechua) · *Shift* = cambio (reto **Field Shift: Adapting Farms with NASA Data**, NASA Space Apps Challenge 2026).
> Equipo **Halcón Dorado** · Sede Piura.

## En una frase

**AllpaShift le dice al agricultor qué sembrar, cuándo y qué hacer esta quincena, según el riesgo climático que muestran los satélites de la NASA para su valle.**

## El problema

En el norte del Perú se siembra por costumbre. Cuando llega una sequía, un calor extremo o un **El Niño costero** como el de 2017, se pierde la campaña:
- En **marzo de 2017** llovió entre **5 y 9 veces lo normal** en los valles de Piura (GPM IMERG).
- Ese evento **no lo vio el índice global ONI**, que lo marcó como "neutral".

El agricultor necesita saber antes cuál es el riesgo y qué alternativa le conviene.

## Qué hace la app

| # | Función | Cómo funciona |
|---|---|---|
| 1 | **Ubicar la parcela** | El agricultor toca el mapa o usa el GPS. La app identifica su valle (Bajo Piura, Chira, San Lorenzo, Alto Piura, Sechura, Huancabamba... 18 valles del norte) |
| 2 | **Leer los satélites** | Consulta datos NASA de ese punto: lluvia (**GPM IMERG**, 11 km), humedad del suelo (**SMAP**, 9 km), clima histórico (**NASA POWER**), vegetación (**MODIS NDVI**, 250 m), temperatura del mar (**MUR SST**) y relieve (**SRTM**) |
| 3 | **Calcular el riesgo** | Compara con lo normal (1991-2020) y mide el riesgo de sequía, de lluvia extrema, de calor y de El Niño costero |
| 4 | **"¿Qué hago esta quincena?"** | Según el mes y la quincena, dice en qué fase está cada cultivo (siembra, crecimiento, floración, cosecha, poda) y qué acciones tomar, con la alerta NASA que las justifica |
| 5 | **Comparar rotaciones** | Para cultivos anuales (arroz, maíz, menestras, algodón, hortalizas), compara la rotación actual con 2 alternativas: beneficios, sacrificios, riesgo e incertidumbre (requisito del reto) |
| 6 | **Perspectiva de la campaña** | Muestra una barra de meses, de la siembra a la cosecha, con el riesgo de cada mes en 🟢 verde, 🟡 ámbar o 🔴 rojo |
| 7 | **Cultivos permanentes** | Mango, limón, uva de mesa, banano, palta, café y cacao no rotan: reciben **acciones** por fase (riego, poda, protección ante lluvias, cosecha anticipada) |
| 8 | **Máquina del tiempo** | Muestra qué habría recomendado AllpaShift antes del Niño Costero 2017. Es la prueba de que funciona |
| 9 | **Asistente que explica** | Una IA traduce el resultado a palabras simples. Los cálculos salen de los datos NASA; la IA no los inventa |

## Para quién

- **Pequeños y medianos agricultores** de los valles del norte: arroz, maíz, menestras, limón, mango, uva, banano.
- **Técnicos agrarios** de la DRAP, las agencias agrarias y las juntas de usuarios de riego.
- **Agroexportadores** de uva, mango y limón que planifican la cosecha ante El Niño.

## Cobertura

- **Regiones:** Tumbes, Piura, Lambayeque, La Libertad, Cajamarca, Amazonas y San Martín. La lógica funciona con **cualquier coordenada del planeta**, porque los datos NASA son globales.
- **Cultivos:** 37 en el catálogo:
  - **Cereales:** arroz, maíz amarillo duro y amiláceo, trigo, cebada, quinua.
  - **Menestras:** frijol caupí, frijol, arveja, zarandaja.
  - **Frutales:** mango, limón, uva de mesa, banano, plátano, mandarina, palta, arándano, maracuyá, papaya, granadilla.
  - **Hortalizas:** sandía, melón, cebolla, ají páprika, tomate, zanahoria, alcachofa, espárrago.
  - **Tubérculos y raíces:** papa, camote, yuca, olluco.
  - **Industriales:** algodón Pima, caña de azúcar, café, cacao.

## Cómo está hecha

| Capa | Tecnología |
|---|---|
| App web | Vue 3 + Leaflet (mapa) + ECharts (gráficos) |
| App móvil | Capacitor 6 (APK de Android y paquete de iOS) |
| API | Java 17 + Spring Boot (api-gateway + agro-service) |
| Datos NASA y riesgo | Python + FastAPI (climate-service) |
| Base de datos | PostgreSQL 17 (modelo en [26_modelo_base_de_datos](26_modelo_base_de_datos.md)) |
| Infraestructura | Docker en un VPS Hetzner: https://allpashift.crisaor.org |

## Uso de IA (declarado)

- El equipo usó asistentes de IA para programar, documentar y buscar datos.
- En la app, la IA solo **explica** resultados calculados con datos NASA.
- Esto se declara en la entrega, como exige la guía.
