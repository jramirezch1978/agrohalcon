import type { FuenteDato, Recomendacion, RespuestaAsistente } from '@/types/api'

/**
 * Asistente SIN IA: responde con plantillas a partir de la recomendación YA calculada (la que está en
 * pantalla, real o de ejemplo). Nunca calcula ni inventa números, y solo cita las fuentes que trae
 * esa recomendación (indicadores, descuentos, meses de la campaña o qué hacer).
 */
export function responderConPlantillas(pregunta: string, rec: Recomendacion, idioma: 'es' | 'en'): RespuestaAsistente {
  const q = pregunta.toLowerCase()
  const es = idioma === 'es'

  if (/riesgos[oa]|riskiest|mes m[aá]s|worst month/.test(q)) return sobreMesRiesgoso(rec, es)

  // Pregunta sobre una rotación concreta ("¿Por qué Arroz - Arroz tiene 55 puntos?")
  const norm = (t: string) => t.toLowerCase().normalize('NFD').replace(/[^a-z]/g, '')
  const rot = rec.rotaciones.find((r) => norm(q).includes(norm(r.nombre)))
  // Pregunta sobre el suelo: puntaje de suelo de esa rotación (o de la recomendada)
  if (/suelo|soil|tierra|nitr[oó]g|legum|salin|salitre|\bsal\b|\bsalt|arenos|sandy/.test(q)) {
    const r = rot ?? ordenar(rec)[0]
    if (r?.saludSuelo != null) return sobreSuelo(r, es)
  }
  if (/recomiend|recomend|recommend/.test(q) && ordenar(rec)[0]?.motivoRecomendada) {
    const m = ordenar(rec)[0]!
    return { respuesta: `${m.nombre}. ${m.motivoRecomendada}`, fuentes: [es ? 'puntaje de AllpaShift' : 'AllpaShift score'] }
  }
  if (rot) return sobreRotacion(rec, rot.id, es)
  if (/arroz|rice/.test(q)) return sobreArroz(rec, es)
  if (/rotaci|rotation|riesgo|risk|mejor|best/.test(q)) return sobreRotaciones(rec, es)
  if (/ni[ñn]o|mar\b|sea|ocean/.test(q)) return sobreElNino(rec, es)
  if (/cu[aá]ndo|when|fecha|date|sembrar|plant/.test(q)) return sobreCuando(rec, es)
  return resumen(rec, es)
}

const NIVEL = {
  es: { bajo: 'bajo', medio: 'medio', alto: 'alto' },
  en: { bajo: 'low', medio: 'medium', alto: 'high' },
} as const

const ordenar = (rec: Recomendacion) => [...rec.rotaciones].sort((a, b) => b.puntaje - a.puntaje)
const minus = (s: string) => s.charAt(0).toLowerCase() + s.slice(1)
const sinPunto = (s: string) => s.replace(/\.\s*$/, '')
/** "NASA POWER + MUR SST" → ["NASA POWER", "MUR SST"], sin repetir */
const unicas = (fuentes: string[]): FuenteDato[] => [...new Set(fuentes.flatMap((f) => f.split(' + ')))]

function fuentesRotacion(rec: Recomendacion, id: number): FuenteDato[] {
  const r = rec.rotaciones.find((x) => x.id === id)
  const desc = r?.descuentos?.map((d) => d.fuente) ?? []
  return unicas(desc.length ? desc : [rec.queHacer.fuente])
}

