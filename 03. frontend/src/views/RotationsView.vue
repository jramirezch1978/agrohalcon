<script setup lang="ts">
import { CalendarDays, MapPin } from 'lucide-vue-next'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import CropTypeSelector from '@/components/campaign/CropTypeSelector.vue'
import HonestyNote from '@/components/campaign/HonestyNote.vue'
import PerennialPlan from '@/components/campaign/PerennialPlan.vue'
import PlantingMonthSelector from '@/components/campaign/PlantingMonthSelector.vue'
import PrioritySelector from '@/components/campaign/PrioritySelector.vue'
import SoilSelector from '@/components/campaign/SoilSelector.vue'
import RotationCard from '@/components/rotations/RotationCard.vue'
import RotationSheet from '@/components/rotations/RotationSheet.vue'
import RotationsChart from '@/components/rotations/RotationsChart.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import { nombreRotacion } from '@/composables/useRotacion'
import { useAppStore } from '@/stores/app'
import { useAsistenteStore } from '@/stores/asistente'
import type { Rotacion } from '@/types/api'

const store = useAppStore()
const chat = useAsistenteStore()
const { t } = useI18n()

// Usa la recomendación del store; si no es de esta parcela (o no hay), la pide
onMounted(() => {
  if (!store.recomendacionEsDeParcela) store.cargarRecomendacion()
})
watch(() => store.idioma, () => store.cargarRecomendacion())

const rec = computed(() => (store.recomendacionEsDeParcela || store.desdeCache ? store.recomendacion : null))
/** De mayor a menor puntaje */
const rotaciones = computed(() => [...(rec.value?.rotaciones ?? [])].sort((a, b) => b.puntaje - a.puntaje))
const mejorId = computed(() => rotaciones.value[0]?.id)

const fecha = computed(() =>
  rec.value
    ? new Intl.DateTimeFormat(store.idioma, { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(rec.value.fecha + 'T12:00:00'))
    : '',
)
const nombreParcela = computed(() => {
  const p = store.parcela
  return p ? (p.nombre ?? `${p.lat.toFixed(3)}, ${p.lon.toFixed(3)}`) : ''
})

// Modo cultivo permanente: plan por etapas en lugar del comparador
const modoPermanente = computed(() => store.tipoCultivo === 'permanente')
/** Esperando el plan (la respuesta que hay en pantalla aún es del modo anterior) */
const esperandoModo = computed(() => store.cargando && modoPermanente.value !== !!rec.value?.plan)

// Detalle "¿Por qué este puntaje?"
const abierta = ref<Rotacion | null>(null)

const pregunta = (r: Rotacion) => t('rotaciones.preguntaRotacion', { nombre: nombreRotacion(r.nombre), puntaje: r.puntaje })
function preguntarPor(r: Rotacion) {
  abierta.value = null
  chat.abrirPanel(pregunta(r))
}

// El botón flotante sugiere preguntar por la rotación recomendada
watch(
  [rotaciones, () => store.idioma, () => store.prioridad],
  ([rs]) => {
    const clave = store.prioridad === 'cuidar_suelo' && rs[0]?.saludSuelo != null ? 'rotaciones.preguntaSuelo' : 'rotaciones.preguntaRecomendada'
    chat.sugerenciaPantalla = rs[0] ? t(clave, { nombre: nombreRotacion(rs[0].nombre) }) : null
  },
  { immediate: true },
)
onUnmounted(() => (chat.sugerenciaPantalla = null))
</script>

<template>
  <section>
    <header class="stagger mb-7">
      <p class="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm font-semibold text-agro-700 dark:text-brote-400">
        <span class="inline-flex min-w-0 items-center gap-1.5"><MapPin class="size-4 shrink-0" aria-hidden="true" /><span class="truncate">{{ nombreParcela }}</span></span>
        <span v-if="fecha" class="inline-flex items-center gap-1 text-xs font-medium text-stone-500 dark:text-stone-400"><CalendarDays class="size-3.5" aria-hidden="true" />{{ fecha }}</span>
      </p>
      <h1 class="mt-3 font-display text-[30px] leading-[1.05] font-extrabold tracking-tight text-balance sm:text-4xl">{{ modoPermanente ? $t('plan.titulo') : $t('rotaciones.titulo') }}</h1>
      <p v-if="!modoPermanente" class="mt-2 max-w-xl text-[15px] text-stone-600 dark:text-stone-400">{{ $t('rotaciones.tocaTarjeta') }}</p>
      <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
        <CropTypeSelector />
        <PlantingMonthSelector v-if="!modoPermanente" />
        <template v-if="!modoPermanente">
          <PrioritySelector />
          <SoilSelector />
        </template>
      </div>
      <HonestyNote class="mt-3" />
    </header>

    <!-- Cargando -->
    <div v-if="(!rec && (store.cargando || store.estado === 'inicial')) || esperandoModo" class="grid grid-cols-1 gap-5 md:grid-cols-3" aria-busy="true" role="status" :aria-label="$t('estados.cargando')">
      <div v-for="i in 3" :key="i" class="superficie flex items-center gap-4 p-6 md:flex-col">
        <SkeletonBlock alto="h-26" ancho="w-26" redondo="rounded-full" />
        <div class="flex-1 space-y-2 md:w-full"><SkeletonBlock alto="h-6" ancho="w-36" /><SkeletonBlock alto="h-6" ancho="w-24" redondo="rounded-full" /></div>
      </div>
    </div>

    <ErrorState v-else-if="!rec" @reintentar="store.cargarRecomendacion()" />

    <!-- Cultivo permanente -->
    <PerennialPlan v-else-if="rec.plan" :plan="rec.plan" :class="store.cargando && 'opacity-60 transition-opacity'" />

    <template v-else>
      <!-- Pidió permanente pero la API no envió plan (respuesta antigua): se muestra el comparador -->
      <p v-if="modoPermanente" class="mb-4 rounded-2xl bg-amber-50 px-4 py-3 text-sm text-amber-900 ring-1 ring-amber-300 dark:bg-amber-400/10 dark:text-amber-100 dark:ring-amber-400/30">
        {{ $t('plan.sinPlan') }}
      </p>
      <div class="grid grid-cols-1 gap-5 pt-2 transition-opacity md:grid-cols-3 md:items-start" :class="store.cargando && 'opacity-60'">
        <RotationCard
          v-for="(r, i) in rotaciones"
          :key="r.id"
          class="stagger"
          :style="{ '--i': i + 1 }"
          :rotacion="r"
          :recomendada="r.id === mejorId"
          :orden="i"
          @abrir="abierta = r"
        />
      </div>

      <div class="superficie stagger mt-6 p-5 sm:p-6" style="--i: 4">
        <SectionTitle :titulo="$t('rotaciones.comparacion')" class="mb-4" />
        <RotationsChart :rotaciones="rotaciones" />
      </div>
    </template>

    <RotationSheet :rotacion="abierta" :indicadores="rec?.indicadores" :perfil="rec?.perfil" @cerrar="abierta = null" @preguntar="preguntarPor" />
  </section>
</template>
