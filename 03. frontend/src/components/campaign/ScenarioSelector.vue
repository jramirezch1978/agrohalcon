<script setup lang="ts">
import { CloudRain, CloudSun, Sun } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import type { Escenario } from '@/types/api'

/** "¿Y si el año viene seco o lluvioso?": escenario HIPOTÉTICO sobre la lluvia normal (no es un pronóstico). */
const store = useAppStore()
const OPCIONES: { id: Escenario; icono: typeof Sun }[] = [
  { id: 'seco', icono: Sun },
  { id: 'normal', icono: CloudSun },
  { id: 'lluvioso', icono: CloudRain },
]
</script>

<template>
  <section class="superficie p-3 sm:p-4">
    <p id="titulo-escenario" class="px-1 text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">{{ $t('escenario.titulo') }}</p>
    <div role="radiogroup" aria-labelledby="titulo-escenario" class="mt-2 grid grid-cols-3 gap-2">
      <button
        v-for="o in OPCIONES"
        :key="o.id"
        type="button"
        role="radio"
        :aria-checked="store.escenario === o.id"
        :disabled="store.cargando"
        class="flex min-h-12 items-center justify-center gap-1.5 rounded-2xl px-2 py-1.5 text-sm font-bold transition active:scale-[0.97] disabled:cursor-wait"
        :class="
          store.escenario === o.id
            ? 'bg-tinta text-white dark:bg-brote-400 dark:text-tinta'
            : 'bg-arena text-tinta ring-1 ring-tinta/8 hover:bg-arena-2 dark:bg-white/5 dark:text-stone-200 dark:ring-white/10'
        "
        @click="store.escenario = o.id"
      >
        <component :is="o.icono" class="size-4" aria-hidden="true" />{{ $t(`escenario.${o.id}`) }}
      </button>
    </div>
    <p class="mt-2 px-1 text-[11px] leading-snug text-stone-500 dark:text-stone-400">
      {{ store.escenario === 'normal' ? $t('escenario.notaNormal') : $t(`escenario.nota_${store.escenario}`) }}
    </p>
  </section>
</template>
