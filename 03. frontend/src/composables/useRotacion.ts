import { useI18n } from 'vue-i18n'
import type { Descuento, Indicadores } from '@/types/api'

/** "Frijol - Maíz" -> "Frijol → Maíz" (muestra el orden de la rotación) */
export const nombreRotacion = (nombre: string) => nombre.replace(/\s*-\s*/g, ' → ')

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
