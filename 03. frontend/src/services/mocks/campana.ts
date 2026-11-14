/**
 * Mocks de la "perspectiva de la campaña": riesgo mes a mes desde la siembra hasta la cosecha.
 * DATOS DE EJEMPLO: simula el riesgo de la campaña a partir de la climatología del lugar, una señal
 * de El Niño simulada y la sensibilidad de cada cultivo. El cálculo real está en el servicio Python.
 */
import type {
  AccionEtapa,
  CicloCultivo,
  CultivoPermanente,
  FuenteDato,
  Indicador,
  ClaveIndicador,
  MesEtapa,
  MesISO,
  MesRiesgo,
  NivelRiesgo,
  PlanPermanente,
  QueHacer,
} from '@/types/api'
import type { ClimaPower } from '../nasaPower'

type Idioma = 'es' | 'en'
const NIVELES: NivelRiesgo[] = ['bajo', 'medio', 'alto']
const nivel = (n: number): NivelRiesgo => NIVELES[Math.max(0, Math.min(2, Math.round(n)))]

// ---------------------------------------------------------------------------
// Utilidades de meses "AAAA-MM"
// ---------------------------------------------------------------------------
export const mesISO = (d: Date): MesISO => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
export function sumarMeses(mes: MesISO, n: number): MesISO {
  const [a, m] = mes.split('-').map(Number)
  return mesISO(new Date(a, m - 1 + n, 1))
}
const mesDelAnio = (mes: MesISO) => Number(mes.split('-')[1]) // 1-12
const nombreMes = (mes: MesISO, idioma: Idioma) =>
  new Date(Number(mes.slice(0, 4)), mesDelAnio(mes) - 1, 1).toLocaleString(idioma, { month: 'long' })

// ---------------------------------------------------------------------------
// Perfil climático del lugar a partir de la climatología del mes
// ---------------------------------------------------------------------------
interface Perfil {
  lluvia: number[] // 1 = temporada de lluvias
  seco: number[] // 0..2 = qué tan seco es el mes
  calor: number[] // 0..2 = meses más calurosos
  pico: number // mes más lluvioso (0-11)
  costaElNino: boolean // costa norte de Perú / Ecuador: El Niño trae lluvias extremas
}

function perfilClima(clima: ClimaPower, lat: number, lon: number): Perfil {
  const maxLluvia = Math.max(...clima.lluvia)
  const maxTemp = Math.max(...clima.temperatura)
  return {
    lluvia: clima.lluvia.map((v) => (maxLluvia >= 0.5 && v >= 0.5 * maxLluvia ? 1 : 0)),
    seco: clima.lluvia.map((v) => (v < 0.1 * maxLluvia || v < 0.2 ? 2 : v < 0.3 * maxLluvia ? 1 : 0)),
    calor: clima.temperatura.map((t) => (t >= maxTemp - 1 ? 2 : t >= maxTemp - 2.5 ? 1 : 0)),
    pico: clima.lluvia.indexOf(maxLluvia),
    costaElNino: lat > -12 && lat < 2 && lon > -82 && lon < -77,
  }
}

type Causa =
  | 'siembra' | 'lluviasNormales' | 'marCalido' | 'lluviaElNino' | 'temporadaLluvias'
  | 'cosechaHumeda' | 'secoNormal' | 'secoArroz' | 'calorFloracion' | 'climaNormal'

const MOTIVOS: Record<Idioma, Record<Causa, string>> = {
  es: {
    siembra: 'Clima normal para la siembra',
    lluviasNormales: 'Lluvias normales',
    marCalido: 'Mar más cálido de lo normal',
    lluviaElNino: 'Posibles lluvias extremas en años con El Niño',
    temporadaLluvias: 'Temporada de lluvias: exceso de humedad',
    cosechaHumeda: 'Lluvias bajando, cosecha con humedad',
    secoNormal: 'Mes seco, sin riesgos importantes',
    secoArroz: 'Mes seco: el arroz depende del agua de riego',
    calorFloracion: 'Calor histórico alto durante la floración',
    climaNormal: 'Clima normal para esta etapa',
  },
  en: {
    siembra: 'Normal weather for planting',
    lluviasNormales: 'Normal rainfall',
    marCalido: 'Warmer sea than normal',
    lluviaElNino: 'Possible extreme rain in El Niño years',
    temporadaLluvias: 'Rainy season: excess moisture',
    cosechaHumeda: 'Rain easing, harvest with moisture',
    secoNormal: 'Dry month, no major risks',
    secoArroz: 'Dry month: rice depends on irrigation water',
    calorFloracion: 'Historically high heat during flowering',
    climaNormal: 'Normal weather for this stage',
  },
}

