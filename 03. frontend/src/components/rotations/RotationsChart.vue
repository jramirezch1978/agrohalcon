<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { useTemaGrafico } from '@/composables/useGraficos'
import { ESTILO_RIESGO } from '@/composables/useRiesgo'
import { nombreRotacion } from '@/composables/useRotacion'
import type { Rotacion } from '@/types/api'

const props = defineProps<{ rotaciones: Rotacion[] }>()
const tema = useTemaGrafico()

const data = computed(() => ({
  labels: props.rotaciones.map((r) => nombreRotacion(r.nombre)),
  datasets: [
    {
      data: props.rotaciones.map((r) => r.puntaje),
      backgroundColor: props.rotaciones.map((r) => ESTILO_RIESGO[r.riesgo].hex),
      borderRadius: 12,
      borderSkipped: false,
      barThickness: 26,
    },
  ],
}))

const options = computed(() => ({
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 1100, easing: 'easeOutQuart' as const, delay: 300 },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: tema.value.tooltipFondo,
      titleColor: tema.value.tooltipTexto,
      bodyColor: tema.value.tooltipTexto,
      padding: 10,
      cornerRadius: 10,
      displayColors: false,
      callbacks: { label: (c: { raw: unknown }) => `${c.raw} / 100` },
    },
  },
  scales: {
    x: { min: 0, max: 100, grid: { color: tema.value.rejilla }, border: { display: false }, ticks: { color: tema.value.texto, stepSize: 25 } },
    y: { grid: { display: false }, border: { display: false }, ticks: { color: tema.value.texto, font: { weight: 600 as const, size: 13 } } },
  },
}))
</script>

<template>
  <div class="h-48" role="img" :aria-label="rotaciones.map((r) => `${nombreRotacion(r.nombre)}: ${r.puntaje}`).join(', ')">
    <Bar :data="data" :options="options" />
  </div>
</template>
