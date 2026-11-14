<script setup lang="ts">
import { ArrowRight, CalendarDays, Flower2, MapPin, Pencil } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import CropTypeSelector from '@/components/campaign/CropTypeSelector.vue'
import AlertSummary from '@/components/home/AlertSummary.vue'
import AskCard from '@/components/home/AskCard.vue'
import BestRotationCard from '@/components/home/BestRotationCard.vue'
import IndicatorCard from '@/components/home/IndicatorCard.vue'
import InfoBottomSheet from '@/components/home/InfoBottomSheet.vue'
import LoadingSkeleton from '@/components/home/LoadingSkeleton.vue'
import RecommendationHero from '@/components/home/RecommendationHero.vue'
import AlertBanner from '@/components/ui/AlertBanner.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { useCompartir } from '@/composables/useCompartir'
import { CLAVES_INDICADOR } from '@/composables/useRiesgo'
import { useAppStore } from '@/stores/app'
import type { ClaveIndicador } from '@/types/api'

const store = useAppStore()
const router = useRouter()
const { compartirWhatsapp } = useCompartir()

onMounted(() => store.cargarRecomendacion())
// Los textos vienen del backend en el idioma pedido: recargar al cambiarlo
watch(() => store.idioma, () => store.cargarRecomendacion())

/**
 * Qué mostrar:
 * - La recomendación si es de esta parcela.
 * - Si falló la red, la última guardada (aunque sea de otra parcela) con aviso.
 */
const rec = computed(() => (store.recomendacionEsDeParcela || store.desdeCache ? store.recomendacion : null))
const abierto = ref<ClaveIndicador | null>(null)
/** Solo se muestran los indicadores con dato real (p. ej. sin MUR SST no hay tarjeta de El Niño) */
const clavesConDato = computed(() => (rec.value ? CLAVES_INDICADOR.filter((k) => rec.value!.indicadores[k]) : []))

