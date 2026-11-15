<script setup lang="ts">
import { CalendarDays, CloudRain, Droplets, Trophy } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import { Bar } from 'vue-chartjs'
import { useI18n } from 'vue-i18n'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import NasaSourceTag from '@/components/ui/NasaSourceTag.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import { useTemaGrafico } from '@/composables/useGraficos'
import { api } from '@/services/api'
import type { DetalleLluvia } from '@/types/api'

/**
 * Detalle de la lluvia de un mes (clic en una barra de "¿Funciona?"): mm por día, total por semana,
 * día y semana más lluviosos. Datos: GPM IMERG diario (Final hasta 2025-09, Late después) vía /api.
 */
const props = defineProps<{ anio: number; mes: number | null; lat: number; lon: number }>()
defineEmits<{ cerrar: [] }>()

const { t, tm, rt, locale } = useI18n()
const tema = useTemaGrafico()
const datos = ref<DetalleLluvia | null>(null)
const estado = ref<'cargando' | 'listo' | 'sin' | 'error'>('cargando')

const nombreMes = computed(() =>
  props.mes ? new Date(props.anio, props.mes - 1, 1).toLocaleDateString(locale.value, { month: 'long', year: 'numeric' }) : '',
)

async function cargar() {
  if (!props.mes) return
  estado.value = 'cargando'
  datos.value = null
  try {
    const d = await api.getDetalleLluvia(props.anio, props.mes, props.lat, props.lon)
    datos.value = d
    estado.value = d.sinDato ? 'sin' : 'listo'
  } catch {
    estado.value = 'error'
  }
}
watch(() => [props.anio, props.mes], cargar, { immediate: true })

const fmtDia = (f: string, opc: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }) =>
  new Date(`${f}T12:00:00`).toLocaleDateString(locale.value, opc)

const maxSemana = computed(() => Math.max(1, ...(datos.value?.semanas ?? []).map((s) => Math.max(s.mm ?? 0, s.normal ?? 0))))

const data = computed(() => {
  const d = datos.value
  if (!d) return { labels: [], datasets: [] }
  const maxMm = d.diaMaximo?.mm ?? 0
  return {
    labels: d.dias.map((x) => Number(x.fecha.slice(8))),
    datasets: [
      ...(d.normalDia != null
        ? [{
            type: 'line' as const, label: t('validacion.detalle.normalDia'), data: d.dias.map(() => d.normalDia),
            borderColor: tema.value.normal, borderDash: [6, 5], borderWidth: 2, pointRadius: 0, order: 0,
          }]
        : []),
      {
        type: 'bar' as const, label: t('validacion.detalle.mmDia'), data: d.dias.map((x) => x.mm),
        backgroundColor: d.dias.map((x) => (x.mm !== null && x.mm === maxMm && maxMm > 0 ? '#ef4444' : tema.value.nasa)),
        borderRadius: 4, borderSkipped: false, maxBarThickness: 14, order: 1,
      },
    ],
  }
})

const options = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 500 },
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: tema.value.tooltipFondo, titleColor: tema.value.tooltipTexto, bodyColor: tema.value.tooltipTexto,
      padding: 10, cornerRadius: 10,
      callbacks: {
        title: (c: { dataIndex: number }[]) => (datos.value ? fmtDia(datos.value.dias[c[0].dataIndex].fecha, { weekday: 'short', day: 'numeric', month: 'short' }) : ''),
        label: (c: { dataset: { label?: string }; raw: unknown }) => ` ${c.dataset.label}: ${c.raw ?? '—'} mm`,
      },
    },
  },
  scales: {
    x: { grid: { display: false }, border: { display: false }, ticks: { color: tema.value.texto, maxRotation: 0, autoSkip: true, autoSkipPadding: 6 } },
    y: { grid: { color: tema.value.rejilla }, border: { display: false }, ticks: { color: tema.value.texto }, title: { display: true, text: 'mm/día', color: tema.value.texto } },
  },
}))

const etiquetaSemanas = computed(() => tm('validacion.detalle.semanas') as unknown[])
</script>

