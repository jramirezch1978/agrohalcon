<script setup lang="ts">
import { CalendarClock } from 'lucide-vue-next'
import { useMeses } from '@/composables/useMeses'
import { mesDesdeHoy, useAppStore } from '@/stores/app'

const store = useAppStore()
const { largo } = useMeses()
const OPCIONES = [
  { offset: 0, clave: 'campana.esteMes' },
  { offset: 1, clave: 'campana.proximo' },
  { offset: 2, clave: 'campana.en2' },
] as const
</script>

<template>
  <section class="superficie p-3 sm:p-4">
    <p id="titulo-mes-siembra" class="mb-2 flex items-center gap-1.5 px-1 text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">
      <CalendarClock class="size-3.5" aria-hidden="true" />{{ $t('campana.mesSiembra') }}
    </p>
    <div role="radiogroup" aria-labelledby="titulo-mes-siembra" class="grid grid-cols-3 gap-2">
      <button
        v-for="o in OPCIONES"
        :key="o.offset"
        type="button"
        role="radio"
        :aria-checked="store.miCultivo.mesSiembraOffset === o.offset"
        :disabled="store.cargando"
        class="flex min-h-16 flex-col items-center justify-center rounded-2xl px-2 py-2 text-center transition active:scale-[0.97] disabled:cursor-wait"
        :class="
          store.miCultivo.mesSiembraOffset === o.offset
            ? 'bg-tinta text-white dark:bg-brote-400 dark:text-tinta'
            : 'bg-arena text-tinta ring-1 ring-tinta/8 hover:bg-arena-2 dark:bg-white/5 dark:text-stone-200 dark:ring-white/10'
        "
        @click="store.miCultivo.mesSiembraOffset = o.offset"
      >
        <span class="font-display text-base leading-tight font-bold capitalize">{{ largo(mesDesdeHoy(o.offset)) }}</span>
        <span class="text-[11px] opacity-75">{{ $t(o.clave) }}</span>
      </button>
    </div>
  </section>
</template>
