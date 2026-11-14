<script setup lang="ts">
import { Satellite } from 'lucide-vue-next'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { iconoEtapa } from '@/composables/useEtapa'
import type { PlanPermanente } from '@/types/api'
import SeasonTimeline from './SeasonTimeline.vue'

defineProps<{ plan: PlanPermanente }>()

const esActual = (etapa: string, actual: string) => etapa.toLowerCase() === actual.toLowerCase()
</script>

<template>
  <div class="space-y-5">
    <!-- Cultivo y etapa actual -->
    <article class="bosque stagger relative overflow-hidden rounded-[30px] p-6 text-white shadow-float sm:p-7" style="--i: 1">
      <component :is="iconoEtapa(plan.etapaActual)" class="absolute -right-6 -bottom-8 size-44 text-white/6" aria-hidden="true" />
      <p class="text-xs font-bold tracking-[0.14em] text-brote-300 uppercase">{{ $t('cultivo.titulo') }}</p>
      <h2 class="mt-2 font-display text-[34px] leading-none font-extrabold tracking-tight">{{ plan.cultivo }}</h2>
      <p class="mt-4 inline-flex items-center gap-2 rounded-full bg-brote-400 px-3.5 py-1.5 text-sm font-bold text-tinta">
        <component :is="iconoEtapa(plan.etapaActual)" class="size-4" aria-hidden="true" />
        {{ $t('plan.etapaActual') }}: <span class="capitalize">{{ plan.etapaActual }}</span>
      </p>
    </article>

    <!-- Línea de 12 meses: etapas + riesgo -->
    <section v-if="plan.meses.length" class="superficie stagger p-5 sm:p-6" style="--i: 2">
      <SectionTitle :titulo="$t('plan.calendario')" class="mb-4" />
      <SeasonTimeline :meses="plan.meses" marcar-hoy class="pt-1" />
    </section>

    <!-- Acciones por etapa -->
    <section v-if="plan.acciones.length" class="stagger" style="--i: 3">
      <SectionTitle :titulo="$t('plan.acciones')" class="mb-3" />
      <ul class="space-y-3">
        <li
          v-for="a in plan.acciones"
          :key="a.etapa"
          class="superficie flex gap-4 p-4 sm:p-5"
          :class="esActual(a.etapa, plan.etapaActual) && '!ring-2 !ring-agro-600 dark:!ring-brote-400'"
        >
          <span
            class="grid size-12 shrink-0 place-items-center rounded-2xl"
            :class="esActual(a.etapa, plan.etapaActual) ? 'bg-agro-700 text-white dark:bg-brote-400 dark:text-tinta' : 'bg-arena text-agro-700 dark:bg-white/8 dark:text-brote-300'"
          >
            <component :is="iconoEtapa(a.etapa)" class="size-6" aria-hidden="true" />
          </span>
          <div class="min-w-0 flex-1">
            <p class="flex flex-wrap items-center gap-2 text-xs font-bold tracking-wide text-stone-500 uppercase dark:text-stone-400">
              {{ a.etapa }}
              <span v-if="esActual(a.etapa, plan.etapaActual)" class="rounded-full bg-agro-700 px-2 py-0.5 text-[10px] text-white dark:bg-brote-400 dark:text-tinta">{{ $t('plan.ahora') }}</span>
            </p>
            <p class="mt-1 font-display text-lg leading-snug font-bold tracking-tight">{{ a.accion }}</p>
            <p class="mt-1 text-sm text-stone-700 dark:text-stone-300">{{ a.motivo }}</p>
            <p class="mt-2 inline-flex items-center gap-1 rounded-full bg-nasa-50 px-2.5 py-1 text-xs font-semibold text-nasa-800 ring-1 ring-nasa-200 dark:bg-nasa-400/10 dark:text-nasa-200 dark:ring-nasa-400/20">
              <Satellite class="size-3.5" aria-hidden="true" />{{ $t('campana.fuente', { fuente: a.fuente }) }}
            </p>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>