function sobreArroz(rec: Recomendacion, es: boolean): RespuestaAsistente {
  const arroz = rec.rotaciones.find((r) => /arroz|rice/i.test(r.nombre))
  const mejor = ordenar(rec)[0]
  if (!arroz || !mejor) return resumen(rec, es)
  const n = NIVEL[es ? 'es' : 'en'][arroz.riesgo]
  const respuesta =
    arroz.id === mejor.id
      ? es
        ? `En tu zona el arroz es la mejor opción: ${arroz.puntaje}/100 (riesgo ${n}). ${sinPunto(arroz.explicacion)}.`
        : `In your area rice is the best option: ${arroz.puntaje}/100 (${n} risk). ${sinPunto(arroz.explicacion)}.`
      : es
        ? `${arroz.nombre} obtuvo ${arroz.puntaje}/100 (riesgo ${n}): ${minus(sinPunto(arroz.explicacion))}. ${mejor.nombre} obtuvo ${mejor.puntaje}/100: ${minus(sinPunto(mejor.explicacion))}.`
        : `${arroz.nombre} scored ${arroz.puntaje}/100 (${n} risk): ${minus(sinPunto(arroz.explicacion))}. ${mejor.nombre} scored ${mejor.puntaje}/100: ${minus(sinPunto(mejor.explicacion))}.`
  return { respuesta, fuentes: unicas([...fuentesRotacion(rec, arroz.id), ...fuentesRotacion(rec, mejor.id)]) }
}

const INDICADOR = {
  es: { lluvia: 'la lluvia', humedadSuelo: 'la humedad del suelo', calor: 'el calor', elNino: 'El Niño', vegetacion: 'la vegetación', campana: 'la campaña' },
  en: { lluvia: 'rainfall', humedadSuelo: 'soil moisture', calor: 'heat', elNino: 'El Niño', vegetacion: 'vegetation', campana: 'the season' },
} as const

function sobreRotacion(rec: Recomendacion, id: number, es: boolean): RespuestaAsistente {
  const r = rec.rotaciones.find((x) => x.id === id)!
  const idioma = es ? 'es' : 'en'
  const n = NIVEL[idioma][r.riesgo]
  const d = r.descuentos ?? []
  const lista = d.map((x) => `${x.puntos} ${es ? 'por' : 'for'} ${INDICADOR[idioma][x.indicador]} (${x.fuente})`).join(', ')
  const respuesta = es
    ? `${r.nombre} obtuvo ${r.puntaje}/100 (riesgo ${n}). ${d.length ? `Le restaron puntos: ${lista}. ` : ''}${sinPunto(r.explicacion)}.`
    : `${r.nombre} scored ${r.puntaje}/100 (${n} risk). ${d.length ? `Points were taken off: ${lista}. ` : ''}${sinPunto(r.explicacion)}.`
  return { respuesta, fuentes: fuentesRotacion(rec, id) }
}

const nombreMesISO = (mes: string, es: boolean) =>
  new Date(Number(mes.slice(0, 4)), Number(mes.slice(5, 7)) - 1, 1).toLocaleString(es ? 'es' : 'en', { month: 'long', year: 'numeric' })

/** "¿Cuál es el mes más riesgoso de mi campaña?": usa el ciclo ya calculado */
function sobreMesRiesgoso(rec: Recomendacion, es: boolean): RespuestaAsistente {
  const meses = rec.plan?.meses ?? ordenar(rec)[0]?.ciclo?.meses ?? []
  if (!meses.length) return resumen(rec, es)
  const orden = { bajo: 0, medio: 1, alto: 2 }
  const peor = meses.reduce((a, b) => (orden[b.riesgo] > orden[a.riesgo] ? b : a))
  const quien = rec.plan ? rec.plan.cultivo : ordenar(rec)[0].nombre
  const n = NIVEL[es ? 'es' : 'en'][peor.riesgo]
  const respuesta = es
    ? `Para ${quien}, el mes más riesgoso es ${nombreMesISO(peor.mes, es)} (riesgo ${n}): ${minus(sinPunto(peor.motivo))}. AllpaShift no predice el clima exacto: estima el riesgo con el clima histórico y la señal de El Niño.`
    : `For ${quien}, the riskiest month is ${nombreMesISO(peor.mes, es)} (${n} risk): ${minus(sinPunto(peor.motivo))}. AllpaShift does not predict the exact weather: it estimates the risk from historical climate and the El Niño signal.`
  return { respuesta, fuentes: unicas([peor.fuente]) }
}

