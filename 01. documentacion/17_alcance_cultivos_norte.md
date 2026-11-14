# Alcance ampliado — Cultivos del norte del Perú + calendario por quincena

> Decisión de Jhonny (2026-11-10): la app móvil debe decir **qué cultivo conviene en cada temporada**, **qué acciones hacer en el mes/quincena de la fecha consultada** y **en qué cultivos**, con **mapa de colores**. Cobertura: **todo el norte del Perú**, no solo Piura.
> ⚠️ Calendarios y cultivos de esta tabla son **preliminares** (conocimiento general). **Lucía debe validarlos** con los calendarios agrícolas de MIDAGRI / Agencias Agrarias antes del 14 nov.

## 1. ¿El reto obliga a usar solo Piura?

**No.** El Challenge Statement habla de "farmers around the world": la herramienta debe funcionar en cualquier lugar. Piura es nuestro **caso de demostración** (impacto local), pero cubrir el norte del Perú suma en *impacto* y *Local Impact* y demuestra que escala.

## 2. Regiones y zonas agroclimáticas

| Región | Costa (valles irrigados, seca; lluvias ene–abr en años El Niño) | Sierra (lluvias oct/nov–abr) | Selva alta / ceja de selva (lluvias casi todo el año) |
|---|---|---|---|
| **Tumbes** | Banano orgánico, arroz, limón, maíz amarillo duro | — | — |
| **Piura** | Mango, limón, arroz, banano orgánico, uva de mesa, palta, algodón Pima, maíz amarillo duro, menestras (caupí, zarandaja), cacao (Alto Piura) | Papa, maíz amiláceo, trigo, café (Huancabamba, Ayabaca) | — |
| **Lambayeque** | Arroz, caña de azúcar, maíz amarillo duro, limón, mango, palta, menestras | Papa, maíz amiláceo (Incahuasi, Cañaris) | — |
| **La Libertad** | Caña de azúcar, espárrago, palta, arándano, uva, alcachofa, arroz (Pacasmayo) | Papa, trigo, cebada, maíz amiláceo | — |
| **Cajamarca** | Arroz (valle del Jequetepeque) | Papa, maíz amiláceo, trigo, cebada, arveja, pastos (ganadería lechera) | Café, cacao, arroz (Jaén, San Ignacio) |
| **Amazonas** | — | Papa, maíz amiláceo | Café, cacao, arroz (Bagua, Utcubamba), plátano |
| **San Martín** | — | — | Arroz, café, cacao, plátano, palma aceitera, maíz amarillo duro |

## 3. Calendario preliminar de fases (por mes)

Leyenda: **S** siembra / trasplante · **C** crecimiento · **F** floración · **K** cosecha · **D** descanso o poda

| Cultivo (zona) | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Arroz (costa norte, campaña principal) | S | S/C | C | C | K | K | D | D | D | D | D | S |
| Mango (Piura, Lambayeque) | K | K | K/D | D | D | C | F | F | F/C | C | K | K |
| Limón (Piura, Tumbes) | K | K | K | K | K | C | C | F | F | C | C | K |
| Uva de mesa (Piura) | D | D/poda | C | C | F | C | C | C | C | K | K | K |
| Banano orgánico (Tumbes, Piura) | K | K | K | K | K | K | K | K | K | K | K | K |
| Palta (costa norte) | C | C | K | K | K | K | C | F | F | C | C | C |
| Maíz amarillo duro (costa) | S | C | C | K | K | S | C | C | K | K | S | C |
| Caña de azúcar | K | K | K | K | K | K | K | K | K | K | K | K |
| Espárrago (La Libertad) | K | K | K | K | C | C | K | K | K | K | K | K |
| Arándano (La Libertad) | C | C | C | C | F | F | K | K | K | K | K | C |
| Papa (sierra) | C | C | F/C | K | K | K | D | D | D | S | S | S/C |
| Maíz amiláceo (sierra) | C | C | F | C | K | K | D | D | D | S | S | C |
| Café (selva alta) | C | C | F/C | K | K | K | K | K | C | F | C | C |
| Cacao (selva alta, Alto Piura) | C | C | K | K | K | K | C | C | C | F | F | C |
| Menestras / caupí (costa) | C | K | K | S | S | C | C | K | K | D | D | S |

