import { useI18n } from 'vue-i18n'
import type { ClaveIndicador, Indicador } from '@/types/api'

/** Diferencia frente a lo normal, texto de alerta y escala de la barra comparativa. */
export function useIndicador() {
  const { t } = useI18n()

  /** Diferencia: en % si hay normal; en °C para El Niño (normal = 0). */
  function diferencia(clave: ClaveIndicador, ind: Indicador): { texto: string; direccion: 'sube' | 'baja' | 'igual' } {
    if (clave === 'elNino' || ind.normal === 0) {
      const d = Math.round((ind.valor - ind.normal) * 10) / 10
      if (Math.abs(d) < 0.3) return { texto: t('indicadores.enRango'), direccion: 'igual' }
      return { texto: t('indicadores.anomalia', { v: (d > 0 ? '+' : '') + d }), direccion: d > 0 ? 'sube' : 'baja' }
    }
    // Temporada seca: con menos de 1 mm/día, un % de diferencia exagera (0.03 vs 0.09 = "-67 %")
    if (clave === 'lluvia' && ind.normal < 1 && ind.valor < 1) return { texto: t('indicadores.temporadaSeca'), direccion: 'igual' }
    const p = Math.round(((ind.valor - ind.normal) / Math.abs(ind.normal)) * 100)
    if (Math.abs(p) < 5) return { texto: t('indicadores.enRango'), direccion: 'igual' }
    return p > 0
      ? { texto: t('indicadores.sobreNormal', { p }), direccion: 'sube' }
      : { texto: t('indicadores.bajoNormal', { p: Math.abs(p) }), direccion: 'baja' }
  }

  /** Texto corto para el banner: "humedad del suelo muy baja", "lluvias extremas"… */
  function textoAlerta(clave: ClaveIndicador, ind: Indicador): string {
    const sube = ind.valor >= ind.normal
    return t(`indicadores.alertas.${clave}${sube ? 'Alta' : 'Baja'}`)
  }

  /** Porcentajes (0-100) para dibujar el valor actual y la marca del normal. */
  function escala(ind: Indicador) {
    const max = Math.max(Math.abs(ind.valor), Math.abs(ind.normal), 0.5) * 1.3
    return {
      actual: Math.min(100, (Math.abs(ind.valor) / max) * 100),
      normal: Math.min(100, (Math.abs(ind.normal) / max) * 100),
    }
  }

  /** Decimales con que se muestra el valor (para que el contador no muestre 0.1234). */
  const decimales = (ind: Indicador) => {
    const s = String(ind.valor)
    return s.includes('.') ? s.split('.')[1].length : 0
  }

  return { diferencia, textoAlerta, escala, decimales }
}