const FUENTE_CAUSA: Record<Causa, FuenteDato> = {
  siembra: 'Ejemplo',
  lluviasNormales: 'Ejemplo',
  marCalido: 'Ejemplo',
  lluviaElNino: 'Ejemplo',
  temporadaLluvias: 'Ejemplo',
  cosechaHumeda: 'Ejemplo',
  secoNormal: 'Ejemplo',
  secoArroz: 'Ejemplo',
  calorFloracion: 'Ejemplo',
  climaNormal: 'Ejemplo',
}

/** Sensibilidad de cada rotación (índice 0 = Frijol-Maíz, 1 = Arroz-Arroz, 2 = Maíz-Algodón) */
const PERFIL_ROTACION = [
  { duracion: 5, lluvia: 1, seco: 0, calor: 0 }, // Frijol - Maíz: sufre con exceso de lluvia
  { duracion: 8, lluvia: 0, seco: 1, calor: 0 }, // Arroz - Arroz: sufre en meses secos
  { duracion: 9, lluvia: 1, seco: 0, calor: 1 }, // Maíz - Algodón: lluvia + calor en floración
]

/** Riesgo de un mes del año para un perfil de sensibilidad. */
function riesgoMes(
  mes: MesISO,
  sens: { lluvia: number; seco: number; calor: number },
  ind: Record<ClaveIndicador, Indicador>,
  posicion: 'siembra' | 'medio' | 'cosecha',
  idioma: Idioma,
  clima: Perfil,
): MesRiesgo {
  const m = mesDelAnio(mes) - 1
  const sst = ind.elNino.valor
  // El Niño solo cambia la lluvia de forma fuerte en la costa norte de Perú y Ecuador
  const ninoActivo = sst >= 1 && clima.costaElNino
  const sueloSeco = ind.humedadSuelo.valor < ind.humedadSuelo.normal * 0.8
  const antes = (clima.pico + 11) % 12
  const despues = (clima.pico + 1) % 12

  const candidatos: [number, Causa][] = []
  // Lluvia: el mes más lluvioso sube un nivel en años con El Niño (y el anterior si El Niño es fuerte)
  if (sens.lluvia) {
    let r = clima.lluvia[m]
    let causa: Causa = r ? 'temporadaLluvias' : 'lluviasNormales'
    if (m === clima.pico && ninoActivo) (r += 1), (causa = 'lluviaElNino')
    else if (m === antes && ninoActivo) causa = sst >= 2 ? ((r += 1), 'lluviaElNino') : ((r = Math.max(r, 1)), 'marCalido')
    else if (m === despues && ninoActivo) (r = Math.max(r, 1)), (causa = posicion === 'cosecha' ? 'cosechaHumeda' : 'temporadaLluvias')
    candidatos.push([r * sens.lluvia, causa])
  }
  // Meses secos: peor si hoy el suelo ya está seco
  if (sens.seco) candidatos.push([clima.seco[m] ? clima.seco[m] - 1 + (sueloSeco ? 1 : 0) : 0, clima.seco[m] ? 'secoArroz' : 'lluviasNormales'])
  // Calor histórico en la floración
  if (sens.calor) candidatos.push([Math.max(0, clima.calor[m] - 1) * sens.calor, 'calorFloracion'])

  const [valor, causaMax] = candidatos.length ? candidatos.reduce((a, b) => (b[0] > a[0] ? b : a)) : ([0, 'climaNormal'] as [number, Causa])
  const causa: Causa = valor === 0 ? (posicion === 'siembra' ? 'siembra' : clima.lluvia[m] ? causaMax : clima.seco[m] ? 'secoNormal' : causaMax) : causaMax
  return { mes, riesgo: nivel(valor), motivo: MOTIVOS[idioma][causa], fuente: FUENTE_CAUSA[causa] }
}

export function cicloRotacion(
  indiceRotacion: number,
  mesSiembra: MesISO,
  ind: Record<ClaveIndicador, Indicador>,
  idioma: Idioma,
  climaPower: ClimaPower,
  lat: number,
  lon: number,
): CicloCultivo {
  const perfil = PERFIL_ROTACION[indiceRotacion]
  const clima = perfilClima(climaPower, lat, lon)
  const meses = Array.from({ length: perfil.duracion }, (_, i) => {
    const mes = sumarMeses(mesSiembra, i)
    return riesgoMes(mes, perfil, ind, i === 0 ? 'siembra' : i === perfil.duracion - 1 ? 'cosecha' : 'medio', idioma, clima)
  })
  const peor = meses.reduce((a, b) => (NIVELES.indexOf(b.riesgo) > NIVELES.indexOf(a.riesgo) ? b : a))
  return {
    siembra: mesSiembra,
    cosecha: sumarMeses(mesSiembra, perfil.duracion - 1),
    duracionMeses: perfil.duracion,
    meses,
    mesMasRiesgoso: peor.riesgo === 'bajo' ? undefined : peor.mes,
  }
}