## 4. Acciones recomendadas por fase (base para la app)

| Fase | Acciones típicas | Alertas con datos NASA |
|---|---|---|
| Preparación / siembra | Análisis de suelo, nivelación, abonado de fondo, elegir variedad | Humedad del suelo (SMAP/POWER) para decidir la fecha; pronóstico de lluvia extrema (GPM, El Niño) |
| Crecimiento | Riego según balance hídrico, fertilización nitrogenada, control de malezas | Anomalía de humedad del suelo → regar o no; NDVI bajo → estrés |
| Floración | Evitar estrés hídrico, polinización, control de plagas | Estrés por calor (T2M_MAX, ECOSTRESS) |
| Cosecha | Planificar mano de obra y mercado | Lluvia en los próximos días (GPM) → adelantar o proteger cosecha |
| Descanso / poda | Cultivo de cobertura o fijador de nitrógeno (rotación), incorporar materia orgánica | Meses de campo descubierto (NDVI) → riesgo de erosión (SRTM + lluvia) |

## 5. Funcionalidad móvil "¿Qué hago esta quincena?"

1. El agricultor abre la app → GPS o toca el mapa → región, zona (costa/sierra/selva) y valle.
2. La app toma la **fecha actual (o la elegida)** → mes y quincena (1ª: días 1–15 · 2ª: días 16–fin).
3. Muestra:
   - **Cultivos aptos para sembrar ahora** en esa zona.
   - **Cultivos ya instalados**: fase actual + **acciones de esta quincena**.
   - **Alertas NASA** del momento (humedad del suelo, calor, lluvia, El Niño).
4. **Mapa de colores** por cultivo seleccionado:
   - 🟢 Apto · 🟡 Apto con manejo (riego, drenaje, variedad) · 🔴 No recomendado
   - Calculado por celda de grilla con clima (POWER), suelo (SoilGrids), pendiente (SRTM) y vegetación (MODIS).
5. **Comparador de rotaciones** (requisito del reto): rotación actual vs 2 alternativas, con beneficios, sacrificios, riesgos e incertidumbre.

## 6. Modelo de datos (catálogo que prepara Lucía)

```json
{
  "cultivo": "Mango",
  "regiones": ["Piura", "Lambayeque"],
  "zona": "costa",
  "rango_temperatura_c": [20, 35],
  "agua_mm_anual": [800, 1200],
  "kc_fao56": {"inicial": 0.6, "medio": 0.85, "final": 0.75},
  "tipo": ["perenne"],
  "aporta_suelo": [],
  "fases": [
    {"fase": "floracion", "meses": [7, 8, 9]},
    {"fase": "cosecha", "meses": [11, 12, 1, 2, 3]}
  ],
  "acciones": {
    "floracion": ["Riego controlado para inducir floración", "Monitoreo de oídio y trips"],
    "cosecha": ["Planificar cosecha y acopio", "Proteger fruta ante lluvias de verano"]
  }
}
```

## 7. Alcance realista para 48 h

| Nivel | Contenido |
|---|---|
| **Mínimo (obligatorio)** | 3 regiones (Tumbes, Piura, Lambayeque) · 8 cultivos · calendario por quincena · mapa de aptitud de 1 cultivo · comparador de 3 rotaciones |
| **Objetivo** | 7 regiones del norte · 15 cultivos · mapa de aptitud de cualquier cultivo · alertas NASA |
| **Extra** | Toda la costa peruana · pronóstico estacional El Niño |

El catálogo (sección 6) **se puede investigar y armar antes del 14** como información de referencia; la lógica y la app se programan desde el 14.
