<script setup lang="ts">
import { BellRing, CloudRain, History, Timer } from 'lucide-vue-next'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import RainChart from '@/components/charts/RainChart.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import NasaSourceTag from '@/components/ui/NasaSourceTag.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import { api } from '@/services/api'
import { PARCELA_PIURA, useAppStore } from '@/stores/app'
import type { Validacion } from '@/types/api'

/**
 * "¿Funciona?": TODO sale de /validacion del servicio de cálculos (lluvia GPM IMERG, alerta MUR SST,
 * semanas de anticipación). No hay números escritos a mano. Solo se ofrecen años con datos reales.
 */
const store = useAppStore()
const { t: $tt } = useI18n()

const anios = ref<number[]>([])
const anio = ref(2017)
const datos = ref<Validacion | null>(null)
const estado = ref<'cargando' | 'listo' | 'error'>('cargando')

async function cargarAnios() {
  const r = await api.getAniosValidacion(PARCELA_PIURA.lat, PARCELA_PIURA.lon)
  anios.value = r.anios
  if (!r.anios.includes(anio.value) && r.anios.length) anio.value = r.anios.at(-1)!
}

async function cargar() {
  estado.value = 'cargando'
  try {
    // La validación de El Niño costero se hace sobre Piura
    datos.value = await api.getValidacion(anio.value, PARCELA_PIURA.lat, PARCELA_PIURA.lon, store.idioma)
    estado.value = 'listo'
  } catch {
    estado.value = 'error'
  }
}
const selector = ref<HTMLElement>()
/** El año elegido (p. ej. 2017) siempre visible en el selector, aunque la lista empiece en 2001 */
async function mostrarAnioElegido() {
  await nextTick()
  selector.value?.querySelector('[aria-checked="true"]')?.scrollIntoView({ inline: 'center', block: 'nearest' })
}
onMounted(async () => {
  await cargarAnios()
  mostrarAnioElegido()
  await cargar()
})
watch([anio, () => store.idioma], cargar)