/** Puntos de riesgo de la campaña (alto = 2, medio = 1), para ajustar el puntaje según el mes de siembra */
export const riesgoCampana = (c: CicloCultivo) => c.meses.reduce((s, m) => s + NIVELES.indexOf(m.riesgo), 0)

/** Acción de hoy para cultivos temporales: depende del escenario Y del mes de siembra elegido */
export function queHacerTemporal(
  escenario: 'sequia' | 'normal' | 'lluvias' | 'lluviasModeradas',
  base: QueHacer,
  idioma: Idioma,
  mesSiembra: MesISO,
): QueHacer {
  const es = idioma === 'es'
  const hoy = mesISO(new Date())
  const siembraEsteMes = mesSiembra <= hoy
  const mesElegido = nombreMes(mesSiembra, idioma)
  const proximo = nombreMes(sumarMeses(hoy, 1), idioma)

  if (escenario === 'sequia') {
    return {
      ...base,
      tipo: 'esperar',
      accion: siembraEsteMes
        ? es ? `Todavía no siembres: el suelo está seco. Mejor espera a ${proximo}` : `Don't plant yet: the soil is dry. Better wait until ${proximo}`
        : es ? `Espera a ${mesElegido} para sembrar; el suelo aún está seco` : `Wait until ${mesElegido} to plant; the soil is still dry`,
    }
  }
  if (escenario === 'normal') {
    return siembraEsteMes
      ? { ...base, tipo: 'sembrar' }
      : {
          ...base,
          tipo: 'sembrar',
          accion: es
            ? `Buenas condiciones: prepara el terreno para sembrar Frijol - Maíz en ${mesElegido}, o adelántalo a este mes`
            : `Good conditions: prepare the land to plant Bean - Maize in ${mesElegido}, or bring it forward to this month`,
        }
  }
  // Lluvias: el drenaje es lo urgente, sea cual sea el mes de siembra
  return {
    ...base,
    tipo: 'preparar drenaje',
    accion: siembraEsteMes ? base.accion : es ? `Limpia los drenajes ahora; para sembrar en ${mesElegido}, ${base.accion.charAt(0).toLowerCase()}${base.accion.slice(1)}` : `Clear the drains now; to plant in ${mesElegido}: ${base.accion.charAt(0).toLowerCase()}${base.accion.slice(1)}`,
  }
}

// ---------------------------------------------------------------------------
// Cultivos permanentes
// ---------------------------------------------------------------------------
type Etapa = 'floracion' | 'fructificacion' | 'cosecha' | 'reposo'

// Etapa por mes del año (E..D) para la costa norte del Perú
const FENOLOGIA: Record<CultivoPermanente, Etapa[]> = {
  //       E                 F                 M          A          M          J          J          A          S            O            N            D
  mango: ['fructificacion', 'cosecha', 'cosecha', 'reposo', 'reposo', 'reposo', 'reposo', 'reposo', 'floracion', 'floracion', 'floracion', 'fructificacion'],
  limon: ['fructificacion', 'fructificacion', 'cosecha', 'cosecha', 'cosecha', 'reposo', 'reposo', 'floracion', 'floracion', 'floracion', 'fructificacion', 'fructificacion'],
  banano: ['fructificacion', 'cosecha', 'cosecha', 'reposo', 'reposo', 'floracion', 'floracion', 'fructificacion', 'fructificacion', 'cosecha', 'cosecha', 'fructificacion'],
}

const NOMBRE_CULTIVO: Record<Idioma, Record<CultivoPermanente, string>> = {
  es: { mango: 'Mango', limon: 'Limón', banano: 'Banano' },
  en: { mango: 'Mango', limon: 'Lime', banano: 'Banana' },
}
const NOMBRE_ETAPA: Record<Idioma, Record<Etapa, string>> = {
  es: { floracion: 'floración', fructificacion: 'fructificación', cosecha: 'cosecha', reposo: 'reposo' },
  en: { floracion: 'flowering', fructificacion: 'fruiting', cosecha: 'harvest', reposo: 'rest' },
}

/** Sensibilidad climática por etapa */
const PERFIL_ETAPA: Record<Etapa, { lluvia: number; seco: number; calor: number }> = {
  floracion: { lluvia: 1, seco: 0, calor: 1 }, // el calor y la lluvia tiran las flores
  fructificacion: { lluvia: 1, seco: 0, calor: 0 }, // la humedad trae hongos
  cosecha: { lluvia: 1, seco: 0, calor: 0 }, // la lluvia complica la cosecha
  reposo: { lluvia: 0, seco: 0, calor: 0 },
}

