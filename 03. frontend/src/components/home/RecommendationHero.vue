<script setup lang="ts">
import { CalendarClock, CircleAlert, CircleCheck, Droplets, Hourglass, Send, ShieldCheck, Shovel, Sprout, TriangleAlert } from 'lucide-vue-next'
import { useMeses } from '@/composables/useMeses'
import BaseButton from '@/components/ui/BaseButton.vue'
import NasaSourceTag from '@/components/ui/NasaSourceTag.vue'
import { ESTILO_RIESGO } from '@/composables/useRiesgo'
import type { NivelRiesgo, QueHacer, TipoAccion } from '@/types/api'
import OrbitArt from './OrbitArt.vue'

/** mesSiembra: solo en modo temporal, para mostrar la siembra planeada */
defineProps<{ queHacer: QueHacer; nivel: NivelRiesgo; mesSiembra?: string }>()
const { largo } = useMeses()
defineEmits<{ compartir: [] }>()

const ICONO = { bajo: CircleCheck, medio: CircleAlert, alto: TriangleAlert }

/** Tipo de acción de la quincena: ícono + clave i18n (campo opcional queHacer.tipo) */
const ACCION: Record<TipoAccion, { icono: typeof Sprout; clave: string }> = {
  sembrar: { icono: Sprout, clave: 'accion.sembrar' },
  esperar: { icono: Hourglass, clave: 'accion.esperar' },
  regar: { icono: Droplets, clave: 'accion.regar' },
  proteger: { icono: ShieldCheck, clave: 'accion.proteger' },
  'preparar drenaje': { icono: Shovel, clave: 'accion.drenaje' },
}
</script>

<template>
  <article :aria-label="$t('inicio.accionRecomendada')" class="bosque relative isolate overflow-hidden rounded-[30px] p-6 text-white shadow-float sm:p-8">
    <OrbitArt />
    <div class="relative">
      <div class="flex flex-wrap items-center gap-2">
        <span class="rounded-full bg-brote-400 px-3 py-1 text-xs font-bold tracking-wide text-tinta uppercase">
          {{ $t('inicio.accionRecomendada') }}
        </span>
        <span class="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold ring-1 ring-white/15 backdrop-blur-sm">
          <component :is="ICONO[nivel]" class="size-3.5" :style="{ color: ESTILO_RIESGO[nivel].hex }" aria-hidden="true" />
          {{ $t('riesgo.general') }}: {{ $t(`riesgo.${nivel}`) }}
        </span>
      </div>

      <!-- Tipo de acción -->
      <p v-if="queHacer.tipo && ACCION[queHacer.tipo]" class="mt-5 inline-flex items-center gap-2.5">
        <span class="grid size-11 place-items-center rounded-2xl bg-white text-tinta shadow-glow">
          <component :is="ACCION[queHacer.tipo].icono" class="size-6" aria-hidden="true" />
        </span>
        <span class="font-display text-xl font-extrabold tracking-tight text-brote-300 uppercase">{{ $t(ACCION[queHacer.tipo].clave) }}</span>
      </p>

      <p class="mt-4 max-w-[20ch] pr-4 font-display text-[28px] leading-[1.1] font-bold tracking-tight text-balance sm:max-w-[26ch] sm:text-[38px]">
        {{ queHacer.accion }}
      </p>

      <div class="mt-5 flex max-w-xl gap-3 rounded-2xl bg-white/8 p-4 ring-1 ring-white/10 backdrop-blur-sm">
        <span class="mt-0.5 h-auto w-1 shrink-0 rounded-full bg-brote-400" aria-hidden="true" />
        <p class="text-[15px] leading-relaxed text-white/85">
          <span class="font-semibold text-white">{{ $t('inicio.motivo') }}:</span> {{ queHacer.motivo }}
        </p>
      </div>

      <div class="mt-4 flex flex-wrap items-center gap-2">
        <NasaSourceTag :fuente="queHacer.fuente" sobre-oscuro />
        <RouterLink
          v-if="mesSiembra"
          to="/campana"
          class="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold ring-1 ring-white/15 transition hover:bg-white/20"
        >
          <CalendarClock class="size-3.5" aria-hidden="true" />{{ $t('campana.siembraPlaneada') }}: {{ largo(mesSiembra) }}
          <span class="text-brote-300 underline underline-offset-2">{{ $t('acciones.cambiarMes') }}</span>
        </RouterLink>
      </div>

      <div class="mt-6">
        <BaseButton class="w-full sm:w-auto" variante="whatsapp" :icono="Send" @click="$emit('compartir')">
          {{ $t('acciones.compartirWhatsapp') }}
        </BaseButton>
      </div>
    </div>
  </article>
</template>
