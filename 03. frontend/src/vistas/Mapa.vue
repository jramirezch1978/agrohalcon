<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { estado, irA, analizar, valleCercano } from '../estado'
import { zonas } from '../data/catalogo'
import { t } from '../i18n'
import Icono from '../componentes/Icono.vue'

const div = ref<HTMLDivElement>()
const consulta = ref('')
const sugerencias = ref<{ nombre: string; lat: number; lon: number }[]>([])
const mostrarTarjeta = ref(true)
let mapa: L.Map | undefined
let marcador: L.Marker | undefined

const icono = L.divIcon({ className: 'pin-parcela', html: '<div class="pin-etq">Mi parcela</div><svg width="34" height="42" viewBox="0 0 24 30"><path d="M12 29s-10-9-10-16a10 10 0 0 1 20 0c0 7-10 16-10 16z" fill="#0f2a1c" stroke="#fff" stroke-width="1.5"/><circle cx="12" cy="12" r="4.5" fill="#c6f36b"/></svg>', iconSize: [34, 42], iconAnchor: [17, 42] })

async function nombreDe(lat: number, lon: number) {
  const v = valleCercano(lat, lon)
  try {
    const r = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&zoom=10&accept-language=${estado.idioma}&lat=${lat}&lon=${lon}`)
    const j = await r.json()
    const a = j.address ?? {}
    const lugar = a.county || a.city || a.town || a.state_district || a.state || j.name || 'Punto seleccionado'
    return v ? `${v.nombre}, ${a.country ?? 'Perú'}` : `${lugar}, ${a.country ?? ''}`.replace(/, $/, '')
  } catch {
    return v ? `${v.nombre}, Perú` : `Punto ${lat.toFixed(2)}, ${lon.toFixed(2)}`
  }
}

async function ponerParcela(lat: number, lon: number, nombre?: string) {
  estado.parcela = { lat: +lat.toFixed(4), lon: +lon.toFixed(4), nombre: nombre ?? 'Buscando el lugar…' }
  mostrarTarjeta.value = true
  marcador?.setLatLng([lat, lon])
  if (!nombre) estado.parcela.nombre = await nombreDe(lat, lon)
}

async function buscar() {
  const q = consulta.value.trim()
  if (q.length < 3) { sugerencias.value = []; return }
  try {
    const r = await fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=5&accept-language=${estado.idioma}&q=${encodeURIComponent(q)}`)
    const j = await r.json()
    sugerencias.value = j.map((x: { display_name: string; lat: string; lon: string }) => ({ nombre: x.display_name, lat: +x.lat, lon: +x.lon }))
  } catch { sugerencias.value = [] }
}

function elegir(s: { nombre: string; lat: number; lon: number }) {
  sugerencias.value = []
  consulta.value = ''
  const partes = s.nombre.split(',').map((x) => x.trim())
  ponerParcela(s.lat, s.lon, `${partes[0]}, ${partes[partes.length - 1]}`)
  mapa?.setView([s.lat, s.lon], 10)
}

function miUbicacion() {
  navigator.geolocation?.getCurrentPosition((p) => {
    ponerParcela(p.coords.latitude, p.coords.longitude)
    mapa?.setView([p.coords.latitude, p.coords.longitude], 11)
  })
}

async function analizarParcela() {
  irA('campana')
  await analizar()
}

onMounted(() => {
  mapa = L.map(div.value!, { zoomControl: false, worldCopyJump: true }).setView([estado.parcela.lat, estado.parcela.lon], 7)
  L.control.zoom({ position: 'bottomright' }).addTo(mapa)
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>', maxZoom: 18,
  }).addTo(mapa)
  // Valles agrícolas del norte (agro.zonas)
  for (const z of zonas) {
    L.circleMarker([z.lat, z.lon], { radius: 9, color: '#2f6b2a', weight: 2, fillColor: '#c6f36b', fillOpacity: 0.55 })
      .bindTooltip(`${z.nombre} · ${z.region}`)
      .on('click', () => ponerParcela(z.lat, z.lon, `${z.nombre}, Perú`))
      .addTo(mapa)
  }
  marcador = L.marker([estado.parcela.lat, estado.parcela.lon], { icon: icono, draggable: true }).addTo(mapa)
  marcador.on('dragend', () => { const p = marcador!.getLatLng(); ponerParcela(p.lat, p.lng) })
  mapa.on('click', (e: L.LeafletMouseEvent) => ponerParcela(e.latlng.lat, e.latlng.lng))
})
onBeforeUnmount(() => mapa?.remove())
</script>

<template>
  <section class="vista-mapa">
    <div ref="div" class="mapa"></div>

    <div class="buscador">
      <Icono n="buscar" />
      <input v-model="consulta" :placeholder="t('buscar')" @input="buscar" @keydown.enter="sugerencias[0] && elegir(sugerencias[0])" />
      <ul v-if="sugerencias.length" class="sugerencias">
        <li v-for="s in sugerencias" :key="s.nombre" @click="elegir(s)">{{ s.nombre }}</li>
      </ul>
    </div>

    <div class="leyenda tarjeta">
      <small>{{ t('nivelRiesgo').toUpperCase() }}</small>
      <span class="chip rojo"><Icono n="alerta" :t="12" /> {{ t('alto') }}</span>
      <span class="chip ambar"><Icono n="info" :t="12" /> {{ t('medio') }}</span>
      <span class="chip verde"><Icono n="check" :t="12" /> {{ t('bajo') }}</span>
      <small class="valles"><span class="punto"></span> Valles agrícolas</small>
    </div>

    <div class="mapa-botones">
      <button class="btn-verde" @click="miUbicacion"><Icono n="gps" /> {{ t('miUbicacion') }}</button>
    </div>

    <div v-if="mostrarTarjeta" class="tarjeta-parcela tarjeta">
      <div class="tp-cab">
        <span class="tp-ico"><Icono n="pin" /></span>
        <div>
          <small>{{ t('miParcela').toUpperCase() }}</small>
          <b>{{ estado.parcela.nombre }}</b>
          <span class="tenue">{{ t('coordenadas') }}: {{ estado.parcela.lat.toFixed(4) }}, {{ estado.parcela.lon.toFixed(4) }}</span>
        </div>
        <button class="x" aria-label="Cerrar" @click="mostrarTarjeta = false"><Icono n="cerrar" /></button>
      </div>
      <button class="btn-primario ancho" @click="analizarParcela">{{ t('analizar') }} <Icono n="flecha" /></button>
    </div>
  </section>
</template>
