import { Capacitor } from '@capacitor/core'
import { Geolocation } from '@capacitor/geolocation'

export interface Coordenadas {
  lat: number
  lon: number
}

/** Por qué no se pudo obtener la ubicación (cada motivo tiene su mensaje en mapa.aviso.*) */
export type MotivoUbicacion = 'denegado' | 'denegadoApp' | 'gpsApagado' | 'inseguro' | 'error'

export class ErrorUbicacion extends Error {
  constructor(public motivo: MotivoUbicacion, detalle?: string) {
    super(detalle ?? motivo)
  }
}

const NO_ACTIVADO = /not enabled|disabled|services/i

/**
 * App Android / iOS: pide el permiso del sistema operativo (diálogo nativo) y luego la posición.
 * - Android: el plugin falla con "Location services are not enabled" si el GPS está apagado.
 * - Si el usuario negó el permiso para siempre, el sistema ya no muestra el diálogo: hay que ir a Ajustes.
 */
async function ubicacionNativa(): Promise<Coordenadas> {
  let estado
  try {
    estado = await Geolocation.checkPermissions()
  } catch (e) {
    throw new ErrorUbicacion(NO_ACTIVADO.test(String((e as Error)?.message)) ? 'gpsApagado' : 'error', String(e))
  }
  if (estado.location !== 'granted' && estado.coarseLocation !== 'granted') {
    try {
      estado = await Geolocation.requestPermissions({ permissions: ['location', 'coarseLocation'] })
    } catch (e) {
      throw new ErrorUbicacion(NO_ACTIVADO.test(String((e as Error)?.message)) ? 'gpsApagado' : 'denegadoApp', String(e))
    }
    if (estado.location !== 'granted' && estado.coarseLocation !== 'granted') throw new ErrorUbicacion('denegadoApp')
  }
  // Primero precisión alta (GPS); si tarda o falla, red/wifi (precisión baja)
  for (const enableHighAccuracy of [true, false]) {
    try {
      const p = await Geolocation.getCurrentPosition({ enableHighAccuracy, timeout: enableHighAccuracy ? 15000 : 10000, maximumAge: 300000 })
      return { lat: p.coords.latitude, lon: p.coords.longitude }
    } catch (e) {
      const msg = String((e as Error)?.message)
      if (NO_ACTIVADO.test(msg)) throw new ErrorUbicacion('gpsApagado', msg)
      if (/denied|permission/i.test(msg)) throw new ErrorUbicacion('denegadoApp', msg)
    }
  }
  throw new ErrorUbicacion('error')
}

/** Geolocalización: permiso y GPS nativos en Android/iOS, API del navegador en la web. */
export async function obtenerUbicacion(): Promise<Coordenadas> {
  if (Capacitor.isNativePlatform()) return ubicacionNativa()
  // Los navegadores solo dan la ubicación en sitios seguros (https o localhost): en http ni siquiera preguntan
  if (!window.isSecureContext) throw new ErrorUbicacion('inseguro')
  if (!('geolocation' in navigator)) throw new ErrorUbicacion('error')
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
      (e) => reject(new ErrorUbicacion(e.code === 1 ? 'denegado' : 'error', e.message)),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 600000 },
    )
  })
}

export interface LugarEncontrado extends Coordenadas {
  nombre: string
  detalle: string
}

/** Buscador de lugares (OpenStreetMap Nominatim, gratuito y mundial). */
export async function buscarLugar(texto: string, idioma: string, signal?: AbortSignal): Promise<LugarEncontrado[]> {
  const url = new URL('https://nominatim.openstreetmap.org/search')
  url.search = new URLSearchParams({ q: texto, format: 'jsonv2', limit: '5', 'accept-language': idioma }).toString()
  const res = await fetch(url, { signal })
  if (!res.ok) throw new Error(String(res.status))
  const data = (await res.json()) as { lat: string; lon: string; name: string; display_name: string }[]
  return data.map((d) => ({
    lat: Number(d.lat),
    lon: Number(d.lon),
    nombre: d.name || d.display_name.split(',')[0],
    detalle: d.display_name.split(',').slice(1, 4).join(',').trim(),
  }))
}

/** Nombre legible de unas coordenadas (geocodificación inversa). */
export async function nombreDeLugar(lat: number, lon: number, idioma: string): Promise<string | undefined> {
  try {
    const url = new URL('https://nominatim.openstreetmap.org/reverse')
    url.search = new URLSearchParams({ lat: String(lat), lon: String(lon), format: 'jsonv2', zoom: '10', 'accept-language': idioma }).toString()
    const res = await fetch(url)
    if (!res.ok) return undefined
    const d = (await res.json()) as { address?: Record<string, string> }
    const a = d.address ?? {}
    const lugar = a.city || a.town || a.village || a.county || a.state
    return [lugar, a.country].filter(Boolean).join(', ') || undefined
  } catch {
    return undefined
  }
}
