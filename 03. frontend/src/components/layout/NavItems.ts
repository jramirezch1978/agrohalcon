import { CircleCheckBig, CircleHelp, Map, Sprout, Sun } from 'lucide-vue-next'

/**
 * Navegación principal (el asistente se abre desde el botón flotante).
 * Cada pestaña es la pregunta que ya tiene en la cabeza quien entra por primera vez:
 * ¿Qué hago? · ¿Qué siembro? · Mapa · ¿Funciona? (prueba El Niño 2017) · Ayuda (cómo funciona y datos NASA).
 */
export const NAV_ITEMS = [
  { to: '/hoy', clave: 'nav.hoy', icono: Sun },
  { to: '/campana', clave: 'nav.campana', icono: Sprout },
  { to: '/mapa', clave: 'nav.mapa', icono: Map },
  { to: '/validacion', clave: 'nav.validacion', icono: CircleCheckBig },
  { to: '/datos', clave: 'nav.datos', icono: CircleHelp },
] as const
