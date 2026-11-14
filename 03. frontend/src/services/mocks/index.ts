import type {
  ClaveIndicador,
  Cultivo,
  Descuento,
  FuenteNasa,
  Indicador,
  Indicadores,
  MapaRiesgo,
  NivelRiesgo,
  OpcionesRecomendacion,
  QueHacer,
  Recomendacion,
  Rotacion,
  Validacion,
  ZonaRiesgo,
  AniosValidacion,
} from '@/types/api'

import type { ClimaPower } from '../nasaPower'
import { CLIMA_PIURA } from '../nasaPower'
import { cicloRotacion, mesISO, planPermanente, queHacerTemporal, riesgoCampana, sumarMeses } from './campana'

type Idioma = 'es' | 'en'

/**
 * DATOS DE EJEMPLO. Todo lo que sale de este archivo es simulado: la fuente SIEMPRE es "Ejemplo"
 * (nunca el nombre de un producto de la NASA) y la app muestra un banner fijo mientras se vea.
 */
export const EJEMPLO: FuenteNasa = 'Ejemplo'
type IndicadoresCompletos = Record<ClaveIndicador, Indicador>

/** Fuerza fuente "Ejemplo" en cualquier objeto anidado (defensa extra: nada simulado con nombre de satélite). */
function marcarEjemplo<T>(x: T): T {
  if (Array.isArray(x)) return x.map(marcarEjemplo) as T
  if (x && typeof x === 'object') {
    return Object.fromEntries(Object.entries(x).map(([k, v]) => [k, k === 'fuente' ? EJEMPLO : marcarEjemplo(v)])) as T
  }
  return x
}

/** Pseudoaleatorio estable por coordenada: misma ubicación => mismos datos. */
function semilla(lat: number, lon: number): () => number {
  let s = Math.abs((Math.floor(lat * 1000) * 73856093) ^ (Math.floor(lon * 1000) * 19349663)) || 1
  return () => {
    s = (s * 16807) % 2147483647
    return (s - 1) / 2147483646
  }
}

/** yyyy-mm-dd en hora local (toISOString usa UTC y puede dar el día siguiente) */
const fechaLocal = (d = new Date()) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

const redondear = (n: number, d = 2) => Math.round(n * 10 ** d) / 10 ** d

// ---------------------------------------------------------------------------
// Zonas de Piura
// ---------------------------------------------------------------------------
const ZONAS_PIURA: ZonaRiesgo[] = [
  { nombre: 'Bajo Piura', lat: -5.35, lon: -80.7, nivel: 'alto' },
  { nombre: 'Valle del Chira', lat: -4.9, lon: -80.85, nivel: 'medio' },
  { nombre: 'Alto Piura', lat: -5.1, lon: -80.15, nivel: 'bajo' },
  { nombre: 'Medio Piura', lat: -5.2, lon: -80.45, nivel: 'alto' },
  { nombre: 'Sechura', lat: -5.56, lon: -80.82, nivel: 'alto' },
  { nombre: 'San Lorenzo', lat: -4.72, lon: -80.25, nivel: 'bajo' },
  { nombre: 'Huancabamba', lat: -5.24, lon: -79.45, nivel: 'bajo' },
  { nombre: 'Ayabaca', lat: -4.64, lon: -79.71, nivel: 'bajo' },
]

// ---------------------------------------------------------------------------
// Escenarios de la demo
//   sequia          -> el ejemplo oficial (Bajo Piura, Medio Piura, ciudad de Piura)
//   normal          -> riesgo bajo (zonas altas)
//   lluvias         -> lluvias extremas tipo El Niño costero (Sechura)
//   lluviasModeradas-> El Niño en formación (Valle del Chira)
// ---------------------------------------------------------------------------
type Escenario = 'sequia' | 'normal' | 'lluvias' | 'lluviasModeradas'

const ESCENARIO_POR_ZONA: Record<string, Escenario> = {
  'Bajo Piura': 'sequia',
  'Medio Piura': 'sequia',
  'Valle del Chira': 'lluviasModeradas',
  Sechura: 'lluvias',
  'Alto Piura': 'normal',
  'San Lorenzo': 'normal',
  Huancabamba: 'normal',
  Ayabaca: 'normal',
}

type D = [ClaveIndicador, number]

interface Base {
  ind: Record<keyof Indicadores, { valor: number; normal: number; nivel: NivelRiesgo }>
  puntajes: [number, number, number] // Frijol-Maíz, Arroz-Arroz, Maíz-Algodón
  /** Puntos restados por indicador (100 + suma = puntaje) */
  descuentos: [D[], D[], D[]]
  fuente: FuenteNasa
}

