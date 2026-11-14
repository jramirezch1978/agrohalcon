<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { useI18n } from 'vue-i18n'
import { useTemaGrafico } from '@/composables/useGraficos'

/** Lluvia mensual del año vs. lo normal. Los meses sin dato (null) quedan vacíos: nunca se rellenan. */
const props = defineProps<{ valores: (number | null)[]; normal: (number | null)[]; anio: number }>()
const tema = useTemaGrafico()
const { t, tm, rt } = useI18n()
const meses = computed(() => (tm('validacion.meses') as unknown[]).map((m) => rt(m as never)))

const data = computed(() => ({
  labels: meses.value,
  datasets: [
    {
      type: 'line' as const,
      label: t('validacion.normal'),
      data: [...props.normal], // copia simple: Chart.js no debe recibir objetos reactivos de Vue
      borderColor: tema.value.normal,
      borderDash: [6, 5],
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.4,
      spanGaps: false,
      order: 0,
    },
    {
      type: 'bar' as const,
      label: String(props.anio),
      data: [...props.valores],
      // Rojo: más del doble de lo normal (y más de 20 mm, para no marcar meses secos)
      backgroundColor: props.valores.map((v, i) => {
        const n = props.normal[i]
        return v !== null && n !== null && v > n * 2 && v > 20 ? '#ef4444' : tema.value.nasa
      }),
      borderRadius: 8,
      borderSkipped: false,
      maxBarThickness: 26,
      order: 1,
    },
  ],
}))

const options = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 900 },
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { position: 'bottom' as const, labels: { color: tema.value.texto, usePointStyle: true, boxWidth: 8, padding: 16 } },
    tooltip: {
      backgroundColor: tema.value.tooltipFondo, titleColor: tema.value.tooltipTexto, bodyColor: tema.value.tooltipTexto,
      padding: 10, cornerRadius: 10,
      callbacks: { label: (c: { dataset: { label?: string }; raw: unknown }) => ` ${c.dataset.label}: ${c.raw ?? '—'} mm` },
    },
  },
  scales: {
    x: { grid: { display: false }, border: { display: false }, ticks: { color: tema.value.texto } },
    y: { grid: { color: tema.value.rejilla }, border: { display: false }, ticks: { color: tema.value.texto }, title: { display: true, text: 'mm', color: tema.value.texto } },
  },
}))
</script>

<template>
  <div class="h-64"><Bar :data="data as never" :options="options as never" /></div>
</template>
