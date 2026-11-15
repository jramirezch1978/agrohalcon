<script setup lang="ts">
import { Droplet, Droplets, Waves } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import type { AguaDisponible } from '@/types/api'

/** Restricción del agricultor: cuánta agua de riego tiene. Cambia el puntaje de agua de cada rotación. */
const store = useAppStore()
const OPCIONES: { id: AguaDisponible; icono: typeof Droplet }[] = [
  { id: 'poca', icono: Droplet },
  { id: 'normal', icono: Droplets },
  { id: 'suficiente', icono: Waves },
]
const actual = () => store.aguaDisponible ?? 'normal'
</script>

<template>
  <section class="superficie p-3 sm:p-4">
    <p id="titulo-agua" class="mb-2 flex items-center gap-1.5 px-1 text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">
      <Droplets class="size-3.5" aria-hidden="true" />{{ $t('aguaDisponible.titulo') }}
    </p>
    <div role="radiogroup" aria-labelledby="titulo-agua" class="grid grid-cols-3 gap-2">
      <button
        v-for="o in OPCIONES"
        :key="o.id"
        type="button"
        role="radio"
        :aria-checked="actual() === o.id"
        :disabled="store.cargando"
        class="flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-2xl px-2 py-2 text-center transition active:scale-[0.97] disabled:cursor-wait"
        :class="
          actual() === o.id
            ? 'bg-tinta text-white dark:bg-brote-400 dark:text-tinta'
            : 'bg-arena text-tinta ring-1 ring-tinta/8 hover:bg-arena-2 dark:bg-white/5 dark:text-stone-200 dark:ring-white/10'
        "
        @click="store.aguaDisponible = o.id"
      >
        <component :is="o.icono" class="size-5" aria-hidden="true" />
        <span class="font-display text-sm leading-tight font-bold">{{ $t(`aguaDisponible.${o.id}`) }}</span>
      </button>
    </div>
    <p class="mt-2 px-1 text-[11px] leading-snug text-stone-500 dark:text-stone-400">{{ $t('aguaDisponible.ayuda') }}</p>
  </section>
</template>