const BASES: Record<Escenario, Base> = {
  sequia: {
    ind: {
      lluvia: { valor: 2.1, normal: 8.5, nivel: 'alto' },
      humedadSuelo: { valor: 0.12, normal: 0.2, nivel: 'alto' },
      calor: { valor: 34.0, normal: 31.0, nivel: 'medio' },
      elNino: { valor: 1.2, normal: 0.0, nivel: 'medio' },
    },
    puntajes: [82, 35, 64],
    descuentos: [
      [['calor', -10], ['humedadSuelo', -8]],
      [['humedadSuelo', -40], ['lluvia', -25]],
      [['calor', -20], ['humedadSuelo', -16]],
    ],
    fuente: EJEMPLO,
  },
  normal: {
    ind: {
      lluvia: { valor: 7.9, normal: 8.5, nivel: 'bajo' },
      humedadSuelo: { valor: 0.21, normal: 0.2, nivel: 'bajo' },
      calor: { valor: 31.4, normal: 31.0, nivel: 'bajo' },
      elNino: { valor: 0.2, normal: 0.0, nivel: 'bajo' },
    },
    puntajes: [86, 68, 79],
    descuentos: [
      [['lluvia', -8], ['calor', -6]],
      [['lluvia', -20], ['humedadSuelo', -12]],
      [['calor', -12], ['lluvia', -9]],
    ],
    fuente: EJEMPLO,
  },
  lluvias: {
    ind: {
      lluvia: { valor: 23.8, normal: 8.5, nivel: 'alto' },
      humedadSuelo: { valor: 0.38, normal: 0.2, nivel: 'alto' },
      calor: { valor: 29.5, normal: 31.0, nivel: 'bajo' },
      elNino: { valor: 2.4, normal: 0.0, nivel: 'alto' },
    },
    puntajes: [41, 74, 33],
    descuentos: [
      [['lluvia', -35], ['humedadSuelo', -24]],
      [['lluvia', -16], ['elNino', -10]],
      [['humedadSuelo', -38], ['lluvia', -29]],
    ],
    fuente: EJEMPLO,
  },
  lluviasModeradas: {
    ind: {
      lluvia: { valor: 13.2, normal: 8.5, nivel: 'medio' },
      humedadSuelo: { valor: 0.27, normal: 0.2, nivel: 'medio' },
      calor: { valor: 30.6, normal: 31.0, nivel: 'bajo' },
      elNino: { valor: 0.9, normal: 0.0, nivel: 'medio' },
    },
    puntajes: [58, 76, 47],
    descuentos: [
      [['lluvia', -24], ['humedadSuelo', -18]],
      [['lluvia', -14], ['elNino', -10]],
      [['humedadSuelo', -30], ['lluvia', -23]],
    ],
    fuente: EJEMPLO,
  },
}

const FUENTES: Record<keyof Indicadores, FuenteNasa> = {
  lluvia: EJEMPLO,
  humedadSuelo: EJEMPLO,
  calor: EJEMPLO,
  elNino: EJEMPLO,
}

/** Textos por escenario. p = % de diferencia; d = déficit de humedad; sst = anomalía del mar. */
type Ctx = { p: number; d: number; sst: number; lluvia: number; normal: number }
type Textos = { rot: [string, string, string]; accion: string; motivo: (c: Ctx) => string; exp: [(c: Ctx) => string, (c: Ctx) => string, (c: Ctx) => string] }

