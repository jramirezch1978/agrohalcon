import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { CLAVES_INDICADOR } from './useRiesgo'

/** Comparte un resumen de la recomendación por WhatsApp (web y Android). */
export function useCompartir() {
  const { t } = useI18n()
  const store = useAppStore()

  function texto(): string {
    const r = store.recomendacion
    if (!r) return ''
    const lugar = store.parcela?.nombre ?? `${r.lat}, ${r.lon}`
    const icono = { bajo: '🟢', medio: '🟡', alto: '🔴' }
    const lineas = CLAVES_INDICADOR.flatMap((k) => {
      const i = r.indicadores[k]
      if (!i) return [] // sin dato real: no se comparte un número que no existe
      return `${icono[i.nivel]} ${t(`indicadores.${k}`)}: ${i.valor} ${i.unidad} (${t('indicadores.normal').toLowerCase()} ${i.normal})`
    })
    return [
      `*${t('compartir.encabezado')}*`,
      `📍 ${lugar}`,
      '',
      `✅ *${r.queHacer.accion}*`,
      `${t('inicio.motivo')}: ${r.queHacer.motivo}`,
      '',
      ...lineas,
      '',
      `🛰️ ${t('compartir.pie')} (${r.queHacer.fuente})`,
    ].join('\n')
  }

  function compartirWhatsapp() {
    const url = `https://wa.me/?text=${encodeURIComponent(texto())}`
    window.open(url, '_blank', 'noopener')
  }

  return { texto, compartirWhatsapp }
}
