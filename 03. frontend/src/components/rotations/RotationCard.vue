<script setup lang="ts">
import { Award, ChevronRight, CloudSun, Droplet, Sprout } from 'lucide-vue-next'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import { nombreRotacion } from '@/composables/useRotacion'
import type { NivelRiesgo, Rotacion } from '@/types/api'
import SeasonTimeline from '@/components/campaign/SeasonTimeline.vue'
import ScoreRing from './ScoreRing.vue'

withDefaults(defineProps<{ rotacion: Rotacion; recomendada?: boolean; orden?: number }>(), { recomendada: false, orden: 0 })
defineEmits<{ abrir: [] }>()

const GOTAS: Record<NivelRiesgo, number> = { bajo: 1, medio: 2, alto: 3 }
</script>

<template>
  <article
    class="relative flex w-full flex-col rounded-[28px] p-5 transition duration-300 sm:p-6"
    :class="recomendada ? 'bosque text-white shadow-float ring-[3px] ring-brote-400' : 'superficie hover:shadow-float'"
  >
  <!-- Parte superior: abre "¿Por qué este puntaje?" -->
  <button
    type="button"
    class="group -m-2 flex flex-col rounded-[22px] p-2 text-left transition active:scale-[0.985]"
    :aria-label="`${nombreRotacion(rotacion.nombre)}: ${rotacion.puntaje}/100, ${$t('riesgo.titulo')} ${$t(`riesgo.${rotacion.riesgo}`)}. ${$t('rotaciones.porQuePuntaje')}`"
    @click="$emit('abrir')"
  >
    <span
      v-if="recomendada"
      class="absolute -top-3.5 left-5 inline-flex items-center gap-1.5 rounded-full bg-brote-400 px-3 py-1.5 text-xs font-bold tracking-wide text-tinta uppercase shadow-glow"
    >
      <Award class="size-4" aria-hidden="true" />{{ $t('rotaciones.recomendada') }}
    </span>

    <div class="flex items-center gap-4 md:flex-col md:items-stretch">
      <ScoreRing class="md:mx-auto" :puntaje="rotacion.puntaje" :nivel="rotacion.riesgo" :tamano="104" :retraso="orden * 120" :sobre-oscuro="recomendada" />
      <div class="min-w-0 flex-1 md:text-center">
        <h2 class="font-display text-xl leading-tight font-bold tracking-tight sm:text-2xl">{{ nombreRotacion(rotacion.nombre) }}</h2>
        <div class="mt-2 flex flex-wrap items-center gap-2 md:justify-center">
          <RiskBadge :nivel="rotacion.riesgo" con-titulo />
          <span
            v-if="rotacion.usoAgua"
            class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold"
            :class="recomendada ? 'bg-white/10 text-white ring-1 ring-white/15' : 'bg-nasa-50 text-nasa-800 ring-1 ring-nasa-200 dark:bg-nasa-400/10 dark:text-nasa-200 dark:ring-nasa-400/20'"
          >
            <span class="flex" aria-hidden="true">
              <Droplet
                v-for="n in 3"
                :key="n"
                class="-mx-px size-3.5"
                :class="n <= GOTAS[rotacion.usoAgua] ? 'fill-current' : 'opacity-35'"
              />
            </span>
            {{ $t('rotaciones.usoAgua') }}: {{ $t(`riesgo.${rotacion.usoAgua}`).toLowerCase() }}
          </span>
        </div>
        <!-- Los dos puntajes que forman el puntaje final -->
        <div v-if="rotacion.saludSuelo != null" class="mt-2 flex flex-wrap gap-2 md:justify-center">
          <span
            v-for="p in [
              { icono: CloudSun, etiqueta: $t('rotaciones.clima'), valor: rotacion.riesgoClimatico ?? rotacion.puntaje, titulo: $t('rotaciones.puntajeClima', { p: rotacion.riesgoClimatico ?? rotacion.puntaje }) },
              { icono: Sprout, etiqueta: $t('rotaciones.suelo'), valor: rotacion.saludSuelo, titulo: $t('rotaciones.puntajeSuelo', { p: rotacion.saludSuelo }) },
            ]"
            :key="p.etiqueta"
            :title="p.titulo"
            class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold tabular-nums"
            :class="recomendada ? 'bg-white/10 text-white ring-1 ring-white/15' : 'bg-arena text-stone-700 ring-1 ring-tinta/10 dark:bg-white/5 dark:text-stone-200 dark:ring-white/10'"
          >
            <component :is="p.icono" class="size-3.5" aria-hidden="true" />{{ p.etiqueta }} {{ p.valor }}
          </span>
        </div>
      </div>
    </div>

    <p class="mt-4 line-clamp-2 text-[15px] leading-relaxed" :class="recomendada ? 'text-white/85' : 'text-stone-700 dark:text-stone-300'">
      {{ rotacion.explicacion }}
    </p>
    <p v-if="recomendada && rotacion.motivoRecomendada" class="mt-2 rounded-2xl bg-white/10 px-3 py-2 text-sm leading-snug font-semibold text-brote-200 ring-1 ring-white/12">
      {{ rotacion.motivoRecomendada }}
    </p>
    <span class="mt-3 inline-flex items-center gap-1 text-sm font-semibold" :class="recomendada ? 'text-brote-300' : 'text-agro-700 dark:text-brote-400'">
      {{ $t('rotaciones.porQuePuntaje') }}<ChevronRight class="size-4 transition group-hover:translate-x-0.5" aria-hidden="true" />
    </span>
  </button>

  <!-- Perspectiva de la campaña: riesgo mes a mes (opcional en la API) -->
  <div v-if="rotacion.ciclo?.meses.length" class="mt-4 border-t pt-4" :class="recomendada ? 'border-white/12' : 'border-tinta/8 dark:border-white/8'">
    <p class="mb-2 text-[11px] font-bold tracking-[0.12em] uppercase" :class="recomendada ? 'text-brote-300' : 'text-agro-700 dark:text-brote-400'">{{ $t('campana.titulo') }}</p>
    <SeasonTimeline
      :meses="rotacion.ciclo.meses"
      :siembra="rotacion.ciclo.siembra"
      :cosecha="rotacion.ciclo.cosecha"
      :duracion-meses="rotacion.ciclo.duracionMeses"
      :mes-mas-riesgoso="rotacion.ciclo.mesMasRiesgoso"
      :sobre-oscuro="recomendada"
    />
  </div>
  </article>
</template>