const TEXTOS: Record<Idioma, Record<Escenario, Textos>> = {
  es: {
    sequia: {
      rot: ['Frijol - Maíz', 'Arroz - Arroz', 'Maíz - Algodón'],
      accion: 'No siembres arroz esta quincena; elige la rotación Frijol - Maíz',
      motivo: (c) => `La humedad del suelo está ${c.d} % por debajo de lo normal`,
      exp: [
        () => 'Usa poca agua y resiste el calor esperado',
        (c) => `Necesita mucha agua y la humedad del suelo está ${c.d} % por debajo de lo normal`,
        () => 'Tolera la sequía, pero el calor puede afectar la floración',
      ],
    },
    normal: {
      rot: ['Frijol - Maíz', 'Arroz - Arroz', 'Maíz - Algodón'],
      accion: 'Buen momento para sembrar: elige la rotación Frijol - Maíz',
      motivo: () => 'La lluvia y la humedad del suelo están dentro de lo normal',
      exp: [
        () => 'Clima normal: buen rendimiento con poco riesgo',
        () => 'Hay agua suficiente, pero usa mucha; vigila el riego',
        () => 'El clima normal favorece la floración del algodón',
      ],
    },
    lluvias: {
      rot: ['Frijol - Maíz', 'Arroz - Arroz', 'Maíz - Algodón'],
      accion: 'Siembra arroz solo en terrenos altos y limpia los drenajes; no siembres algodón',
      motivo: (c) => `Llueve ${c.lluvia} mm/día cuando lo normal es ${c.normal} y el mar está +${c.sst} °C más caliente (El Niño)`,
      exp: [
        () => 'El exceso de lluvia pudre la raíz del frijol',
        () => 'Tolera el suelo inundado y aprovecha el exceso de agua',
        () => 'La humedad alta favorece plagas y hongos en el algodón',
      ],
    },
    lluviasModeradas: {
      rot: ['Frijol - Maíz', 'Arroz - Arroz', 'Maíz - Algodón'],
      accion: 'Prepara drenajes antes de sembrar; la rotación Arroz - Arroz es la más segura',
      motivo: (c) => `Llueve ${c.lluvia} mm/día cuando lo normal es ${c.normal}, y el mar empieza a calentarse (+${c.sst} °C)`,
      exp: [
        () => 'Puede funcionar, pero el frijol sufre si sigue lloviendo',
        () => 'Aprovecha la lluvia extra y tolera el suelo húmedo',
        () => 'La humedad favorece plagas en el algodón',
      ],
    },
  },
  en: {
    sequia: {
      rot: ['Bean - Maize', 'Rice - Rice', 'Maize - Cotton'],
      accion: "Don't plant rice this fortnight; choose the Bean - Maize rotation",
      motivo: (c) => `Soil moisture is ${c.d}% below normal`,
      exp: [
        () => 'Uses little water and tolerates the expected heat',
        (c) => `Needs a lot of water and soil moisture is ${c.d}% below normal`,
        () => 'Tolerates drought, but heat may affect flowering',
      ],
    },
    normal: {
      rot: ['Bean - Maize', 'Rice - Rice', 'Maize - Cotton'],
      accion: 'Good time to plant: choose the Bean - Maize rotation',
      motivo: () => 'Rainfall and soil moisture are within normal range',
      exp: [
        () => 'Normal weather: good yield with low risk',
        () => 'There is enough water, but it uses a lot; watch irrigation',
        () => 'Normal weather favors cotton flowering',
      ],
    },
    lluvias: {
      rot: ['Bean - Maize', 'Rice - Rice', 'Maize - Cotton'],
      accion: 'Plant rice only on high ground and clear the drains; do not plant cotton',
      motivo: (c) => `It is raining ${c.lluvia} mm/day when normal is ${c.normal}, and the sea is +${c.sst} °C warmer (El Niño)`,
      exp: [
        () => 'Excess rain rots bean roots',
        () => 'Tolerates flooded soil and uses the extra water',
        () => 'High moisture favors pests and fungi in cotton',
      ],
    },
    lluviasModeradas: {
      rot: ['Bean - Maize', 'Rice - Rice', 'Maize - Cotton'],
      accion: 'Prepare drainage before planting; the Rice - Rice rotation is the safest',
      motivo: (c) => `It is raining ${c.lluvia} mm/day when normal is ${c.normal}, and the sea is starting to warm (+${c.sst} °C)`,
      exp: [
        () => 'It can work, but beans suffer if the rain continues',
        () => 'Uses the extra rain and tolerates wet soil',
        () => 'Moisture favors pests in cotton',
      ],
    },
  },
}

/** Zona de Piura más cercana (a menos de ~40 km), si existe. */
function zonaCercana(lat: number, lon: number): ZonaRiesgo | undefined {
  let mejor: ZonaRiesgo | undefined
  let dist = 0.36
  for (const z of ZONAS_PIURA) {
    const d = Math.hypot(z.lat - lat, z.lon - lon)
    if (d < dist) {
      dist = d
      mejor = z
    }
  }
  return mejor
}

function escenarioPara(lat: number, lon: number): { esc: Escenario; variar: boolean } {
  const zona = zonaCercana(lat, lon)
  if (zona) return { esc: ESCENARIO_POR_ZONA[zona.nombre], variar: false }
  // Resto del mundo: escenario estable según la coordenada, con valores algo distintos
  const opciones: Escenario[] = ['sequia', 'normal', 'lluvias', 'lluviasModeradas']
  return { esc: opciones[Math.floor(semilla(lat, lon)() * opciones.length)], variar: true }
}

/** Lluvia actual SIMULADA según el escenario, a partir de la lluvia normal del mes */
const LLUVIA_ESCENARIO: Record<string, (normal: number) => number> = {
  sequia: (n) => n * 0.3,
  normal: (n) => n * 0.95,
  lluvias: (n) => n + 6.5,
  lluviasModeradas: (n) => n + 2.8,
}

