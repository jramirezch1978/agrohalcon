import { CloudRain, Droplets, Thermometer, Waves, Leaf } from 'lucide-vue-next'
import type { ClaveIndicador, NivelRiesgo } from '@/types/api'

/** Estilos por nivel de riesgo (contraste AA en claro y oscuro). */
export const ESTILO_RIESGO: Record<
  NivelRiesgo,
  { texto: string; fondo: string; anillo: string; barra: string; punto: string; hex: string; suave: string }
> = {
  bajo: {
    texto: 'text-emerald-800 dark:text-emerald-300',
    fondo: 'bg-emerald-50 dark:bg-emerald-400/10',
    anillo: 'ring-emerald-600/20 dark:ring-emerald-400/25',
    barra: 'bg-emerald-500',
    punto: 'bg-emerald-500',
    hex: '#10b981',
    suave: 'bg-emerald-500/12 text-emerald-700 dark:text-emerald-300',
  },
  medio: {
    texto: 'text-amber-800 dark:text-amber-300',
    fondo: 'bg-amber-50 dark:bg-amber-400/10',
    anillo: 'ring-amber-600/25 dark:ring-amber-400/25',
    barra: 'bg-amber-500',
    punto: 'bg-amber-500',
    hex: '#f59e0b',
    suave: 'bg-amber-500/14 text-amber-700 dark:text-amber-300',
  },
  alto: {
    texto: 'text-red-800 dark:text-red-300',
    fondo: 'bg-red-50 dark:bg-red-400/10',
    anillo: 'ring-red-600/20 dark:ring-red-400/25',
    barra: 'bg-red-500',
    punto: 'bg-red-500',
    hex: '#ef4444',
    suave: 'bg-red-500/12 text-red-700 dark:text-red-300',
  },
}

export const ICONO_INDICADOR: Record<ClaveIndicador, typeof CloudRain> = {
  lluvia: CloudRain,
  humedadSuelo: Droplets,
  calor: Thermometer,
  elNino: Waves,
  vegetacion: Leaf,
}

export const CLAVES_INDICADOR: ClaveIndicador[] = ['lluvia', 'humedadSuelo', 'calor', 'elNino', 'vegetacion']
