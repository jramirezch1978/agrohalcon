<script setup lang="ts">
import { ChevronDown, ExternalLink, Satellite } from 'lucide-vue-next'
import type { NasaDataset } from '@/data/nasaDatasets'

defineProps<{ dataset: NasaDataset }>()
</script>

<template>
  <article class="superficie flex h-full flex-col overflow-hidden">
    <header class="relative flex items-center gap-4 overflow-hidden bg-linear-to-br p-5 text-white" :class="dataset.color">
      <component :is="dataset.icono" class="absolute -right-4 -bottom-6 size-32 text-white/10" aria-hidden="true" />
      <span class="grid size-12 shrink-0 place-items-center rounded-2xl bg-white/15 ring-1 ring-white/25 backdrop-blur">
        <component :is="dataset.icono" class="size-6" aria-hidden="true" />
      </span>
      <div class="relative min-w-0">
        <!-- Primero lo que mide, en palabras simples; el nombre del satélite va debajo -->
        <h2 class="font-display text-lg leading-snug font-bold tracking-tight">{{ $t(`datos.items.${dataset.id}.simple`) }}</h2>
        <p class="text-xs font-semibold text-white/85">{{ dataset.nombre }}</p>
      </div>
    </header>

    <div class="flex-1 space-y-3.5 p-5 text-[15px]">
      <div>
        <p class="text-xs font-bold tracking-wide text-stone-500 uppercase dark:text-stone-400">{{ $t('datos.paraQue') }}</p>
        <p class="mt-0.5 text-stone-700 dark:text-stone-300">{{ $t(`datos.items.${dataset.id}.uso`) }}</p>
      </div>

      <!-- Para el jurado y los curiosos: plegado por defecto -->
      <details class="group rounded-2xl bg-stone-50 px-4 py-3 dark:bg-white/5">
        <summary class="flex min-h-8 cursor-pointer list-none items-center justify-between text-sm font-semibold text-stone-600 dark:text-stone-300">
          {{ $t('datos.tecnico') }}
          <ChevronDown class="size-4 transition group-open:rotate-180" aria-hidden="true" />
        </summary>
        <dl class="mt-3 space-y-2.5 text-sm">
          <div>
            <dt class="text-xs font-bold tracking-wide text-stone-500 uppercase dark:text-stone-400">{{ $t('datos.mision') }}</dt>
            <dd class="mt-0.5 flex items-start gap-1.5 text-stone-800 dark:text-stone-200">
              <Satellite class="mt-0.5 size-4 shrink-0 text-nasa-700 dark:text-nasa-300" aria-hidden="true" />{{ dataset.mision }}
            </dd>
          </div>
          <div>
            <dt class="text-xs font-bold tracking-wide text-stone-500 uppercase dark:text-stone-400">{{ $t('datos.variable') }}</dt>
            <dd class="mt-0.5">{{ $t(`datos.items.${dataset.id}.variable`) }}</dd>
          </div>
          <div>
            <dt class="text-xs font-bold tracking-wide text-stone-500 uppercase dark:text-stone-400">{{ $t('datos.resolucion') }}</dt>
            <dd class="mt-0.5 font-mono">{{ dataset.resolucion }}</dd>
          </div>
        </dl>
        <a
          :href="dataset.url"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-3 flex min-h-11 items-center justify-center gap-2 rounded-xl bg-nasa-800 text-sm font-semibold text-white transition hover:bg-nasa-700 active:scale-[0.98]"
        >
          {{ $t('datos.abrir') }}<ExternalLink class="size-4" aria-hidden="true" />
          <span class="sr-only">{{ dataset.nombre }} {{ $t('datos.nuevaPestana') }}</span>
        </a>
      </details>
    </div>
  </article>
</template>
