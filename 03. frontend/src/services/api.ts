import axios, { AxiosError } from 'axios'
import { i18n } from '@/i18n'
import { useOrigenStore } from '@/stores/origen'
import type {
  AniosValidacion,
  DetalleLluvia,
  Cultivo,
  MapaRiesgo,
  OpcionesRecomendacion,
  PreguntaAsistente,
  Recomendacion,
  RespuestaAsistente,
  Validacion,
  SueloPropuesto,
} from '@/types/api'
import { aniosValidacion, detalleLluvia, calcularMapa, calcularRecomendacion, calcularValidacion, CALCULOS_URL, soloConDato, sueloPython } from './calculos'
import { mockAniosValidacion, mockCultivos, mockMapa, mockRecomendacion, mockValidacion } from './mocks'
import { responderConPlantillas } from './asistentePlantillas'
import { climatologiaPower } from './nasaPower'

/**
 * De dónde salen los datos:
 * - 'python'  (modo principal): servicio de cálculos en VITE_CALCULOS_URL → datos reales de la NASA.
 * - 'java'    : backend Java en VITE_API_URL (VITE_USE_MOCK=false y sin VITE_CALCULOS_URL).
 * - 'ejemplo' : datos simulados, etiquetados "Ejemplo" y con banner fijo en pantalla.
 * Si el servicio falla, se pasa al respaldo CON aviso (toast + banner), nunca en silencio.
 */
export const USE_MOCK = (import.meta.env.VITE_USE_MOCK ?? 'true') !== 'false'
export const MODO: 'python' | 'java' | 'ejemplo' = CALCULOS_URL ? 'python' : USE_MOCK ? 'ejemplo' : 'java'

export type Idioma = 'es' | 'en'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8080',
  timeout: 15000,
})

/** Error con mensaje amigable para mostrar en la UI. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly tipo: 'red' | 'servidor' | 'desconocido',
  ) {
    super(message)
  }
}

http.interceptors.response.use(
  (r) => r,
  (e: AxiosError) => {
    if (!e.response) return Promise.reject(new ApiError('Sin conexión con el servidor', 'red'))
    return Promise.reject(new ApiError(`Error del servidor (${e.response.status})`, 'servidor'))
  },
)

const aApiError = (e: unknown) =>
  e instanceof ApiError ? e : (e as AxiosError)?.response ? new ApiError('Error del servicio de cálculos', 'servidor') : new ApiError('Sin conexión con el servicio de cálculos', 'red')

/** Simula latencia de red para que los skeletons se vean en modo ejemplo. */
const demora = <T>(data: T, ms = 600): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(structuredClone(data)), ms))

/** Datos de ejemplo de una pantalla: se registran como 'ejemplo' (banner) y, si fue por un fallo, se avisa. */
function deEjemplo<T>(recurso: 'mapa' | 'validacion' | 'recomendacion', datos: T, porFallo: boolean): T {
  const origen = useOrigenStore()
  origen.registrar(recurso, 'ejemplo')
  if (porFallo) origen.avisar(i18n.global.t('origen.servicioCaido'))
  return datos
}

/**
 * Modo Java: si la API respondió con el último dato guardado porque el servicio de cálculos no respondió
 * (header X-Desde-Cache), se marca como copia guardada y se avisa con su fecha. Nunca en silencio.
 */
function marcarOrigenJava(recurso: 'recomendacion' | 'validacion', headers: Record<string, unknown>) {
  const origen = useOrigenStore()
  if (String(headers['x-desde-cache']) === 'true') {
    origen.registrar(recurso, 'cache')
    origen.avisar(i18n.global.t('origen.usandoCache', { fecha: String(headers['x-fecha-dato'] ?? '?') }))
  } else {
    origen.registrar(recurso, 'real')
  }
}