/** Nivel de la lluvia: en temporada seca (normal < 1 mm/día) que no llueva es lo normal */
function nivelLluvia(valor: number, normal: number): NivelRiesgo {
  const exceso = valor - normal
  if (exceso >= 5) return 'alto'
  if (exceso >= 2) return 'medio'
  if (normal >= 1) {
    if (valor < normal * 0.5) return 'alto'
    if (valor < normal * 0.75) return 'medio'
  }
  return 'bajo'
}

export function mockRecomendacion(
  lat: number,
  lon: number,
  idioma: Idioma = 'es',
  opciones: OpcionesRecomendacion = {},
  climaPower: ClimaPower | null = null,
): Recomendacion {
  const clima = climaPower ?? CLIMA_PIURA
  const { esc, variar } = escenarioPara(lat, lon)
  const base = BASES[esc]
  const r = semilla(lon, lat)
  const j = () => (variar ? 0.92 + r() * 0.16 : 1)

  const unidades = {
    lluvia: idioma === 'es' ? 'mm/día' : 'mm/day',
    humedadSuelo: 'm3/m3',
    calor: '°C',
    elNino: idioma === 'es' ? '°C anomalía' : '°C anomaly',
  }

  const indicadores = Object.fromEntries(
    (Object.keys(base.ind) as (keyof Indicadores)[]).map((k) => {
      const b = base.ind[k]
      const dec = k === 'humedadSuelo' ? 2 : 1
      const normal = k === 'elNino' ? 0 : redondear(b.normal * j(), dec)
      const valor = redondear(k === 'elNino' ? b.valor * j() : b.valor * (normal / b.normal) * j(), dec)
      return [k, { valor, normal, unidad: unidades[k], nivel: b.nivel, fuente: FUENTES[k] }]
    }),
  ) as IndicadoresCompletos

  // Lluvia: el "normal" es la climatología del mes (dato de ejemplo en esta pantalla)
  const normalLluvia = redondear(clima.lluvia[new Date().getMonth()], 2)
  const lluviaHoy = redondear(LLUVIA_ESCENARIO[esc](normalLluvia), 2)
  indicadores.lluvia = { ...indicadores.lluvia, valor: lluviaHoy, normal: normalLluvia, nivel: nivelLluvia(lluviaHoy, normalLluvia) }


  const ctx: Ctx = {
    p: Math.round((indicadores.lluvia.valor / indicadores.lluvia.normal - 1) * 100),
    d: Math.round((1 - indicadores.humedadSuelo.valor / indicadores.humedadSuelo.normal) * 100),
    sst: indicadores.elNino.valor,
    lluvia: indicadores.lluvia.valor,
    normal: indicadores.lluvia.normal,
  }
  const tx = TEXTOS[idioma][esc]
  const usoAgua: NivelRiesgo[] = ['bajo', 'alto', 'medio']
  const nivelDe = (p: number): NivelRiesgo => (p >= 70 ? 'bajo' : p >= 50 ? 'medio' : 'alto')

  const comun = { lat: redondear(lat), lon: redondear(lon), fecha: fechaLocal(), indicadores }

  // --- Cultivo permanente: plan por etapas, sin rotaciones ---
  if (opciones.tipoCultivo === 'permanente') {
    const { plan, queHacer } = planPermanente(opciones.cultivo ?? 'mango', indicadores, idioma, clima, lat, lon)
    return marcarEjemplo({ ...comun, rotaciones: [], queHacer, plan })
  }

  // --- Cultivo temporal: rotaciones con la perspectiva de la campaña ---
  const referencia = sumarMeses(mesISO(new Date()), 1) // sembrar el próximo mes
  const mesSiembra = opciones.mesSiembra ?? referencia

  const rotaciones: Rotacion[] = base.puntajes.map((_p0, i) => {
    const ciclo = cicloRotacion(i, mesSiembra, indicadores, idioma, clima, lat, lon)
    // Método transparente: puntaje = 100 + suma de descuentos (todos visibles)
    const descuentos: Descuento[] = base.descuentos[i].map(([indicador, puntos]) => ({
      indicador,
      puntos: variar ? Math.round(puntos * (0.85 + r() * 0.3)) : puntos,
      fuente: EJEMPLO,
    }))
    // Adelantar o atrasar la siembra cambia el riesgo de la campaña (referencia: sembrar el próximo mes)
    const ajuste = 3 * (riesgoCampana(cicloRotacion(i, referencia, indicadores, idioma, clima, lat, lon)) - riesgoCampana(ciclo))
    if (ajuste !== 0) descuentos.push({ indicador: 'campana', puntos: ajuste, fuente: EJEMPLO })
    const puntaje = Math.max(5, Math.min(98, 100 + descuentos.reduce((s, d) => s + d.puntos, 0)))
    return { id: i + 1, nombre: tx.rot[i], puntaje, riesgo: nivelDe(puntaje), usoAgua: usoAgua[i], explicacion: tx.exp[i](ctx), descuentos, ciclo }
  })

  const queHacer: QueHacer = queHacerTemporal(esc, { accion: tx.accion, motivo: tx.motivo(ctx), fuente: EJEMPLO }, idioma, mesSiembra)

  return marcarEjemplo({ ...comun, rotaciones, queHacer })
}

