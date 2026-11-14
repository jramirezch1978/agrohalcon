<script setup lang="ts">
import { CalendarRange, Sparkles } from 'lucide-vue-next'
import BaseButton from '@/components/ui/BaseButton.vue'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import NasaSourceTag from '@/components/ui/NasaSourceTag.vue'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import { ICONO_INDICADOR } from '@/composables/useRiesgo'
import { nombreRotacion, useRotacion } from '@/composables/useRotacion'
import type { Indicadores, Rotacion } from '@/types/api'
import ScoreRing from './ScoreRing.vue'

defineProps<{ rotacion: Rotacion | null; indicadores?: Indicadores }>()
defineEmits<{ cerrar: []; preguntar: [rotacion: Rotacion] }>()

const { motivoDescuento } = useRotacion()
</script>

<template>
  <BottomSheet :abierto="!!rotacion" :titulo="$t('rotaciones.porQuePuntaje')" @cerrar="$emit('cerrar')">
    <template v-if="rotacion">
      <p class="pr-12 text-xs font-bold tracking-[0.14em] text-agro-600 uppercase dark:text-brote-400">{{ $t('rotaciones.porQuePuntaje') }}</p>
      <div class="mt-3 flex items-center gap-4">
        <ScoreRing :puntaje="rotacion.puntaje" :nivel="rotacion.riesgo" :tamano="92" />
        <div class="min-w-0">
          <h2 class="font-display text-2xl leading-tight font-bold tracking-tight">{{ nombreRotacion(rotacion.nombre) }}</h2>
          <RiskBadge class="mt-2" :nivel="rotacion.riesgo" con-titulo tamano="md" />
        </div>
      </div>

      <p class="mt-5 text-[15px] leading-relaxed text-stone-700 dark:text-stone-300">{{ rotacion.explicacion }}</p>

      <template v-if="rotacion.descuentos?.length">
        <h3 class="mt-6 text-sm font-bold">{{ $t('rotaciones.restaron') }}</h3>
        <p class="mt-1 text-xs text-stone-500 dark:text-stone-400">
          {{ $t('rotaciones.formula') }}:
          <strong class="font-semibold text-tinta tabular-nums dark:text-white">100 {{ rotacion.descuentos.map((d) => (d.puntos < 0 ? '− ' + Math.abs(d.puntos) : '+ ' + d.puntos)).join(' ') }} = {{ rotacion.puntaje }}</strong>
        </p>
        <ul class="mt-3 space-y-2">
          <li v-for="d in rotacion.descuentos" :key="d.indicador" class="flex items-center gap-3 rounded-2xl bg-arena p-3 dark:bg-white/5">
            <span
              class="grid size-10 shrink-0 place-items-center rounded-xl"
              :class="d.puntos < 0 ? 'bg-red-500/12 text-red-700 dark:text-red-300' : 'bg-emerald-500/12 text-emerald-700 dark:text-emerald-300'"
            >
              <component :is="d.indicador === 'campana' ? CalendarRange : ICONO_INDICADOR[d.indicador]" class="size-5" aria-hidden="true" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block text-[15px]">
                <strong class="font-display text-lg font-bold tabular-nums" :class="d.puntos < 0 ? 'text-red-700 dark:text-red-300' : 'text-emerald-700 dark:text-emerald-300'">{{ d.puntos > 0 ? '+' + d.puntos : d.puntos }}</strong>
                {{ motivoDescuento(d, indicadores) }}
              </span>
              <NasaSourceTag class="mt-1" :fuente="d.fuente" />
            </span>
          </li>
        </ul>
      </template>

      <BaseButton class="mt-6" bloque variante="acento" :icono="Sparkles" @click="$emit('preguntar', rotacion)">
        {{ $t('asistente.abrir') }}
      </BaseButton>
    </template>
  </BottomSheet>
</template>
