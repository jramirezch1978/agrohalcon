import { createI18n } from 'vue-i18n'
import es from './locales/es'
import en from './locales/en'

export type Idioma = 'es' | 'en'
export const IDIOMAS: Idioma[] = ['es', 'en']

function idiomaInicial(): Idioma {
  try {
    const guardado = localStorage.getItem('agroshift:idioma')
    if (guardado === 'es' || guardado === 'en') return guardado
  } catch {
    /* almacenamiento no disponible */
  }
  return navigator.language?.toLowerCase().startsWith('es') ? 'es' : 'en'
}

export const i18n = createI18n({
  legacy: false,
  locale: idiomaInicial(),
  fallbackLocale: 'en',
  messages: { es, en },
})
