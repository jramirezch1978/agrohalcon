<script setup lang="ts">
import { ArrowDown, ArrowUp, Minus } from 'lucide-vue-next'
import { computed, toRef } from 'vue'
import NasaSourceTag from '@/components/ui/NasaSourceTag.vue'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import { useContador, useMontado } from '@/composables/useAnimacion'
import { useIndicador } from '@/composables/useIndicador'
import { ESTILO_RIESGO, ICONO_INDICADOR } from '@/composables/useRiesgo'
import type { ClaveIndicador, Indicador } from '@/types/api'

const props = withDefaults(defineProps<{ clave: ClaveIndicador; indicador: Indicador; orden?: number }>(), { orden: 0 })
defineEmits<{ abrir: [] }>()

const { diferencia, escala, mostrar } = useIndicador()
const vista = computed(() => mostrar(props.clave, props.indicador))
const e = computed(() => escala(props.indicador))
const dif = computed(() => diferencia(props.clave, props.indicador))
const estilo = computed(() => ESTILO_RIESGO[props.indicador.nivel])
const flecha = computed(() => ({ sube: ArrowUp, baja: ArrowDown, igual: Minus })[dif.value.direccion])

// Animaciones: el número sube y la barra se llena, en cascada según "orden"
const valor = useContador(toRef(() => vista.value.valor), 1100, 250 + props.orden * 90)
const valorTexto = computed(() => valor.value.toFixed(vista.value.decimales))
const montado = useMontado(250 + props.orden * 90)
</script>

<template>
  <button
    type="button"
    class="superficie group relative flex w-full flex-col overflow-hidden p-4 text-left transition duration-300 hover:-translate-y-0.5 hover:shadow-float active:scale-[0.98] sm:p-5"
    :aria-label="`${$t(`indicadores.${clave}`)}: ${vista.valor} ${vista.unidad}, ${$t(`riesgo.${indicador.nivel}`)}. ${$t('indicadores.porQueImporta')}`"
    @click="$emit('abrir')"
  >
    <div class="flex items-start justify-between gap-2">
      <span class="flex min-w-0 items-center gap-2">
        <span class="grid size-10 shrink-0 place-items-center rounded-2xl" :class="estilo.suave">
          <component :is="ICONO_INDICADOR[clave]" class="size-5" aria-hidden="true" />
        </span>
        <span class="text-sm leading-tight font-semibold">{{ $t(`indicadores.${clave}`) }}</span>
      </span>
    </div>

    <p class="mt-4 flex flex-wrap items-baseline gap-x-1.5">
      <span class="font-display text-[32px] leading-none font-bold tracking-tight tabular-nums">{{ valorTexto }}</span>
      <span class="text-xs font-medium text-stone-500 dark:text-stone-400">{{ vista.unidad }}</span>
    </p>
    <p class="mt-1 text-xs text-stone-500 dark:text-stone-400">{{ $t('indicadores.normal') }}: {{ vista.normal }} {{ vista.unidad }}</p>

    <!-- Barra comparativa: valor actual (color) vs. normal (línea) -->
    <div class="relative mt-3 h-2.5 rounded-full bg-tinta/6 dark:bg-white/8" aria-hidden="true">
      <div
        class="absolute inset-y-0 left-0 rounded-full transition-[width] duration-[1100ms] ease-out"
        :class="estilo.barra"
        :style="{ width: (montado ? e.actual : 0) + '%' }"
      />
      <div class="absolute -top-1 -bottom-1 w-0.5 rounded-full bg-tinta dark:bg-white" :style="{ left: e.normal + '%' }" />
    </div>
    <p class="mt-2 flex items-center gap-1 text-xs font-bold" :class="estilo.texto">
      <component :is="flecha" class="size-3.5 shrink-0" aria-hidden="true" />{{ dif.texto }}
    </p>

    <div class="mt-auto flex flex-wrap items-center gap-1.5 pt-3">
      <RiskBadge :nivel="indicador.nivel" />
      <NasaSourceTag :fuente="indicador.fuente" corta />
    </div>
  </button>
</template>
