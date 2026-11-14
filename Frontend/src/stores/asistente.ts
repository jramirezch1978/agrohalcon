import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { api } from '@/services/api'
import type { FuenteDato, RespuestaAsistente } from '@/types/api'
import { useAppStore } from './app'

export interface MensajeChat {
  id: number
  rol: 'usuario' | 'asistente'
  texto: string
  fuentes?: FuenteDato[]
  /** true si es la respuesta básica (queHacer.motivo) porque /api/asistente falló o tardó */
  respaldo?: boolean
}

const CLAVE = 'agroshift:chat'
/** Plan B: si el asistente no responde en este tiempo, se usa la respuesta básica */
export const LIMITE_ESPERA_MS = 10_000
export const MAX_CARACTERES = 300

function leerHistorial(): MensajeChat[] {
  try {
    return JSON.parse(localStorage.getItem(CLAVE) ?? '[]') as MensajeChat[]
  } catch {
    return []
  }
}

function conLimite<T>(promesa: Promise<T>, ms: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('tiempo agotado')), ms)
    promesa.then(
      (v) => (clearTimeout(t), resolve(v)),
      (e) => (clearTimeout(t), reject(e)),
    )
  })
}

export const useAsistenteStore = defineStore('asistente', () => {
  const app = useAppStore()
  const historial = ref<MensajeChat[]>(leerHistorial())
  const escribiendo = ref(false)

  // --- Panel flotante ---
  const panelAbierto = ref(false)
  /** Pregunta sugerida que registra la pantalla actual (ej. la rotación recomendada) */
  const sugerenciaPantalla = ref<string | null>(null)
  /** Pregunta sugerida que se muestra primero al abrir el panel */
  const sugerenciaContexto = ref<string | null>(null)

  function abrirPanel(sugerencia?: string) {
    sugerenciaContexto.value = sugerencia ?? sugerenciaPantalla.value
    panelAbierto.value = true
  }
  function cerrarPanel() {
    panelAbierto.value = false
  }

  watch(
    historial,
    (h) => {
      try {
        localStorage.setItem(CLAVE, JSON.stringify(h.slice(-50)))
      } catch {
        /* almacenamiento no disponible */
      }
    },
    { deep: true },
  )

  // Las respuestas dependen de la parcela: al cambiarla, conversación nueva
  watch(
    () => [app.parcela?.lat, app.parcela?.lon],
    () => limpiar(),
  )

  const nuevoId = () => (historial.value.at(-1)?.id ?? 0) + 1

  async function preguntar(pregunta: string) {
    const texto = pregunta.trim().slice(0, MAX_CARACTERES)
    if (!texto || escribiendo.value || !app.parcela) return

    historial.value.push({ id: nuevoId(), rol: 'usuario', texto })
    escribiendo.value = true
    try {
      const { lat, lon } = app.parcela
      // Sin IA: plantillas sobre la recomendación ya calculada (la misma que está en pantalla)
      if (!app.recomendacion) await app.cargarRecomendacion()
      const r: RespuestaAsistente = await conLimite(
        api.preguntarAsistente({ lat, lon, pregunta: texto, idioma: app.idioma, ...app.opcionesCultivo }, app.recomendacion),
        LIMITE_ESPERA_MS,
      )
      historial.value.push({ id: nuevoId(), rol: 'asistente', texto: r.respuesta, fuentes: r.fuentes })
    } catch {
      // Plan B: solo mostramos lo que ya calculó /api/recomendacion
      if (!app.recomendacion) await app.cargarRecomendacion()
      const qh = app.recomendacion?.queHacer
      historial.value.push({
        id: nuevoId(),
        rol: 'asistente',
        texto: qh?.motivo ?? '',
        fuentes: qh ? [qh.fuente] : undefined,
        respaldo: true,
      })
    } finally {
      escribiendo.value = false
    }
  }

  function limpiar() {
    historial.value = []
  }

  return { historial, escribiendo, preguntar, limpiar, panelAbierto, sugerenciaContexto, sugerenciaPantalla, abrirPanel, cerrarPanel }
})
