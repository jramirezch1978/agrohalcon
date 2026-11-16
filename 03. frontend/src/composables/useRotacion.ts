import { useI18n } from 'vue-i18n'
import type { Calificacion, Descuento, Indicadores, NivelRiesgo, Rotacion } from '@/types/api'

/** "Frijol - Maíz" -> "Frijol → Maíz" (muestra el orden de la rotación) */
export const nombreRotacion = (nombre: string) => nombre.replace(/\s*-\s*/g, ' → ')

/** Calificación en palabras (la manda el servidor; si no, se deduce del puntaje con los mismos cortes). */
export const calificacionDe = (r: Pick<Rotacion, 'puntaje' | 'calificacion'>): Calificacion =>
  r.calificacion ?? (r.puntaje >= 70 ? 'buena' : r.puntaje >= 45 ? 'regular' : 'riesgosa')

/** Color de la calificación (verde / ámbar / rojo) */
export const NIVEL_CALIFICACION: Record<Calificacion, NivelRiesgo> = { buena: 'bajo', regular: 'medio', riesgosa: 'alto' }

export function useRotacion() {
  const { t } = useI18n()

  /** "por humedad del suelo baja" según el valor actual del indicador */
  function motivoDescuento(d: Descuento, indicadores?: Indicadores): string {
    if (d.indicador === 'campana') return t(d.puntos < 0 ? 'rotaciones.campanaMenos' : 'rotaciones.campanaMas')
    const ind = indicadores?.[d.indicador]
    const sube = ind ? ind.valor >= ind.normal : false
    return t('rotaciones.descuento', { motivo: t(`indicadores.estado.${d.indicador}${sube ? 'Alta' : 'Baja'}`) })
  }

  return { motivoDescuento }
}