export const api = {
  /** Lanza ApiError si el servicio no responde: el store decide entre la copia guardada y el ejemplo. */
  async getRecomendacion(lat: number, lon: number, idioma: Idioma = 'es', opciones: OpcionesRecomendacion = {}): Promise<Recomendacion> {
    if (MODO === 'ejemplo') return deEjemplo('recomendacion', await api.getRecomendacionEjemplo(lat, lon, idioma, opciones), false)
    if (MODO === 'python') {
      try {
        const r = await calcularRecomendacion(lat, lon, idioma, opciones)
        useOrigenStore().registrar('recomendacion', 'real')
        return r
      } catch (e) {
        throw aApiError(e)
      }
    }
    const { tipoCultivo, mesSiembra, cultivo, prioridad, tipoSuelo, salinidad, fuenteSuelo } = opciones
    const temporal = tipoCultivo !== 'permanente'
    const params = {
      lat,
      lon,
      lang: idioma,
      tipoCultivo,
      mesSiembra: temporal ? mesSiembra : undefined,
      cultivo: temporal ? undefined : cultivo,
      ...(temporal ? { prioridad, tipoSuelo, salinidad, fuenteSuelo } : {}),
    }
    const r = await http.get<Recomendacion>('/api/recomendacion', { params })
    marcarOrigenJava('recomendacion', r.headers)
    // Igual que en modo Python: un indicador sin dato real (valor null) no se muestra
    return { ...r.data, indicadores: soloConDato(r.data.indicadores as never) }
  },

  /** Tipo de suelo PROPUESTO por SoilGrids (ISRIC, no NASA). Sin servicio o sin dato → tipoSuelo null. */
  async getSuelo(lat: number, lon: number): Promise<SueloPropuesto> {
    const sinDato: SueloPropuesto = { tipoSuelo: null, arena: null, limo: null, arcilla: null, fuente: 'sin dato' }
    if (MODO === 'ejemplo') return sinDato
    try {
      if (MODO === 'python') return await sueloPython(lat, lon)
      const { data } = await http.get<SueloPropuesto>('/api/suelo', { params: { lat, lon }, timeout: 65000 })
      return data
    } catch {
      return sinDato
    }
  },

  /** Recomendación de EJEMPLO (todas las fuentes dicen "Ejemplo"). */
  async getRecomendacionEjemplo(lat: number, lon: number, idioma: Idioma = 'es', opciones: OpcionesRecomendacion = {}): Promise<Recomendacion> {
    return demora(mockRecomendacion(lat, lon, idioma, opciones, await climatologiaPower(lat, lon)), 300)
  },

  async getMapa(region = 'piura', idioma: Idioma = 'es'): Promise<MapaRiesgo> {
    if (MODO === 'python') {
      try {
        const m = await calcularMapa(region, idioma)
        useOrigenStore().registrar('mapa', 'real')
        return m
      } catch {
        return deEjemplo('mapa', await demora(mockMapa(region), 200), true)
      }
    }
    if (MODO === 'ejemplo') return deEjemplo('mapa', await demora(mockMapa(region), 400), false)
    const { data } = await http.get<MapaRiesgo>('/api/mapa', { params: { region, lang: idioma } })
    useOrigenStore().registrar('mapa', 'real')
    return data
  },

  async getCultivos(idioma: Idioma = 'es'): Promise<Cultivo[]> {
    if (MODO !== 'java') return demora(mockCultivos(idioma), 300)
    const { data } = await http.get<Cultivo[]>('/api/cultivos', { params: { lang: idioma } })
    return data
  },

  /**
   * Asistente SIN IA: responde con plantillas a partir de la recomendación YA calculada (la que está en
   * pantalla). Solo cita las fuentes que trae esa recomendación. Con backend Java usa /api/asistente.
   */
  async preguntarAsistente(cuerpo: PreguntaAsistente, rec: Recomendacion | null): Promise<RespuestaAsistente> {
    if (MODO !== 'java') {
      if (!rec) throw new ApiError('Sin recomendación calculada', 'desconocido')
      return demora(responderConPlantillas(cuerpo.pregunta, rec, cuerpo.idioma), 700 + Math.random() * 600)
    }
    // Plan B a los 10 s (ver stores/asistente.ts)
    const { data } = await http.post<RespuestaAsistente>('/api/asistente', cuerpo, { timeout: 10000 })
    return data
  },

  async getValidacion(anio: number, lat: number, lon: number, idioma: Idioma = 'es'): Promise<Validacion> {
    if (MODO === 'python') {
      try {
        const v = await calcularValidacion(anio, lat, lon, idioma)
        useOrigenStore().registrar('validacion', 'real')
        return v
      } catch {
        return deEjemplo('validacion', await demora(mockValidacion(anio, lat, lon, idioma), 200), true)
      }
    }
    if (MODO === 'ejemplo') return deEjemplo('validacion', await demora(mockValidacion(anio, lat, lon, idioma)), false)
    const r = await http.get<Validacion>('/api/validacion', { params: { anio, lat, lon, lang: idioma } })
    marcarOrigenJava('validacion', r.headers)
    return r.data
  },

  /** Lluvia de un mes día por día y por semana (clic en una barra de "¿Funciona?"). */
  async getDetalleLluvia(anio: number, mes: number, lat: number, lon: number): Promise<DetalleLluvia> {
    if (MODO === 'python') return detalleLluvia(anio, mes, lat, lon)
    if (MODO === 'ejemplo') throw new ApiError('Sin detalle diario en modo de ejemplo', 'desconocido')
    const { data } = await http.get<DetalleLluvia>('/api/validacion/detalle', { params: { anio, mes, lat, lon }, timeout: 60000 })
    return data
  },

  /** Años con datos reales (el selector de "¿Funciona?" solo ofrece estos). */
  async getAniosValidacion(lat: number, lon: number): Promise<AniosValidacion> {
    if (MODO === 'python') {
      try {
        return await aniosValidacion(lat, lon)
      } catch {
        return mockAniosValidacion()
      }
    }
    if (MODO === 'ejemplo') return mockAniosValidacion()
    const { data } = await http.get<AniosValidacion>('/api/validacion/anios', { params: { lat, lon } })
    return data
  },
}
