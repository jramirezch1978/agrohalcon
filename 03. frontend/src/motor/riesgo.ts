// Motor de riesgo de AllpaShift: reglas transparentes sobre los datos NASA.
// Las mismas reglas las implementa climate-service (David); esto es la versión del navegador.
import { cultivos, MESES, rotacionesPorPiso, type Cultivo, type Fase, type Piso, accionPermanente, nombreFase } from '../data/catalogo'
import type { DatosNasa } from './nasa'

export type Nivel = 'bajo' | 'medio' | 'alto'
export type Color = 'verde' | 'ambar' | 'rojo'

export interface Indicadores {
  humedadPct: number | null      // % frente a lo normal (negativo = más seco)
  lluviaMm30: number | null
  lluviaNormal30: number
  lluviaPct: number | null
  calorC: number | null          // °C sobre la máxima normal
  sstAnomalia: number | null
  nivel: Nivel
  alerta: string | null
  fuente: string
}

export interface MesCampania { mes: number; anio: number; color: Color; motivo: string }
export interface Rotacion {
  c1: Cultivo; c2: Cultivo; puntaje: number; nivel: Nivel; agua: 'baja' | 'media' | 'alta'
  motivo: string; porque: string[]; campania: MesCampania[]; mesMasRiesgoso: MesCampania | null
  siembra: number; cosecha: number; duracion: number; actual: boolean
}

export interface Accion { tipo: 'ESPERAR' | 'SEMBRAR' | 'PROTEGER' | 'REGAR' | 'COSECHAR'; titulo: string; motivo: string }

const r1 = (x: number) => Math.round(x * 10) / 10

export function calcularIndicadores(d: DatosNasa, mesHoy: number): Indicadores {
  const n = d.normales[mesHoy]
  const lluviaNormal30 = n.lluviaMmDia * 30
  let humedadPct: number | null = null, lluviaPct: number | null = null, calorC: number | null = null, lluviaMm30: number | null = null
  if (d.reciente) {
    humedadPct = Math.round(((d.reciente.humedadSup - n.humedadSup) / n.humedadSup) * 100)
    lluviaMm30 = r1(d.reciente.lluviaMm30)
    // En la costa la normal puede ser casi 0: se usa un mínimo de 10 mm para que el porcentaje tenga sentido
    lluviaPct = Math.round(((d.reciente.lluviaMm30 - lluviaNormal30) / Math.max(lluviaNormal30, 10)) * 100)
    calorC = r1(d.reciente.tMax - n.tMax)
  }
  const sst = d.sstAnomalia
  let nivel: Nivel = 'bajo'
  const alertas: string[] = []
  if (humedadPct !== null && humedadPct <= -25) { nivel = 'alto'; alertas.push('humedad del suelo muy baja') }
  else if (humedadPct !== null && humedadPct <= -10) { nivel = 'medio'; alertas.push('humedad del suelo baja') }
  if (lluviaMm30 !== null && lluviaMm30 < 0.5 * lluviaNormal30 && lluviaNormal30 >= 3) alertas.unshift('lluvia muy baja')
  if (lluviaPct !== null && lluviaPct >= 150 && (lluviaMm30 ?? 0) >= 30) {
    nivel = 'alto'
    alertas.push(`lluvia muy por encima de lo normal (${Math.round(lluviaMm30 ?? 0)} mm en 30 días; lo normal es ${Math.round(lluviaNormal30)} mm)`)
  }
  if (calorC !== null && calorC >= 2) { nivel = 'alto'; alertas.push(`calor ${calorC} °C sobre lo normal`) }
  else if (calorC !== null && calorC >= 1 && nivel === 'bajo') nivel = 'medio'
  if (sst !== null && sst >= 1.5) { nivel = 'alto'; alertas.push(`mar ${r1(sst)} °C más caliente (señal de El Niño costero)`) }
  return {
    humedadPct, lluviaMm30, lluviaNormal30: r1(lluviaNormal30), lluviaPct, calorC, sstAnomalia: sst === null ? null : r1(sst),
    nivel, alerta: alertas.length && nivel !== 'bajo' ? alertas.join(' y ') : null, fuente: d.fuente,
  }
}

export const excesoLluvia = (ind: Indicadores) => ind.lluviaPct !== null && ind.lluviaPct >= 150 && (ind.lluviaMm30 ?? 0) >= 30