export function mockMapa(region: string): MapaRiesgo {
  if (region.toLowerCase() !== 'piura') return { region, zonas: [] }
  // Mismas zonas que config/zonas_piura.yaml del servicio, SIN nivel: sin el servicio no hay dato real
  return { region: 'piura', zonas: ZONAS_MAPA.map((z) => ({ ...z, nivel: null })) }
}

const ZONAS_MAPA = [
  { nombre: 'Bajo Piura', lat: -5.35, lon: -80.7 },
  { nombre: 'Alto Piura', lat: -5.18, lon: -79.97 },
  { nombre: 'Valle del Chira', lat: -4.9, lon: -80.85 },
  { nombre: 'Sullana', lat: -4.9, lon: -80.69 },
  { nombre: 'Chulucanas', lat: -5.09, lon: -80.16 },
  { nombre: 'Tambogrande', lat: -4.93, lon: -80.34 },
  { nombre: 'Sechura', lat: -5.56, lon: -80.82 },
]

export function mockCultivos(idioma: Idioma = 'es'): Cultivo[] {
  const n = idioma === 'es'
    ? ['Frijol', 'Maíz', 'Arroz', 'Algodón', 'Sorgo', 'Mango', 'Limón', 'Camote']
    : ['Bean', 'Maize', 'Rice', 'Cotton', 'Sorghum', 'Mango', 'Lime', 'Sweet potato']
  return [
    { id: 1, nombre: n[0], usoAgua: 'bajo', toleranciaCalor: 'medio', toleranciaSequia: 'medio', cicloDias: 90 },
    { id: 2, nombre: n[1], usoAgua: 'medio', toleranciaCalor: 'medio', toleranciaSequia: 'medio', cicloDias: 120 },
    { id: 3, nombre: n[2], usoAgua: 'alto', toleranciaCalor: 'medio', toleranciaSequia: 'bajo', cicloDias: 140 },
    { id: 4, nombre: n[3], usoAgua: 'medio', toleranciaCalor: 'alto', toleranciaSequia: 'alto', cicloDias: 180 },
    { id: 5, nombre: n[4], usoAgua: 'bajo', toleranciaCalor: 'alto', toleranciaSequia: 'alto', cicloDias: 110 },
    { id: 6, nombre: n[5], usoAgua: 'medio', toleranciaCalor: 'alto', toleranciaSequia: 'medio', cicloDias: 365 },
    { id: 7, nombre: n[6], usoAgua: 'medio', toleranciaCalor: 'alto', toleranciaSequia: 'medio', cicloDias: 365 },
    { id: 8, nombre: n[7], usoAgua: 'bajo', toleranciaCalor: 'alto', toleranciaSequia: 'alto', cicloDias: 120 },
  ]
}

/**
 * "¿Funciona?" sin el servicio de cálculos: NO se muestra una serie inventada. La pantalla explica que
 * la prueba de 2017 necesita el servicio de cálculos (allí están los datos reales).
 */
export function mockValidacion(anio: number, lat: number, lon: number, idioma: Idioma = 'es'): Validacion {
  const vacia = { unidad: 'mm/mes', fuente: 'sin dato' as const, valores: Array(12).fill(null), normal: Array(12).fill(null) }
  const texto = idioma === 'es'
    ? 'La prueba con datos reales necesita el servicio de cálculos. Sin él no mostramos números.'
    : 'The real-data test needs the calculation service. Without it we show no numbers.'
  return {
    anio, lat, lon, evento: null,
    series: { lluvia: vacia },
    alerta: null, mesLluviaMaxima: null, semanasAnticipacion: null, realidad: null,
    recomendacionPrevia: { accion: texto, motivo: texto, fuente: EJEMPLO },
    resumen: texto,
  }
}

export function mockAniosValidacion(): AniosValidacion {
  return { anios: [2017], fuente: EJEMPLO, conMurSst: [] }
}