/** Puntaje de suelo de una rotación con sus reglas (catálogo de cultivos / dato del agricultor; nunca NASA) */
function sobreSuelo(r: Recomendacion['rotaciones'][number], es: boolean): RespuestaAsistente {
  const reglas = [...(r.descuentosSuelo ?? [])].sort((a, b) => b.puntos - a.puntos).slice(0, 3).map((d) => d.explicacion)
  const respuesta = es
    ? `${r.nombre}: cuidado del suelo ${r.saludSuelo} de 100. ${reglas.length ? reglas.join(' ') : 'Ninguna regla de suelo le suma ni le resta.'}`
    : `${r.nombre}: soil care ${r.saludSuelo} out of 100. ${reglas.length ? reglas.join(' ') : 'No soil rule adds or takes points.'}`
  return { respuesta, fuentes: [es ? 'catálogo de cultivos' : 'crop catalog'] }
}

function sobreRotaciones(rec: Recomendacion, es: boolean): RespuestaAsistente {
  const [mejor, ...resto] = ordenar(rec)
  if (!mejor) return resumen(rec, es)
  const lista = resto.map((r) => `${r.nombre} (${r.puntaje})`).join(es ? ' y ' : ' and ')
  const respuesta = es
    ? `La recomendada es ${mejor.nombre}, con ${mejor.puntaje}/100. ${sinPunto(mejor.explicacion)}.${lista ? ` Le siguen ${lista}.` : ''}`
    : `The recommended option is ${mejor.nombre}, scoring ${mejor.puntaje}/100. ${sinPunto(mejor.explicacion)}.${lista ? ` Next are ${lista}.` : ''}`
  return { respuesta, fuentes: unicas(rec.rotaciones.flatMap((r) => fuentesRotacion(rec, r.id))) }
}

function sobreCuando(rec: Recomendacion, es: boolean): RespuestaAsistente {
  const respuesta = es
    ? `Para esta quincena, AllpaShift recomienda: ${minus(sinPunto(rec.queHacer.accion))}. Motivo: ${minus(sinPunto(rec.queHacer.motivo))}.`
    : `For this fortnight, AllpaShift recommends: ${minus(sinPunto(rec.queHacer.accion))}. Reason: ${minus(sinPunto(rec.queHacer.motivo))}.`
  return { respuesta, fuentes: unicas([rec.queHacer.fuente]) }
}

function sobreElNino(rec: Recomendacion, es: boolean): RespuestaAsistente {
  const n = rec.indicadores.elNino
  if (!n) {
    return {
      respuesta: es ? 'No hay dato de temperatura del mar para esta recomendación.' : 'There is no sea temperature data for this recommendation.',
      fuentes: [],
    }
  }
  const nivel = NIVEL[es ? 'es' : 'en'][n.nivel]
  const respuesta = es
    ? `El mar frente a Perú y Ecuador está ${n.valor > 0 ? '+' : ''}${n.valor} °C respecto a lo normal (nivel ${nivel}). Si sigue alto, aumenta el riesgo de lluvias extremas en la costa norte.`
    : `The sea off Peru and Ecuador is ${n.valor > 0 ? '+' : ''}${n.valor} °C compared to normal (${nivel} level). If it stays high, the risk of extreme rain on the northern coast increases.`
  return { respuesta, fuentes: unicas([n.fuente]) }
}

function resumen(rec: Recomendacion, es: boolean): RespuestaAsistente {
  const respuesta = es
    ? `${sinPunto(rec.queHacer.accion)}. Motivo: ${minus(sinPunto(rec.queHacer.motivo))}.`
    : `${sinPunto(rec.queHacer.accion)}. Reason: ${minus(sinPunto(rec.queHacer.motivo))}.`
  return { respuesta, fuentes: unicas([rec.queHacer.fuente]) }
}
