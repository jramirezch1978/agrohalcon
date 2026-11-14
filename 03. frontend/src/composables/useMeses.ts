import { useAppStore } from '@/stores/app'
import type { MesISO } from '@/types/api'

const fecha = (mes: MesISO) => new Date(Number(mes.slice(0, 4)), Number(mes.slice(5, 7)) - 1, 1)

/** Nombres de meses "AAAA-MM" en el idioma de la app. */
export function useMeses() {
  const store = useAppStore()
  const largo = (mes: MesISO) => fecha(mes).toLocaleString(store.idioma, { month: 'long' })
  const conAnio = (mes: MesISO) => fecha(mes).toLocaleString(store.idioma, { month: 'long', year: 'numeric' })
  const inicial = (mes: MesISO) => fecha(mes).toLocaleString(store.idioma, { month: 'narrow' }).toUpperCase()
  const corto = (mes: MesISO) => fecha(mes).toLocaleString(store.idioma, { month: 'short' }).replace('.', '')
  const hoy = (() => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  })()
  return { largo, conAnio, inicial, corto, hoy }
}
