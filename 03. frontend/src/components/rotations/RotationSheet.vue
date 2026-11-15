<script setup lang="ts">
import { BookOpen, CalendarRange, Sparkles, Sprout } from 'lucide-vue-next'
import BaseButton from '@/components/ui/BaseButton.vue'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import NasaSourceTag from '@/components/ui/NasaSourceTag.vue'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import { ICONO_INDICADOR } from '@/composables/useRiesgo'
import { nombreRotacion, useRotacion } from '@/composables/useRotacion'
import type { Indicadores, PerfilRecomendacion, Rotacion } from '@/types/api'
import RotationReview from './RotationReview.vue'
import ScoreRing from './ScoreRing.vue'

defineProps<{ rotacion: Rotacion | null; indicadores?: Indicadores; perfil?: PerfilRecomendacion }>()
defineEmits<{ cerrar: []; preguntar: [rotacion: Rotacion] }>()

const { motivoDescuento } = useRotacion()

/** Fuente de una regla de suelo en el idioma de la app (nunca se presenta como dato NASA). */
function fuenteSuelo(f: string, t: (k: string) => string) {
  if (f === 'catálogo de cultivos') return t('rotaciones.fuenteCatalogo')
  if (f === 'dato del agricultor') return t('rotaciones.fuenteAgricultor')
  return f
}
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

      <!-- Puntaje final = mezcla de clima, suelo y agua según la prioridad del agricultor -->
      <div v-if="perfil && rotacion.saludSuelo != null" class="mt-5 rounded-2xl bg-arena p-3 dark:bg-white/5">
        <p class="text-sm font-bold">{{ $t('prioridad.final') }}: {{ rotacion.puntaje }} {{ $t('rotaciones.de100') }}</p>
        <p class="mt-1 text-xs text-stone-600 dark:text-stone-300">
          {{ $t('prioridad.formula', { prioridad: $t(`prioridad.${perfil.prioridad}`).toLowerCase(), pc: Math.round(perfil.pesos.clima * 100), ps: Math.round(perfil.pesos.suelo * 100), pa: Math.round(perfil.pesos.agua * 100) }) }}
        </p>
        <p class="mt-1 text-xs font-semibold text-tinta tabular-nums dark:text-white">
          {{ $t('rotaciones.clima') }} {{ rotacion.riesgoClimatico }} · {{ $t('rotaciones.suelo') }} {{ rotacion.saludSuelo }} · {{ $t('prioridad.agua') }} {{ rotacion.puntajeAgua }}
        </p>
        <p v-if="rotacion.motivoRecomendada" class="mt-2 text-sm leading-snug text-agro-800 dark:text-brote-300">{{ rotacion.motivoRecomendada }}</p>
      </div>

      <p class="mt-5 text-[15px] leading-relaxed text-stone-700 dark:text-stone-300">{{ rotacion.explicacion }}</p>

      <template v-if="rotacion.descuentos?.length">
        <h3 class="mt-6 text-sm font-bold">
          <template v-if="rotacion.saludSuelo != null">{{ $t('rotaciones.climaTitulo') }} · {{ $t('rotaciones.puntajeClima', { p: rotacion.riesgoClimatico ?? rotacion.puntaje }) }}<br /></template>
          <span :class="rotacion.saludSuelo != null && 'font-normal text-stone-600 dark:text-stone-300'">{{ $t('rotaciones.restaron') }}</span>
        </h3>
        <p class="mt-1 text-xs text-stone-500 dark:text-stone-400">
          {{ $t('rotaciones.formula') }}:
          <strong class="font-semibold text-tinta tabular-nums dark:text-white">100 {{ rotacion.descuentos.map((d) => (d.puntos < 0 ? '− ' + Math.abs(d.puntos) : '+ ' + d.puntos)).join(' ') }} = {{ rotacion.riesgoClimatico ?? rotacion.puntaje }}</strong>
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

      <!-- Salud del suelo: reglas del catálogo de cultivos (y datos del agricultor) -->
      <template v-if="rotacion.saludSuelo != null">
        <h3 class="mt-6 flex items-center gap-1.5 text-sm font-bold">
          <Sprout class="size-4 text-agro-700 dark:text-brote-400" aria-hidden="true" />{{ $t('rotaciones.sueloTitulo') }} · {{ $t('rotaciones.puntajeSuelo', { p: rotacion.saludSuelo }) }}
        </h3>
        <p class="mt-1 text-xs text-stone-500 dark:text-stone-400">{{ $t('rotaciones.sueloSubtitulo') }}</p>
        <ul v-if="rotacion.descuentosSuelo?.length" class="mt-3 space-y-2">
          <li v-for="d in rotacion.descuentosSuelo" :key="d.regla" class="flex items-start gap-3 rounded-2xl bg-arena p-3 dark:bg-white/5">
            <strong
              class="font-display w-10 shrink-0 text-center text-lg font-bold tabular-nums"
              :class="d.puntos < 0 ? 'text-red-700 dark:text-red-300' : 'text-emerald-700 dark:text-emerald-300'"
            >{{ d.puntos > 0 ? '+' + d.puntos : d.puntos }}</strong>
            <span class="min-w-0 flex-1">
              <span class="block text-[15px] leading-snug">{{ d.explicacion }}</span>
              <span class="mt-1 inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-stone-600 ring-1 ring-tinta/10 dark:bg-white/10 dark:text-stone-300 dark:ring-white/10">
                <BookOpen class="size-3.5" aria-hidden="true" />{{ $t('inicio.fuente', { fuente: fuenteSuelo(d.fuente, $t) }) }}
              </span>
            </span>
          </li>
        </ul>
      </template>

      <RotationReview :rotacion="rotacion" :indicadores="indicadores" :perfil="perfil" />

      <BaseButton class="mt-6" bloque variante="acento" :icono="Sparkles" @click="$emit('preguntar', rotacion)">
        {{ $t('asistente.abrir') }}
      </BaseButton>
    </template>
  </BottomSheet>
</template>
