<script setup lang="ts">
import { ArrowUpRight } from 'lucide-vue-next'

defineProps<{ preguntas: string[]; deshabilitado?: boolean }>()
defineEmits<{ elegir: [pregunta: string] }>()
</script>

<template>
  <ul class="flex flex-col items-end gap-2">
    <li v-for="(q, i) in preguntas" :key="q" class="stagger max-w-[90%]" :style="{ '--i': i + 1 }">
      <button
        type="button"
        :disabled="deshabilitado"
        class="flex min-h-12 items-center gap-2 rounded-2xl bg-white px-4 py-2.5 text-left text-sm font-semibold text-agro-800 shadow-card ring-1 ring-agro-600/25 transition hover:bg-agro-50 hover:ring-agro-600/50 active:scale-[0.98] disabled:opacity-50 dark:bg-noche-3 dark:text-brote-300 dark:ring-brote-400/25 dark:hover:bg-white/8"
        @click="$emit('elegir', q)"
      >
        {{ q }}
        <ArrowUpRight class="size-4 shrink-0" aria-hidden="true" />
      </button>
    </li>
  </ul>
</template>
