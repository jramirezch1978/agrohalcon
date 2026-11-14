<script setup lang="ts">
import { CircleAlert, CircleCheck, TriangleAlert } from 'lucide-vue-next'
import { ESTILO_RIESGO } from '@/composables/useRiesgo'
import type { NivelRiesgo } from '@/types/api'

withDefaults(defineProps<{ nivel: NivelRiesgo; conTitulo?: boolean; tamano?: 'sm' | 'md' }>(), {
  conTitulo: false,
  tamano: 'sm',
})

// Nivel con color + ícono + texto (nunca solo color: accesible para daltonismo)
const ICONO = { bajo: CircleCheck, medio: CircleAlert, alto: TriangleAlert }
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full font-semibold whitespace-nowrap ring-1 ring-inset"
    :class="[
      ESTILO_RIESGO[nivel].fondo,
      ESTILO_RIESGO[nivel].texto,
      ESTILO_RIESGO[nivel].anillo,
      tamano === 'sm' ? 'py-1 pr-2.5 pl-2 text-xs' : 'py-1.5 pr-3 pl-2.5 text-sm',
    ]"
  >
    <component :is="ICONO[nivel]" :class="tamano === 'sm' ? 'size-3.5' : 'size-4'" aria-hidden="true" />
    <template v-if="conTitulo">{{ $t('riesgo.titulo') }}</template>
    {{ $t(`riesgo.${nivel}`) }}
  </span>
</template>