// Riesgo de un mes de campaña para un cultivo
function riesgoMes(c: Cultivo, d: DatosNasa, mes: number, ind: Indicadores, esPrimerMes: boolean): { color: Color; motivo: string } {
  const n = d.normales[mes]
  const lluviaMes = n.lluviaMmDia * 30
  const anioMax = Math.max(...d.normales.map((x) => x.lluviaMmDia)) * 30
  if (esPrimerMes && ind.humedadPct !== null && ind.humedadPct <= -25 && c.agua !== 'baja') return { color: 'rojo', motivo: `suelo seco al sembrar (${ind.humedadPct} % frente a lo normal)` }
  if (esPrimerMes && ind.humedadPct !== null && ind.humedadPct <= -25) return { color: 'ambar', motivo: 'suelo seco al sembrar; siembra con riego de enseño' }
  const lluviaAnomala = excesoLluvia(ind)
  if (esPrimerMes && lluviaAnomala) return { color: c.toleraInundacion ? 'ambar' : 'rojo', motivo: `lluvia actual muy por encima de lo normal (${Math.round(ind.lluviaMm30 ?? 0)} mm en 30 días)` }
  if (lluviaMes >= 0.6 * anioMax && lluviaMes >= 25 && !c.toleraInundacion) {
    const sst = (ind.sstAnomalia !== null && ind.sstAnomalia >= 1.5) || lluviaAnomala
    return { color: sst ? 'rojo' : 'ambar', motivo: `temporada de lluvias, exceso de humedad${sst ? ' y señal de El Niño' : ''}` }
  }
  if (n.tMax >= c.tempMax || (ind.calorC !== null && ind.calorC >= 2 && n.tMax + ind.calorC >= c.tempMax)) {
    return { color: c.toleraCalor ? 'ambar' : 'rojo', motivo: `calor (máxima normal ${r1(n.tMax)} °C)` }
  }
  if (lluviaMes < 5 && c.agua === 'alta') return { color: 'ambar', motivo: 'mes seco: depende del agua de riego' }
  return { color: 'verde', motivo: 'condiciones normales para el cultivo' }
}

export function evaluarRotaciones(d: DatosNasa, ind: Indicadores, piso: Piso, mesSiembra: number, anioSiembra: number): Rotacion[] {
  const lista = rotacionesPorPiso[piso].map(([a, b], i, arr) => {
    const c1 = cultivos[a], c2 = cultivos[b]
    const duracion = Math.min(c1.cicloMeses + Math.max(2, Math.round(c2.cicloMeses / 2)), 9)
    const campania: MesCampania[] = []
    for (let k = 0; k < duracion; k++) {
      const mes = (mesSiembra + k) % 12
      const anio = anioSiembra + Math.floor((mesSiembra + k) / 12)
      const cult = k < c1.cicloMeses ? c1 : c2
      const r = riesgoMes(cult, d, mes, ind, k === 0)
      campania.push({ mes, anio, color: r.color, motivo: r.motivo })
    }
    const rojos = campania.filter((m) => m.color === 'rojo').length
    const ambar = campania.filter((m) => m.color === 'ambar').length
    const porque: string[] = []
    let p = 92
    const aguaPen = { baja: 0, media: 8, alta: 22 }
    p -= aguaPen[c1.agua] / 2 + aguaPen[c2.agua] / 2
    if (c1.agua === 'alta' || c2.agua === 'alta') porque.push('Necesita mucha agua')
    if (ind.humedadPct !== null && ind.humedadPct <= -25) {
      const castigo = c1.toleraSequia ? 2 : c1.agua === 'alta' ? 15 : 8
      p -= castigo
      porque.push(c1.toleraSequia ? 'Aguanta el suelo seco de ahora' : `La humedad del suelo está ${Math.abs(ind.humedadPct)} % por debajo de lo normal`)
    }
    if (excesoLluvia(ind)) {
      if (c1.toleraInundacion) { p += 6; porque.push('Tolera el encharcamiento de este año lluvioso') }
      else { p -= 8; porque.push(`Llueve mucho más de lo normal (${Math.round(ind.lluviaMm30 ?? 0)} mm en 30 días): riesgo de encharcamiento y hongos`) }
    }
    p -= rojos * 6 + ambar * 2.5
    if (rojos) porque.push(`${rojos} mes(es) en rojo en la campaña`)
    if (c1.fijaNitrogeno || c2.fijaNitrogeno) { p += 4; porque.push('Incluye una leguminosa que devuelve nitrógeno al suelo') }
    const mono = c1.nombre === c2.nombre
    if (mono) { p -= 8; porque.push('Monocultivo: desgasta el suelo y repite plagas') }
    if (!c1.toleraCalor && ind.calorC !== null && ind.calorC >= 1) { p -= 5; porque.push('El calor puede afectar la floración') }
    const puntaje = Math.max(5, Math.min(98, Math.round(p)))
    const nivel: Nivel = puntaje >= 70 ? 'bajo' : puntaje >= 50 ? 'medio' : 'alto'
    const agua = c1.agua === 'alta' || c2.agua === 'alta' ? 'alta' : c1.agua === 'media' || c2.agua === 'media' ? 'media' : 'baja'
    const orden = { rojo: 2, ambar: 1, verde: 0 }
    const peor = campania.reduce<MesCampania | null>((m, x) => (!m || orden[x.color] > orden[m.color] ? x : m), null)
    const motivo = excesoLluvia(ind) && !c1.toleraInundacion
      ? `Con ${Math.round(ind.lluviaMm30 ?? 0)} mm de lluvia en 30 días hay riesgo de encharcamiento al sembrar`
      : excesoLluvia(ind) && c1.toleraInundacion ? 'Aguanta el exceso de lluvia, pero usa mucha agua y desgasta el suelo'
      : mono && agua === 'alta' && ind.humedadPct !== null && ind.humedadPct <= -25
      ? `Necesita mucha agua y la humedad del suelo está ${Math.abs(ind.humedadPct)} % por debajo de lo normal`
      : agua === 'baja' ? 'Usa poca agua y resiste el calor esperado'
      : c2.toleraSequia || c1.toleraSequia ? 'Tolera la sequía, pero el calor puede afectar la floración'
      : 'Rendimiento estable si hay agua de riego'
    return {
      c1, c2, puntaje, nivel, agua, motivo, porque, campania, mesMasRiesgoso: peor && peor.color !== 'verde' ? peor : null,
      siembra: mesSiembra, cosecha: campania[campania.length - 1].mes, duracion, actual: i === arr.length - 1,
    } as Rotacion
  })
  return lista.sort((a, b) => b.puntaje - a.puntaje)
}

