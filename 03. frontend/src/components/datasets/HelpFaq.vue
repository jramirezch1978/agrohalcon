<script setup lang="ts">
import { ChevronDown } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/** Preguntas frecuentes, plegadas: la persona abre solo la que le interesa. */
const { tm, rt } = useI18n()
const preguntas = computed(() =>
  (tm('ayuda.faq') as { p: unknown; r: unknown }[]).map((x) => ({ p: rt(x.p as never), r: rt(x.r as never) })),
)
</script>

<template>
  <section class="superficie p-5 sm:p-6" :aria-label="$t('ayuda.faqTitulo')">
    <h2 class="font-display text-xl font-bold tracking-tight">{{ $t('ayuda.faqTitulo') }}</h2>
    <div class="mt-3 divide-y divide-tinta/8 dark:divide-white/10">
      <details v-for="(x, i) in preguntas" :key="i" class="group py-1">
        <summary class="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 text-[15px] font-semibold">
          {{ x.p }}
          <ChevronDown class="size-5 shrink-0 text-stone-500 transition group-open:rotate-180" aria-hidden="true" />
        </summary>
        <p class="pb-3 text-[15px] text-stone-600 dark:text-stone-300">{{ x.r }}</p>
      </details>
    </div>
  </section>
</template>
