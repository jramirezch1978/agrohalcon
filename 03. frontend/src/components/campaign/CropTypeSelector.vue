<script setup lang="ts">
import { Sprout, Trees } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import type { CultivoPermanente, TipoCultivo } from '@/types/api'

const store = useAppStore()
const TIPOS: { id: TipoCultivo; icono: typeof Sprout }[] = [
  { id: 'temporal', icono: Sprout },
  { id: 'permanente', icono: Trees },
]
const PERMANENTES: CultivoPermanente[] = ['mango', 'limon', 'banano']
</script>

<template>
  <section class="superficie p-3 sm:p-4" :aria-label="$t('cultivo.pregunta')">
    <p class="mb-2 px-1 text-xs font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">{{ $t('cultivo.pregunta') }}</p>
    <div role="radiogroup" :aria-label="$t('cultivo.pregunta')" class="grid grid-cols-2 gap-2">
      <button
        v-for="t in TIPOS"
        :key="t.id"
        type="button"
        role="radio"
        :aria-checked="store.miCultivo.tipo === t.id"
        class="flex min-h-16 flex-col items-start gap-1.5 rounded-2xl p-3 text-left transition active:scale-[0.98] min-[400px]:flex-row min-[400px]:items-center min-[400px]:gap-2.5"
        :class="
          store.miCultivo.tipo === t.id
            ? 'bg-agro-700 text-white shadow-[0_6px_18px_-8px_rgb(25_97_58/0.7)] dark:bg-brote-400 dark:text-tinta'
            : 'bg-arena text-tinta ring-1 ring-tinta/8 hover:bg-arena-2 dark:bg-white/5 dark:text-stone-200 dark:ring-white/10'
        "
        @click="store.miCultivo.tipo = t.id"
      >
        <component :is="t.icono" class="size-6 shrink-0" aria-hidden="true" />
        <span class="min-w-0 hyphens-auto break-words">
          <span class="block text-sm leading-tight font-bold">{{ $t(`cultivo.${t.id}`) }}</span>
          <span class="mt-0.5 block text-xs leading-tight opacity-80">{{ $t(`cultivo.${t.id}Detalle`) }}</span>
        </span>
      </button>
    </div>

    <!-- Cultivo permanente: cuál -->
    <div v-if="store.miCultivo.tipo === 'permanente'" class="mt-3 flex flex-wrap items-center gap-2 px-1">
      <span class="text-sm font-medium text-stone-600 dark:text-stone-300">{{ $t('cultivo.cual') }}</span>
      <div role="radiogroup" :aria-label="$t('cultivo.cual')" class="flex flex-wrap gap-1.5">
        <button
          v-for="c in PERMANENTES"
          :key="c"
          type="button"
          role="radio"
          :aria-checked="store.miCultivo.permanente === c"
          class="min-h-10 rounded-full px-4 text-sm font-semibold transition"
          :class="
            store.miCultivo.permanente === c
              ? 'bg-tinta text-white dark:bg-brote-400 dark:text-tinta'
              : 'bg-white text-stone-700 ring-1 ring-tinta/12 hover:bg-arena dark:bg-noche-3 dark:text-stone-200 dark:ring-white/12'
          "
          @click="store.miCultivo.permanente = c"
        >
          {{ $t(`cultivo.${c}`) }}
        </button>
      </div>
    </div>
  </section>
</template>
