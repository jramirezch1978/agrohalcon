<script setup lang="ts">
import { BookA, ChevronDown } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/** Glosario: los términos científicos que usa la app, explicados en palabras simples (plegados). */
const { tm, rt } = useI18n()
const terminos = computed(() => (tm('glosario.terminos') as { t: unknown; d: unknown }[]).map((x) => ({ t: rt(x.t as never), d: rt(x.d as never) })))
</script>

<template>
  <section class="superficie p-5 sm:p-6" :aria-label="$t('glosario.titulo')">
    <h2 class="flex items-center gap-2 font-display text-xl font-bold tracking-tight">
      <BookA class="size-5 text-agro-700 dark:text-brote-400" aria-hidden="true" />{{ $t('glosario.titulo') }}
    </h2>
    <p class="mt-1 text-sm text-stone-600 dark:text-stone-400">{{ $t('glosario.subtitulo') }}</p>
    <div class="mt-3 divide-y divide-tinta/8 dark:divide-white/10">
      <details v-for="(x, i) in terminos" :key="i" class="group py-1">
        <summary class="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 text-[15px] font-semibold">
          {{ x.t }}
          <ChevronDown class="size-5 shrink-0 text-stone-500 transition group-open:rotate-180" aria-hidden="true" />
        </summary>
        <p class="pb-3 text-[15px] text-stone-600 dark:text-stone-300">{{ x.d }}</p>
      </details>
    </div>
  </section>
</template>
