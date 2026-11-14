import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

Chart.register(
  BarController, BarElement, CategoryScale, Filler,
  Legend, LinearScale, LineController, LineElement, PointElement, Tooltip,
)
Chart.defaults.font.family = "'Inter Variable', system-ui, sans-serif"
Chart.defaults.font.size = 12

/** Colores de gráficos según el tema claro/oscuro. */
export function useTemaGrafico() {
  const store = useAppStore()
  return computed(() => {
    const oscuro = store.tema === 'oscuro'
    return {
      texto: oscuro ? '#a8b5ae' : '#5f6b65',
      rejilla: oscuro ? 'rgba(255,255,255,0.07)' : 'rgba(16,35,27,0.07)',
      pista: oscuro ? 'rgba(255,255,255,0.08)' : 'rgba(16,35,27,0.07)',
      tooltipFondo: oscuro ? '#f3f1ea' : '#10231b',
      tooltipTexto: oscuro ? '#10231b' : '#ffffff',
      normal: oscuro ? '#6b7a73' : '#a8a29e',
      principal: oscuro ? '#c2ee5c' : '#19613a',
      nasa: oscuro ? '#8eaefc' : '#0b3d91',
    }
  })
}
