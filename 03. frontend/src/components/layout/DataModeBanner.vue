<script setup lang="ts">
import { FlaskConical } from 'lucide-vue-next'
import { useOrigenStore } from '@/stores/origen'

/** Banner fijo mientras haya datos de ejemplo en pantalla. Nunca se oculta solo. */
const origen = useOrigenStore()
</script>

<template>
  <div
    v-if="origen.hayEjemplo"
    role="status"
    class="sticky top-0 z-[600] flex items-center justify-center gap-2 bg-amber-400 px-4 py-2 text-center text-sm font-bold text-tinta shadow-md"
  >
    <FlaskConical class="size-4 shrink-0" aria-hidden="true" />{{ $t('origen.banner') }}
  </div>
</template>
