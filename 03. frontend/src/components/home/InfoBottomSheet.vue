<script setup lang="ts">
import { ArrowRight, Satellite } from 'lucide-vue-next'
import { computed } from 'vue'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import { useIndicador } from '@/composables/useIndicador'
import { ESTILO_RIESGO, ICONO_INDICADOR } from '@/composables/useRiesgo'
import type { ClaveIndicador, Indicador } from '@/types/api'

const props = defineProps<{ clave: ClaveIndicador | null; indicador: Indicador | null }>()
defineEmits<{ cerrar: [] }>()

const { diferencia, escala } = useIndicador()

/** Resolución espacial aproximada de cada fuente */
const RESOLUCION: Record<string, string> = {
  'GPM IMERG': '~10 km (0.1°)',
  'NASA POWER': '~50 km (0.5°)',
  'MUR SST': 'Niño 1+2 (0°-10° S, 90°-80° O)',
  SMAP: '~9 km (EASE-Grid 2.0)',
  'MODIS NDVI': '250 m (compuesto de 16 días)',
}
const e = computed(() => (props.indicador ? escala(props.indicador) : { actual: 0, normal: 0 }))
</script>

<template>
  <BottomSheet :abierto="!!clave && !!indicador" :titulo="$t('indicadores.porQueImporta')" @cerrar="$emit('cerrar')">
    <template v-if="clave && indicador">
      <div class="flex items-center gap-3 pr-12">
        <span class="grid size-14 shrink-0 place-items-center rounded-2xl" :class="ESTILO_RIESGO[indicador.nivel].suave">
          <component :is="ICONO_INDICADOR[clave]" class="size-7" aria-hidden="true" />
        </span>
        <div>
          <p class="text-xs font-bold tracking-[0.14em] text-agro-600 uppercase dark:text-brote-400">{{ $t('indicadores.porQueImporta') }}</p>
          <h2 class="font-display text-2xl font-bold tracking-tight">{{ $t(`indicadores.${clave}`) }}</h2>
        </div>
      </div>

      <!-- Actual vs. normal -->
      <div class="mt-6 grid grid-cols-2 gap-3">
        <div class="rounded-2xl p-4" :class="ESTILO_RIESGO[indicador.nivel].fondo">
          <p class="text-xs font-semibold text-stone-600 dark:text-stone-300">{{ $t('indicadores.tuParcela') }}</p>
          <p class="mt-1 font-display text-3xl font-bold tabular-nums">{{ indicador.valor }}</p>
          <p class="text-xs text-stone-600 dark:text-stone-400">{{ indicador.unidad }}</p>
        </div>
        <div class="rounded-2xl bg-arena p-4 dark:bg-white/5">
          <p class="text-xs font-semibold text-stone-600 dark:text-stone-300">{{ $t('indicadores.normal') }}</p>
          <p class="mt-1 font-display text-3xl font-bold text-stone-500 tabular-nums dark:text-stone-400">{{ indicador.normal }}</p>
          <p class="text-xs text-stone-600 dark:text-stone-400">{{ indicador.unidad }}</p>
        </div>
      </div>
      <div class="mt-4 space-y-2" aria-hidden="true">
        <div class="flex items-center gap-3 text-xs font-medium">
          <span class="w-16 text-stone-500">{{ $t('indicadores.actual') }}</span>
          <div class="h-3 flex-1 rounded-full bg-tinta/6 dark:bg-white/8">
            <div class="h-full rounded-full" :class="ESTILO_RIESGO[indicador.nivel].barra" :style="{ width: e.actual + '%' }" />
          </div>
        </div>
        <div class="flex items-center gap-3 text-xs font-medium">
          <span class="w-16 text-stone-500">{{ $t('indicadores.normal') }}</span>
          <div class="h-3 flex-1 rounded-full bg-tinta/6 dark:bg-white/8">
            <div class="h-full rounded-full bg-stone-400 dark:bg-stone-500" :style="{ width: e.normal + '%' }" />
          </div>
        </div>
      </div>
      <div class="mt-4 flex flex-wrap items-center gap-2">
        <RiskBadge :nivel="indicador.nivel" con-titulo tamano="md" />
        <span class="text-sm font-semibold" :class="ESTILO_RIESGO[indicador.nivel].texto">{{ diferencia(clave, indicador).texto }}</span>
      </div>

      <!-- Aviso de calidad del dato (p. ej. lluvia satelital atrasada) -->
      <p v-if="indicador.aviso" class="mt-4 rounded-xl bg-amber-100 p-3 text-sm font-medium text-amber-900 dark:bg-amber-400/15 dark:text-amber-200">
        {{ indicador.aviso }}
      </p>

      <!-- Explicación simple -->
      <h3 class="mt-6 text-sm font-bold">{{ $t('indicadores.queSignifica') }}</h3>
      <p class="mt-1 text-[15px] leading-relaxed text-stone-700 dark:text-stone-300">{{ $t(`indicadores.explicacion.${clave}`) }}</p>
      <h3 class="mt-4 text-sm font-bold">{{ $t('indicadores.porQueImporta') }}</h3>
      <p class="mt-1 text-[15px] leading-relaxed text-stone-700 dark:text-stone-300">{{ $t(`indicadores.importa.${clave}`) }}</p>
      <p class="mt-2 text-[15px] leading-relaxed font-medium" :class="ESTILO_RIESGO[indicador.nivel].texto">{{ $t(`indicadores.consejo.${indicador.nivel}`) }}</p>
      <p class="mt-4 rounded-xl bg-arena p-3 text-xs leading-relaxed text-stone-600 dark:bg-white/5 dark:text-stone-300">
        <template v-if="clave === 'lluvia'">{{ $t('indicadores.normalHistorico') }} </template>
        <template v-if="RESOLUCION[indicador.fuente]">{{ $t('indicadores.escala', { res: RESOLUCION[indicador.fuente] }) }}</template>
      </p>

      <!-- Satélite de origen -->
      <RouterLink to="/datos" class="mt-6 flex items-center gap-3 rounded-2xl bg-nasa-800 p-4 text-white transition hover:bg-nasa-700" @click="$emit('cerrar')">
        <span class="grid size-11 place-items-center rounded-xl bg-white/12"><Satellite class="size-5" aria-hidden="true" /></span>
        <span class="flex-1">
          <span class="block text-xs text-white/75">{{ $t('indicadores.medidoPor') }}</span>
          <span class="block font-display text-lg font-bold">{{ indicador.fuente }}</span>
        </span>
        <ArrowRight class="size-5" aria-hidden="true" />
      </RouterLink>
    </template>
  </BottomSheet>
</template>