const fmtFecha = (iso: string) =>
  new Intl.DateTimeFormat(store.idioma, { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(iso + 'T12:00:00'))
const fmtMes = (iso: string) =>
  new Intl.DateTimeFormat(store.idioma, { month: 'long', year: 'numeric' }).format(new Date(iso + '-15T12:00:00'))

const lluvia = computed(() => datos.value?.series.lluvia)
/** Solo se dibuja si hay al menos un mes con dato real */
const hayLluvia = computed(() => !!lluvia.value && lluvia.value.fuente !== 'sin dato' && lluvia.value.valores.some((v) => v !== null))

/** Lluvia del mes máximo: cuántas veces lo normal (calculado de la serie que llegó) */
const pico = computed(() => {
  const d = datos.value
  if (!d?.mesLluviaMaxima || !lluvia.value) return null
  const i = Number(d.mesLluviaMaxima.slice(5, 7)) - 1
  const v = lluvia.value.valores[i]
  const n = lluvia.value.normal[i]
  if (v === null || n === null || n === 0) return null
  return { mes: fmtMes(d.mesLluviaMaxima), veces: Math.round((v / n) * 10) / 10, mm: Math.round(v) }
})

/** Cronología armada con los datos (nada escrito a mano) */
const hitos = computed(() => {
  const d = datos.value
  if (!d) return []
  const lista: { texto: string; tono: 'aviso' | 'drenaje' | 'lluvia' | 'realidad' }[] = []
  const a = d.alerta
  if (a) {
    lista.push({
      tono: 'aviso',
      texto:
        a.indicador === 'elNino'
          ? `${fmtFecha(a.fecha)}: ${$tt('validacion.hitoMar', { valor: signo(a.valor), fuente: a.fuente })}`
          : `${fmtFecha(a.fecha)}: ${a.motivo} (${a.fuente})`,
    })
    if (a.alertaDrenaje && a.alertaDrenaje.fecha !== a.fecha) {
      lista.push({ tono: 'drenaje', texto: `${fmtFecha(a.alertaDrenaje.fecha)}: ${$tt('validacion.hitoDrenaje', { valor: signo(a.alertaDrenaje.valor) })}` })
    }
  }
  if (pico.value && lluvia.value) lista.push({ tono: 'lluvia', texto: $tt('validacion.hitoLluvia', { mes: pico.value.mes, veces: pico.value.veces, fuente: lluvia.value.fuente }) })
  if (d.realidad) lista.push({ tono: 'realidad', texto: `${d.realidad.resumen} (${d.realidad.fuente})` })
  return lista
})

const signo = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(1)}`
</script>

<template>
  <section>
    <PageHeader :titulo="$t('validacion.titulo')" :subtitulo="$t('validacion.subtitulo')" etiqueta="Piura · El Niño costero" />

    <!-- Selector de año: solo años con datos reales -->
    <div ref="selector" class="no-scrollbar stagger -mx-4 mb-6 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:px-0" role="radiogroup" :aria-label="$t('validacion.anio')" style="--i: 1">
      <button
        v-for="a in anios"
        :key="a"
        type="button"
        role="radio"
        :aria-checked="anio === a"
        class="relative shrink-0 rounded-2xl px-5 py-3 font-display text-base font-bold tabular-nums transition"
        :class="anio === a ? 'bg-tinta text-white shadow-float dark:bg-brote-400 dark:text-tinta' : 'bg-white text-stone-600 shadow-card hover:text-tinta dark:bg-noche-2 dark:text-stone-300'"
        @click="anio = a"
      >
        {{ a }}
        <span v-if="a === 2017" class="absolute -top-1 -right-1 size-3 rounded-full bg-red-500 ring-2 ring-arena dark:ring-noche" />
      </button>
    </div>

    <ErrorState v-if="estado === 'error'" @reintentar="cargar" />

    <div v-else-if="estado === 'cargando' && !datos" class="space-y-4">
      <SkeletonBlock alto="h-48" redondo="rounded-[28px]" />
      <SkeletonBlock alto="h-72" redondo="rounded-[28px]" />
    </div>

    <div v-else-if="datos" class="space-y-4 transition-opacity" :class="estado === 'cargando' && 'opacity-50'">
      <!-- Qué habría dicho AllpaShift -->
      <article class="bosque stagger relative overflow-hidden rounded-[30px] p-6 text-white shadow-float sm:p-8" style="--i: 2">
        <History class="absolute -right-6 -bottom-8 size-48 text-white/5" aria-hidden="true" />
        <p class="text-xs font-bold tracking-[0.14em] text-brote-300 uppercase">
          {{ datos.alerta ? $t('validacion.habriaAvisado', { fecha: fmtFecha(datos.alerta.fecha) }) : $t('validacion.habriaRecomendado') }}
        </p>
        <p class="mt-3 max-w-[30ch] font-display text-2xl leading-tight font-bold tracking-tight text-balance sm:text-3xl">
          {{ datos.alerta?.accion ?? datos.recomendacionPrevia.accion }}
        </p>
        <p class="mt-3 max-w-2xl text-[15px] text-white/80">{{ datos.alerta?.motivo ?? datos.recomendacionPrevia.motivo }}</p>
        <NasaSourceTag class="mt-4" :fuente="datos.alerta?.fuente ?? datos.recomendacionPrevia.fuente" sobre-oscuro />
        <p v-if="datos.alerta?.nota" class="mt-3 text-sm text-amber-200">{{ datos.alerta.nota }}</p>
        <p class="mt-5 max-w-2xl rounded-2xl bg-white/8 p-4 text-[15px] font-medium ring-1 ring-white/10">{{ datos.resumen }}</p>
      </article>

      <!-- Cifras (todas calculadas por el servicio) -->
      <div v-if="pico || datos.semanasAnticipacion !== null || datos.alerta" class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div v-if="pico" class="superficie stagger p-4" style="--i: 3">
          <CloudRain class="size-5 text-nasa-600 dark:text-nasa-300" aria-hidden="true" />
          <p class="mt-2 font-display text-3xl font-extrabold tracking-tight tabular-nums">{{ pico.veces }}×</p>
          <p class="text-xs text-stone-500 dark:text-stone-400">{{ $t('validacion.picoLluviaMes', { mes: pico.mes, mm: pico.mm }) }}</p>
        </div>
        <div v-if="datos.semanasAnticipacion !== null" class="superficie stagger p-4" style="--i: 4">
          <Timer class="size-5 text-amber-600 dark:text-amber-300" aria-hidden="true" />
          <p class="mt-2 font-display text-3xl font-extrabold tracking-tight tabular-nums">{{ datos.semanasAnticipacion }}</p>
          <p class="text-xs text-stone-500 dark:text-stone-400">{{ $t('validacion.anticipacion') }}</p>
        </div>
        <div v-if="datos.alerta" class="superficie stagger p-4" style="--i: 5">
          <BellRing class="size-5 text-red-600 dark:text-red-300" aria-hidden="true" />
          <p class="mt-2 font-display text-xl leading-tight font-extrabold tracking-tight">{{ fmtFecha(datos.alerta.fecha) }}</p>
          <p class="text-xs text-stone-500 dark:text-stone-400">{{ $t('validacion.fechaAviso') }}</p>
        </div>
      </div>

      <!-- Lluvia mensual vs. lo normal (oculta si no hay dato real) -->
      <div v-if="hayLluvia && lluvia" class="superficie stagger p-5" style="--i: 6">
        <SectionTitle :titulo="$t('validacion.lluvia')" class="mb-3"><NasaSourceTag :fuente="lluvia.fuente" corta /></SectionTitle>
        <RainChart :valores="lluvia.valores" :normal="lluvia.normal" :anio="anio" />
      </div>

      <!-- Cronología, armada con los datos -->
      <div v-if="hitos.length" class="superficie stagger p-5 sm:p-6" style="--i: 7">
        <SectionTitle :titulo="$t('validacion.cronologia')" class="mb-4" />
        <ol class="relative space-y-5 border-l-2 border-dashed border-tinta/10 pl-6 dark:border-white/10">
          <li v-for="(h, i) in hitos" :key="i" class="relative">
            <span
              class="absolute top-0.5 -left-[33px] grid size-4 place-items-center rounded-full ring-4 ring-white dark:ring-noche-2"
              :class="{ aviso: 'bg-amber-400', drenaje: 'bg-brote-400', lluvia: 'bg-red-500', realidad: 'bg-nasa-500' }[h.tono]"
            />
            <p class="text-[15px]" :class="h.tono === 'drenaje' && 'font-bold'">{{ h.texto }}</p>
          </li>
        </ol>
      </div>
    </div>
  </section>
</template>
