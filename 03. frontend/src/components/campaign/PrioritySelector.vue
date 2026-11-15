<script setup lang="ts">
import { Droplets, ShieldCheck, Sprout, Target } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import type { Prioridad } from '@/types/api'

/** "¿Qué es más importante para ti?": cambia los pesos del puntaje final y la rotación recomendada. */
const store = useAppStore()
const OPCIONES: { id: Prioridad; icono: typeof Droplets }[] = [
  { id: 'arriesgar_menos', icono: ShieldCheck },
  { id: 'ahorrar_agua', icono: Droplets },
  { id: 'cuidar_suelo', icono: Sprout },
]
/** Sin elección guardada se muestra marcada la del servidor por defecto (arriesgar menos) */
const actual = () => store.prioridad ?? 'arriesgar_menos'
</script>

<template>
  <section class="superficie p-3 sm:p-4">
    <p id="titulo-prioridad" class="mb-2 flex items-center gap-1.5 px-1 text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">
      <Target class="size-3.5" aria-hidden="true" />{{ $t('prioridad.titulo') }}
    </p>
    <div role="radiogroup" aria-labelledby="titulo-prioridad" class="grid grid-cols-3 gap-2">
      <button
        v-for="o in OPCIONES"
        :key="o.id"
        type="button"
        role="radio"
        :aria-checked="actual() === o.id"
        :disabled="store.cargando"
        class="flex min-h-18 flex-col items-center justify-center gap-0.5 rounded-2xl px-2 py-2 text-center transition active:scale-[0.97] disabled:cursor-wait"
        :class="
          actual() === o.id
            ? 'bg-tinta text-white dark:bg-brote-400 dark:text-tinta'
            : 'bg-arena text-tinta ring-1 ring-tinta/8 hover:bg-arena-2 dark:bg-white/5 dark:text-stone-200 dark:ring-white/10'
        "
        @click="store.prioridad = o.id"
      >
        <component :is="o.icono" class="size-5" aria-hidden="true" />
        <span class="font-display text-sm leading-tight font-bold">{{ $t(`prioridad.${o.id}`) }}</span>
        <span class="text-[11px] leading-tight opacity-75">{{ $t(`prioridad.ayuda_${o.id}`) }}</span>
      </button>
    </div>
  </section>
</template>