export function accionRecomendada(ind: Indicadores, mesSiembra: number, mejor: Rotacion | undefined): Accion {
  const sig = MESES[(mesSiembra + 1) % 12].toLowerCase()
  if (ind.humedadPct !== null && ind.humedadPct <= -25)
    return { tipo: 'ESPERAR', titulo: `Todavía no siembres: el suelo está seco. Mejor espera a ${sig}`, motivo: `La humedad del suelo está ${Math.abs(ind.humedadPct)} % por debajo de lo normal` }
  if (excesoLluvia(ind))
    return { tipo: 'PROTEGER', titulo: 'Prepara drenes antes de sembrar: está lloviendo mucho más de lo normal', motivo: `En los últimos 30 días cayeron ${Math.round(ind.lluviaMm30 ?? 0)} mm; lo normal en este mes son ${Math.round(ind.lluviaNormal30)} mm. Es una señal temprana de El Niño` }
  if (ind.calorC !== null && ind.calorC >= 2)
    return { tipo: 'REGAR', titulo: 'Riega temprano: hace más calor de lo normal', motivo: `La temperatura máxima está ${ind.calorC} °C por encima de lo normal` }
  return { tipo: 'SEMBRAR', titulo: `Buen momento para sembrar ${mejor ? mejor.c1.nombre.toLowerCase() : ''}`.trim(), motivo: 'La humedad del suelo, la lluvia y el calor están dentro de lo normal' }
}

export function accionCultivoPermanente(nombre: string, mes: number, ind: Indicadores): Accion & { fase: Fase } {
  const c = cultivos[nombre]
  const fase = (c.calendario ?? 'CCCCCCCCCCCC')[mes] as Fase
  const base = accionPermanente[nombre]?.[fase] ?? 'Mantén el riego y la sanidad del cultivo.'
  if (excesoLluvia(ind)) return { fase, tipo: 'PROTEGER', titulo: `${nombre} en ${nombreFase[fase].toLowerCase()}: drena y protege del exceso de lluvia`, motivo: base }
  if (ind.humedadPct !== null && ind.humedadPct <= -25) return { fase, tipo: 'REGAR', titulo: `${nombre} en ${nombreFase[fase].toLowerCase()}: refuerza el riego, el suelo está seco`, motivo: base }
  if (fase === 'K') return { fase, tipo: 'COSECHAR', titulo: `${nombre}: estás en temporada de cosecha`, motivo: base }
  return { fase, tipo: 'SEMBRAR', titulo: `${nombre} en ${nombreFase[fase].toLowerCase()}`, motivo: base }
}
