/**
 * Leaflet configurado para Vite.
 * Problema conocido: Leaflet calcula la ruta de sus íconos desde el CSS y con Vite
 * el marcador por defecto aparece roto. Se importan las imágenes como módulos.
 */
import L from 'leaflet'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl })

/** Pin de "Mi parcela" con el estilo de la app. */
export function iconoParcela(etiqueta: string) {
  return L.divIcon({
    className: '',
    iconSize: [44, 52],
    iconAnchor: [22, 50],
    tooltipAnchor: [0, -46],
    html: `<div style="position:relative;width:44px;height:52px" role="img" aria-label="${etiqueta}">
      <span style="position:absolute;left:12px;bottom:0;width:20px;height:8px;border-radius:50%;background:rgba(0,0,0,.28);filter:blur(2px)"></span>
      <svg width="44" height="48" viewBox="0 0 44 48" style="position:absolute;top:0;left:0;filter:drop-shadow(0 6px 10px rgba(8,17,13,.35))">
        <path d="M22 46s16-14.5 16-26A16 16 0 0 0 6 20c0 11.5 16 26 16 26z" fill="#10231b" stroke="#fff" stroke-width="2"/>
        <circle cx="22" cy="20" r="7" fill="#c2ee5c"/>
      </svg></div>`,
  })
}

export default L
