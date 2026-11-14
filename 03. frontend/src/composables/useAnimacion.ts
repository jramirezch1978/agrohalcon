import { onMounted, ref, watch, type Ref } from 'vue'

type Fuente = Readonly<Ref<number>>

const sinMovimiento = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

/** Número que sube desde 0 hasta el valor (y se re-anima si el valor cambia). */
export function useContador(objetivo: Fuente, duracion = 1100, retraso = 0) {
  const actual = ref(0)
  let frame = 0

  function animar(desde: number, hasta: number) {
    cancelAnimationFrame(frame)
    if (sinMovimiento()) {
      actual.value = hasta
      return
    }
    const inicio = performance.now() + retraso
    const paso = (ahora: number) => {
      const t = Math.min(1, Math.max(0, (ahora - inicio) / duracion))
      const e = 1 - Math.pow(1 - t, 3) // ease-out cúbico
      actual.value = desde + (hasta - desde) * e
      if (t < 1) frame = requestAnimationFrame(paso)
    }
    frame = requestAnimationFrame(paso)
  }

  onMounted(() => animar(0, objetivo.value))
  watch(objetivo, (n, v) => animar(v ?? 0, n))
  return actual
}

/** false en el primer render y true después: para que las barras "se llenen" con transición. */
export function useMontado(retraso = 60) {
  const listo = ref(false)
  onMounted(() => setTimeout(() => (listo.value = true), retraso))
  return listo
}
