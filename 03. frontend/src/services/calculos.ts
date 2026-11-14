/**
 * Cliente del servicio de cálculos en Python (allpashift-calculos). Es el modo principal de la demo:
 * todos los datos de pantalla salen de aquí (NASA POWER, GPM IMERG y MUR SST).
 *
 * VITE_CALCULOS_URL = URL del servicio (en el celular, la IP de la PC: http://192.168.x.x:8001).
 * Estas funciones LANZAN error si el servicio falla: quien llama decide el respaldo y lo avisa.
 */
import axios from 'axios'
import type { AniosValidacion, ClaveIndicador, Indicador, MapaRiesgo, OpcionesRecomendacion, Recomendacion, Validacion } from '@/types/api'

export const CALCULOS_URL: string = import.meta.env.VITE_CALCULOS_URL || ''

type Idioma = 'es' | 'en'

const http = axios.create({ baseURL: CALCULOS_URL, timeout: 20000 })

/** Indicador tal como lo envía Python: valor y nivel pueden ser null ("sin dato"). */
type IndicadorPython = Omit<Indicador, 'valor' | 'nivel'> & { valor: number | null; nivel: Indicador['nivel'] | null }

/** Quita los indicadores sin dato real: la app no muestra un número que no existe. */
function soloConDato(indicadores: Record<string, IndicadorPython>): Recomendacion['indicadores'] {
  const salida: Recomendacion['indicadores'] = {}
  for (const [clave, ind] of Object.entries(indicadores)) {
    if (ind.valor !== null && ind.nivel !== null) salida[clave as ClaveIndicador] = ind as Indicador
  }
  return salida
}

export async function calcularRecomendacion(lat: number, lon: number, idioma: Idioma, opciones: OpcionesRecomendacion): Promise<Recomendacion> {
  const { tipoCultivo, mesSiembra, cultivo } = opciones
  const { data } = await http.post('/calcular', {
    lat,
    lon,
    lang: idioma,
    tipoCultivo: tipoCultivo ?? 'temporal',
    mesSiembra: tipoCultivo === 'permanente' ? undefined : mesSiembra,
    cultivo: tipoCultivo === 'permanente' ? cultivo : undefined,
  })
  return { ...data, indicadores: soloConDato(data.indicadores) } as Recomendacion
}

export async function calcularMapa(region: string, idioma: Idioma): Promise<MapaRiesgo> {
  const { data } = await http.post<MapaRiesgo>('/mapa', { region, lang: idioma }, { timeout: 45000 })
  return data
}

export async function calcularValidacion(anio: number, lat: number, lon: number, idioma: Idioma): Promise<Validacion> {
  const { data } = await http.get<Validacion>('/validacion', { params: { anio, lat, lon, lang: idioma } })
  return data
}

export async function aniosValidacion(lat: number, lon: number): Promise<AniosValidacion> {
  const { data } = await http.get<AniosValidacion>('/validacion/anios', { params: { lat, lon } })
  return data
}
