import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

/**
 * De dónde salen los datos que se ven en pantalla. Regla: nunca cambiar de datos reales a datos de
 * ejemplo (o a la copia guardada) en silencio.
 * - 'real'    : servicio de cálculos (Python) con datos de la NASA
 * - 'ejemplo' : datos simulados (por configuración o porque el servicio no respondió)
 * - 'cache'   : última recomendación guardada en el teléfono (sin conexión)
 */
export type Origen = 'real' | 'ejemplo' | 'cache'
export type Recurso = 'recomendacion' | 'mapa' | 'validacion'

export interface Toast {
  id: number
  texto: string
}

export const useOrigenStore = defineStore('origen', () => {
  const origenes = ref<Partial<Record<Recurso, Origen>>>({})
  const toasts = ref<Toast[]>([])
  let siguiente = 1

  /** true si alguna pantalla muestra datos de ejemplo → banner fijo */
  const hayEjemplo = computed(() => Object.values(origenes.value).includes('ejemplo'))

  function registrar(recurso: Recurso, origen: Origen) {
    origenes.value = { ...origenes.value, [recurso]: origen }
  }

  function avisar(texto: string, ms = 6000) {
    if (toasts.value.some((t) => t.texto === texto)) return // no repetir el mismo aviso
    const id = siguiente++
    toasts.value.push({ id, texto })
    setTimeout(() => cerrar(id), ms)
  }

  function cerrar(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  return { origenes, hayEjemplo, toasts, registrar, avisar, cerrar }
})