<template>
  <BottomSheet :abierto="!!mes" :titulo="t('validacion.detalle.titulo', { mes: nombreMes })" @cerrar="$emit('cerrar')">
    <div class="space-y-5 md:min-w-[28rem]">
      <div class="pr-12">
        <p class="text-xs font-bold tracking-[0.14em] text-agro-600 uppercase dark:text-brote-400">{{ $t('validacion.detalle.etiqueta') }}</p>
        <h2 class="font-display text-2xl font-bold tracking-tight first-letter:uppercase">{{ nombreMes }}</h2>
        <p v-if="datos?.parcial && datos.hasta" class="mt-1 text-sm text-amber-700 dark:text-amber-300">
          {{ $t('validacion.detalle.parcial', { fecha: fmtDia(datos.hasta) }) }}
        </p>
      </div>

      <div v-if="estado === 'cargando'" class="space-y-3">
        <SkeletonBlock class="h-20" />
        <SkeletonBlock class="h-48" />
        <p class="text-center text-xs text-stone-500 dark:text-stone-400">{{ $t('validacion.detalle.cargando') }}</p>
      </div>

      <p v-else-if="estado === 'sin'" class="rounded-2xl bg-arena p-4 text-sm dark:bg-white/5">{{ $t('validacion.detalle.sinDato') }}</p>
      <p v-else-if="estado === 'error'" class="rounded-2xl bg-red-50 p-4 text-sm text-red-800 dark:bg-red-500/10 dark:text-red-200">{{ $t('validacion.detalle.error') }}</p>

      <template v-else-if="datos">
        <!-- Resumen -->
        <div class="grid grid-cols-2 gap-2.5">
          <div class="rounded-2xl bg-arena p-3 dark:bg-white/5">
            <CloudRain class="size-4 text-nasa-600 dark:text-nasa-300" aria-hidden="true" />
            <p class="mt-1 font-display text-2xl font-extrabold tabular-nums">{{ datos.total }} <span class="text-sm font-medium">mm</span></p>
            <p class="text-xs text-stone-500 dark:text-stone-400">
              {{ datos.normalMes != null ? $t('validacion.detalle.totalVsNormal', { normal: Math.round(datos.normalMes) }) : $t('validacion.detalle.total') }}
              <b v-if="datos.veces != null" class="text-tinta dark:text-white">· {{ datos.veces }}×</b>
            </p>
          </div>
          <div class="rounded-2xl bg-arena p-3 dark:bg-white/5">
            <Trophy class="size-4 text-red-500" aria-hidden="true" />
            <p class="mt-1 font-display text-2xl font-extrabold tabular-nums">{{ datos.diaMaximo.mm }} <span class="text-sm font-medium">mm</span></p>
            <p class="text-xs text-stone-500 dark:text-stone-400">{{ $t('validacion.detalle.diaMax', { dia: fmtDia(datos.diaMaximo.fecha, { weekday: 'long', day: 'numeric' }) }) }}</p>
          </div>
          <div class="rounded-2xl bg-arena p-3 dark:bg-white/5">
            <Droplets class="size-4 text-nasa-600 dark:text-nasa-300" aria-hidden="true" />
            <p class="mt-1 font-display text-2xl font-extrabold tabular-nums">{{ datos.diasConLluvia }}</p>
            <p class="text-xs text-stone-500 dark:text-stone-400">{{ $t('validacion.detalle.diasConLluvia') }}</p>
          </div>
          <div class="rounded-2xl bg-arena p-3 dark:bg-white/5">
            <CalendarDays class="size-4 text-amber-600 dark:text-amber-300" aria-hidden="true" />
            <p class="mt-1 font-display text-2xl font-extrabold">{{ datos.semanaMaxima ? rt(etiquetaSemanas[datos.semanaMaxima - 1] as never) : '—' }}</p>
            <p class="text-xs text-stone-500 dark:text-stone-400">{{ $t('validacion.detalle.semanaMax') }}</p>
          </div>
        </div>

        <!-- Día por día -->
        <div>
          <p class="mb-2 text-sm font-bold">{{ $t('validacion.detalle.porDia') }}</p>
          <div class="h-48"><Bar :data="data as never" :options="options as never" /></div>
        </div>

        <!-- Por semana -->
        <div>
          <p class="mb-2 text-sm font-bold">{{ $t('validacion.detalle.porSemana') }}</p>
          <ul class="space-y-2">
            <li v-for="s in datos.semanas" :key="s.semana" class="grid grid-cols-[6.5rem_1fr_4rem] items-center gap-2 text-sm">
              <span class="text-xs text-stone-600 dark:text-stone-300">
                <b :class="s.semana === datos.semanaMaxima && 'text-red-600 dark:text-red-300'">{{ rt(etiquetaSemanas[s.semana - 1] as never) }}</b>
                <br />{{ fmtDia(s.desde, { day: 'numeric' }) }}–{{ fmtDia(s.hasta) }}
              </span>
              <span class="relative h-3 rounded-full bg-tinta/5 dark:bg-white/10">
                <span
                  class="absolute inset-y-0 left-0 rounded-full"
                  :class="s.semana === datos.semanaMaxima ? 'bg-red-500' : 'bg-nasa-500'"
                  :style="{ width: `${((s.mm ?? 0) / maxSemana) * 100}%` }"
                />
                <span
                  v-if="s.normal != null"
                  class="absolute -inset-y-1 w-0.5 bg-tinta/50 dark:bg-white/60"
                  :style="{ left: `${(s.normal / maxSemana) * 100}%` }"
                  :title="$t('validacion.detalle.normalSemana', { mm: s.normal })"
                />
              </span>
              <span class="text-right font-bold tabular-nums">{{ s.mm ?? '—' }} <span class="text-xs font-normal">mm</span></span>
            </li>
          </ul>
          <p v-if="datos.normalMes != null" class="mt-2 text-xs text-stone-500 dark:text-stone-400">{{ $t('validacion.detalle.leyendaNormal') }}</p>
        </div>

        <div class="flex flex-wrap items-center gap-2 text-xs text-stone-500 dark:text-stone-400">
          <NasaSourceTag :fuente="datos.fuente" corta />
          <span>{{ datos.producto }}</span>
        </div>
      </template>
    </div>
  </BottomSheet>
</template>
