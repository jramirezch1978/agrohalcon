import { createI18n } from 'vue-i18n'
import es from './locales/es'
import en from './locales/en'

export type Idioma = 'es' | 'en'
export const IDIOMAS: Idioma[] = ['es', 'en']

function idiomaInicial(): Idioma {
  try {
    const guardado = localStorage.getItem('allpashift:idioma')
    if (guardado === 'es' || guardado === 'en') return guardado
  } catch {
    /* almacenamiento no disponible */
  }
  // Por defecto en inglés (entrega a la NASA); el usuario puede cambiar a español y se recuerda
  return 'en'
}

export const i18n = createI18n({
  legacy: false,
  locale: idiomaInicial(),
  fallbackLocale: 'en',
  messages: { es, en },
})