const nombreParcela = computed(() => {
  const p = store.parcela
  return p ? (p.nombre ?? `${p.lat.toFixed(3)}, ${p.lon.toFixed(3)}`) : ''
})
const coordenadas = computed(() => (store.parcela ? `${store.parcela.lat.toFixed(3)}, ${store.parcela.lon.toFixed(3)}` : ''))
const fecha = computed(() =>
  rec.value
    ? new Intl.DateTimeFormat(store.idioma, { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(rec.value.fecha + 'T12:00:00'))
    : '',
)
</script>

<template>
  <section>
    <!-- Encabezado: parcela, fecha y cambiar parcela -->
    <header class="stagger mb-5">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="flex items-center gap-1.5 text-sm font-semibold text-agro-700 dark:text-brote-400">
            <MapPin class="size-4 shrink-0" aria-hidden="true" />
            <span class="truncate">{{ nombreParcela }}</span>
          </p>
          <p class="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-stone-500 dark:text-stone-400">
            <span v-if="store.parcela?.nombre" class="tabular-nums">{{ coordenadas }}</span>
            <span v-if="fecha" class="inline-flex items-center gap-1"><CalendarDays class="size-3.5" aria-hidden="true" />{{ fecha }}</span>
          </p>
        </div>
        <RouterLink
          to="/mapa"
          class="inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-full bg-white px-4 text-sm font-semibold shadow-card ring-1 ring-tinta/8 transition hover:bg-arena dark:bg-noche-2 dark:ring-white/10 dark:hover:bg-white/8"
        >
          <Pencil class="size-4" aria-hidden="true" />{{ $t('acciones.cambiarParcela') }}
        </RouterLink>
      </div>
      <h1 class="mt-4 font-display text-[30px] leading-[1.05] font-extrabold tracking-tight text-balance sm:text-4xl">
        {{ $t('inicio.titulo') }}
      </h1>
      <p class="mt-2 max-w-xl text-[15px] text-stone-600 dark:text-stone-400">{{ $t('inicio.subtitulo') }}</p>
      <CropTypeSelector class="mt-4" />
    </header>

    <!-- Cargando (sin datos de esta parcela todavía) -->
    <LoadingSkeleton v-if="!rec && (store.estado === 'cargando' || store.estado === 'inicial')" />

    <!-- Error sin nada guardado -->
    <ErrorState v-else-if="!rec" @reintentar="store.cargarRecomendacion()" />

    <div v-else class="space-y-4 transition-opacity duration-300" :class="store.cargando && 'opacity-60'">
      <AlertBanner v-if="store.desdeCache" tono="offline" :titulo="$t('inicio.sinConexion', { fecha })" class="stagger">
        {{ $t('inicio.sinConexionDetalle') }}
        <button type="button" class="ml-1 font-bold underline underline-offset-2" @click="store.cargarRecomendacion()">{{ $t('acciones.reintentar') }}</button>
      </AlertBanner>
      <AlertSummary :indicadores="rec.indicadores" class="stagger" />

      <div class="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <RecommendationHero
          class="stagger lg:row-span-2"
          style="--i: 1"
          :que-hacer="rec.queHacer"
          :nivel="store.nivelGeneral"
          :mes-siembra="rec.plan || store.tipoCultivo === 'permanente' ? undefined : store.mesSiembra"
          @compartir="compartirWhatsapp"
        />
        <BestRotationCard v-if="store.mejorRotacion && !rec.plan" class="stagger" style="--i: 2" :rotacion="store.mejorRotacion" />
        <!-- Cultivo permanente: etapa actual -->
        <RouterLink
          v-else-if="rec.plan"
          to="/campana"
          class="superficie stagger group flex items-center gap-4 p-5 transition hover:-translate-y-0.5 hover:shadow-float"
          style="--i: 2"
        >
          <span class="grid size-14 shrink-0 place-items-center rounded-2xl bg-agro-700 text-white dark:bg-brote-400 dark:text-tinta">
            <Flower2 class="size-7" aria-hidden="true" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block text-xs font-bold tracking-[0.12em] text-agro-600 uppercase dark:text-brote-400">{{ $t('plan.etapaActual') }}</span>
            <span class="block font-display text-lg font-bold tracking-tight">{{ rec.plan.cultivo }} · <span class="capitalize">{{ rec.plan.etapaActual }}</span></span>
            <span class="block text-sm text-stone-500 dark:text-stone-400">{{ $t('inicio.verPlan') }}</span>
          </span>
          <ArrowRight class="size-5 shrink-0 text-stone-400 transition group-hover:translate-x-1" aria-hidden="true" />
        </RouterLink>
        <AskCard class="stagger hidden lg:block" style="--i: 3" />
      </div>

      <div class="pt-4">
        <SectionTitle :titulo="$t('inicio.indicadoresTitulo')" :subtitulo="$t('inicio.tocaIndicador')" class="stagger mb-3" style="--i: 3" />
        <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <IndicatorCard
            v-for="(k, i) in clavesConDato"
            :key="`${k}-${rec.lat}-${rec.lon}`"
            class="stagger"
            :style="{ '--i': i + 4 }"
            :orden="i"
            :clave="k"
            :indicador="rec.indicadores[k]!"
            @abrir="abierto = k"
          />
        </div>
      </div>

      <BaseButton class="stagger w-full sm:w-auto" style="--i: 8" variante="secundario" :icono-derecha="ArrowRight" @click="router.push('/campana')">
        {{ rec.plan ? $t('inicio.verPlan') : $t('acciones.verRotaciones') }}
      </BaseButton>

      <AskCard class="stagger lg:hidden" style="--i: 9" />
    </div>

    <InfoBottomSheet :clave="abierto" :indicador="abierto && rec ? (rec.indicadores[abierto] ?? null) : null" @cerrar="abierto = null" />
  </section>
</template>
