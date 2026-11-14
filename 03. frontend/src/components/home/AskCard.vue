<script setup lang="ts">
import { ArrowUpRight, Sparkles } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAsistenteStore } from '@/stores/asistente'

const { tm, rt } = useI18n()
const chat = useAsistenteStore()

/** Abre el panel del asistente y envía la pregunta elegida */
function preguntar(q: string) {
  chat.abrirPanel()
  chat.preguntar(q)
}

const sugeridas = computed(() => (tm('asistente.sugeridas') as unknown[]).map((m) => rt(m as never)))
</script>

<template>
  <section class="superficie overflow-hidden p-5">
    <div class="flex items-center gap-3">
      <span class="grid size-11 place-items-center rounded-2xl bg-nasa-800 text-brote-300">
        <Sparkles class="size-5" aria-hidden="true" />
      </span>
      <div class="min-w-0 flex-1">
        <h2 class="font-display text-lg font-bold tracking-tight">{{ $t('inicio.preguntaTitulo') }}</h2>
        <p class="text-sm text-stone-500 dark:text-stone-400">{{ $t('inicio.preguntaTexto') }}</p>
      </div>
    </div>
    <ul class="mt-4 space-y-2">
      <li v-for="q in sugeridas" :key="q">
        <button
          type="button"
          :disabled="chat.escribiendo"
          class="flex min-h-12 w-full items-center justify-between gap-3 rounded-2xl bg-arena px-4 py-3 text-left text-sm font-medium transition hover:bg-arena-2 disabled:opacity-60 dark:bg-white/5 dark:hover:bg-white/10"
          @click="preguntar(q)"
        >
          {{ q }}
          <ArrowUpRight class="size-4 shrink-0 text-agro-600 dark:text-brote-400" aria-hidden="true" />
        </button>
      </li>
    </ul>
  </section>
</template>
