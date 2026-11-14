import { Apple, Flower2, Moon, Sprout, Wheat } from 'lucide-vue-next'

/** Ícono según la etapa del cultivo (acepta español o inglés) */
export function iconoEtapa(etapa: string) {
  const e = etapa.toLowerCase()
  if (/flor|flower/.test(e)) return Flower2
  if (/fruct|fruit/.test(e)) return Apple
  if (/cosech|harvest/.test(e)) return Wheat
  if (/repos|rest/.test(e)) return Moon
  return Sprout
}

/** "marzo de 2027" -> "Marzo de 2027" */
export const mayusculaInicial = (t: string) => t.charAt(0).toUpperCase() + t.slice(1)