function accionesEtapa(etapa: Etapa, ind: Record<ClaveIndicador, Indicador>, idioma: Idioma): Omit<AccionEtapa, 'etapa'> {
  const dCalor = Math.round((ind.calor.valor - ind.calor.normal) * 10) / 10
  const dHum = Math.round((1 - ind.humedadSuelo.valor / ind.humedadSuelo.normal) * 100)
  const es = idioma === 'es'
  switch (etapa) {
    case 'floracion':
      return dCalor > 1
        ? { accion: es ? 'Riega temprano y evita el estrés por calor' : 'Water early and avoid heat stress', motivo: es ? `Calor ${dCalor} °C por encima de lo normal` : `Heat ${dCalor} °C above normal`, fuente: 'Ejemplo' }
        : { accion: es ? 'Mantén el riego regular y vigila la floración' : 'Keep regular irrigation and monitor flowering', motivo: es ? 'Temperaturas dentro de lo normal' : 'Temperatures within normal range', fuente: 'Ejemplo' }
    case 'fructificacion':
      return { accion: es ? 'Prepara drenajes y vigila hongos en los frutos' : 'Prepare drainage and watch for fungi on the fruit', motivo: es ? 'Meses de lluvia; El Niño puede aumentarlas' : 'Rainy months; El Niño can increase them', fuente: 'Ejemplo' }
    case 'cosecha':
      return { accion: es ? 'Cosecha en días secos y protege la fruta de la lluvia' : 'Harvest on dry days and protect the fruit from rain', motivo: es ? 'Historial de lluvias en los meses de cosecha' : 'Rainfall history in harvest months', fuente: 'Ejemplo' }
    case 'reposo':
      return dHum > 15
        ? { accion: es ? 'Poda y riega poco pero seguido para conservar humedad' : 'Prune and water little but often to keep moisture', motivo: es ? `Suelo ${dHum} % más seco de lo normal` : `Soil ${dHum}% drier than normal`, fuente: 'Ejemplo' }
        : { accion: es ? 'Poda, abona y prepara la próxima floración' : 'Prune, fertilize and prepare the next flowering', motivo: es ? 'Humedad del suelo normal' : 'Normal soil moisture', fuente: 'Ejemplo' }
  }
}

export function planPermanente(
  cultivo: CultivoPermanente,
  ind: Record<ClaveIndicador, Indicador>,
  idioma: Idioma,
  climaPower: ClimaPower,
  lat: number,
  lon: number,
): { plan: PlanPermanente; queHacer: QueHacer } {
  const hoy = mesISO(new Date())
  const clima = perfilClima(climaPower, lat, lon)
  const etapaDe = (mes: MesISO) => FENOLOGIA[cultivo][mesDelAnio(mes) - 1]

  const meses: MesEtapa[] = Array.from({ length: 12 }, (_, i) => {
    const mes = sumarMeses(hoy, i)
    const etapa = etapaDe(mes)
    const r = riesgoMes(mes, PERFIL_ETAPA[etapa], ind, 'medio', idioma, clima)
    return { ...r, etapa: NOMBRE_ETAPA[idioma][etapa] }
  })

  // Acciones en el orden en que llegan las etapas, empezando por la actual
  const orden: Etapa[] = []
  for (let i = 0; i < 12; i++) {
    const e = etapaDe(sumarMeses(hoy, i))
    if (!orden.includes(e)) orden.push(e)
  }
  const acciones: AccionEtapa[] = orden.map((e) => ({ etapa: NOMBRE_ETAPA[idioma][e], ...accionesEtapa(e, ind, idioma) }))

  const etapaHoy = etapaDe(hoy)
  const nombre = NOMBRE_CULTIVO[idioma][cultivo]
  const etapaTxt = NOMBRE_ETAPA[idioma][etapaHoy]
  const a = acciones[0]
  const TIPO: Record<Etapa, QueHacer['tipo']> = { floracion: 'regar', fructificacion: 'preparar drenaje', cosecha: 'proteger', reposo: 'regar' }
  const accionCorta = etapaHoy === 'floracion' && a.motivo.match(/\d/)
    ? (idioma === 'es' ? 'riega temprano y protege del calor' : 'water early and protect from heat')
    : a.accion.charAt(0).toLowerCase() + a.accion.slice(1)

  return {
    plan: { cultivo: nombre, etapaActual: etapaTxt, meses, acciones },
    queHacer: {
      tipo: TIPO[etapaHoy],
      accion: idioma === 'es' ? `${nombre} en ${etapaTxt}: ${accionCorta}` : `${nombre} in ${etapaTxt}: ${accionCorta}`,
      motivo: a.motivo,
      fuente: 'Ejemplo',
    },
  }
}
