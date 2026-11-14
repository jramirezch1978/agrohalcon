// Asistente "Pregúntale a AllpaShift": responde con los resultados ya calculados (no inventa datos).
import { reactive } from 'vue'
import { estado, fechaHoy } from '../estado'
import { MESES } from '../data/catalogo'
import { accionCultivoPermanente } from '../motor/riesgo'

export const chat = reactive({ mensajes: [] as { de: 'yo' | 'ia'; txt: string }[] })

export function preguntar(p: string) {
  estado.asistenteAbierto = true
  chat.mensajes.push({ de: 'yo', txt: p })
  chat.mensajes.push({ de: 'ia', txt: responder(p) })
}

function responder(p: string): string {
  const q = p.toLowerCase()
  const i = estado.ind
  const rs = estado.rotaciones
  if (!i || !rs.length) return 'Primero elige tu parcela en el mapa y pulsa «Analizar esta parcela».'
  const fuente = i.fuente === 'Ejemplo' ? 'datos de ejemplo' : 'datos de NASA POWER'
  if (q.includes('arroz')) {
    const arroz = rs.find((r) => r.c1.nombre === 'Arroz')
    if (!arroz) return 'En tu zona el arroz no está entre las rotaciones evaluadas.'
    return `El arroz necesita mucha agua. ${i.humedadPct !== null ? `Hoy la humedad del suelo está ${i.humedadPct} % frente a lo normal` : 'No hay dato reciente de humedad del suelo'}. Por eso «${arroz.c1.nombre} → ${arroz.c2.nombre}» obtiene ${arroz.puntaje}/100 (${fuente}). ${arroz.porque.join('. ')}.`
  }
  if (q.includes('menos riesgo') || q.includes('rotación')) {
    const m = rs[0]
    return `La de menos riesgo es «${m.c1.nombre} → ${m.c2.nombre}» con ${m.puntaje}/100: ${m.motivo.toLowerCase()}. ${m.porque.join('. ')}.`
  }
  if (q.includes('mes') && q.includes('riesgo')) {
    const m = rs[0].mesMasRiesgoso
    return m ? `En tu campaña recomendada, el mes más riesgoso es ${MESES[m.mes].toLowerCase()} de ${m.anio}: ${m.motivo}.` : 'Con la rotación recomendada no hay meses en rojo ni en ámbar.'
  }
  if (q.includes('niño') || q.includes('nino') || q.includes('mar')) {
    return i.sstAnomalia === null
      ? 'No hay dato de temperatura del mar para este punto (MUR SST solo aplica frente a la costa del Pacífico).'
      : `El mar frente a tu costa está ${i.sstAnomalia > 0 ? '+' : ''}${i.sstAnomalia} °C frente a lo normal (MUR SST, NASA). ${i.sstAnomalia >= 1.5 ? 'Es una señal de El Niño costero: prepara drenes y protege la cosecha.' : 'Por ahora no es una señal fuerte de El Niño costero.'}`
  }
  if (q.includes('regar') || q.includes('riesgo tiene mi')) {
    const a = accionCultivoPermanente(estado.permanente, fechaHoy.getMonth(), i)
    return `${a.titulo}. ${a.motivo}`
  }
  return `Según ${fuente}: riesgo climático ${i.nivel}. ${estado.accion?.titulo ?? ''}. Puedes preguntar por el arroz, la rotación con menos riesgo, el mes más riesgoso o El Niño.`
}
