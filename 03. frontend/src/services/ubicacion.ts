import { Capacitor } from '@capacitor/core'
import { Geolocation } from '@capacitor/geolocation'

export interface Coordenadas {
  lat: number
  lon: number
}

/** Geolocalización: plugin nativo en Android, API del navegador en web. */
export async function obtenerUbicacion(): Promise<Coordenadas> {
  if (Capacitor.isNativePlatform()) {
    const p = await Geolocation.getCurrentPosition({ enableHighAccuracy: false, timeout: 12000 })
    return { lat: p.coords.latitude, lon: p.coords.longitude }
  }
  return new Promise((resolve, reject) => {
    if (!('geolocation' in navigator)) return reject(new Error('sin geolocalización'))
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
      reject,
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 600000 },
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
