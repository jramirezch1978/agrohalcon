<script setup lang="ts">
import { ArrowUp, Info, RotateCcw } from 'lucide-vue-next'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppLogo from '@/components/ui/AppLogo.vue'
import { MAX_CARACTERES, useAsistenteStore } from '@/stores/asistente'
import ChatBubble from './ChatBubble.vue'
import SuggestedQuestions from './SuggestedQuestions.vue'
import TypingIndicator from './TypingIndicator.vue'

defineProps<{ compacto?: boolean }>()

const chat = useAsistenteStore()
const { t, tm, rt } = useI18n()

const texto = ref('')
const lista = ref<HTMLElement>()
const entrada = ref<HTMLTextAreaElement>()

/** Pregunta de contexto (ej. la rotación vista) + las 3 sugeridas fijas */
const sugeridas = computed(() => {
  const fijas = (tm('asistente.sugeridas') as unknown[]).map((m) => rt(m as never))
  return chat.sugerenciaContexto ? [chat.sugerenciaContexto, ...fijas] : fijas
})

const contextoPendiente = computed(() => {
  const c = chat.sugerenciaContexto
  return c && !chat.historial.some((m) => m.rol === 'usuario' && m.texto === c) ? c : null
})

async function enviar(pregunta = texto.value) {
  if (!pregunta.trim() || chat.escribiendo) return
  texto.value = ''
  ajustarAltura()
  await chat.preguntar(pregunta)
}

function teclado(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    enviar()
  }
}

/** El campo crece con el texto hasta un máximo */
function ajustarAltura() {
  nextTick(() => {
    const el = entrada.value
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 128) + 'px'
  })
}

/** Scroll automático al último mensaje */
function bajar(suave = true) {
  nextTick(() => lista.value?.scrollTo({ top: lista.value.scrollHeight, behavior: suave ? 'smooth' : 'auto' }))
}
watch(() => [chat.historial.length, chat.escribiendo], () => bajar())
onMounted(() => bajar(false))

defineExpose({ enfocar: () => entrada.value?.focus() })
</script>

<template>
  <div class="flex h-full min-h-0 flex-col">
    <!-- Encabezado -->
    <header class="flex items-center gap-3 border-b border-tinta/6 px-4 py-3 dark:border-white/8">
      <div class="relative shrink-0">
        <AppLogo :tamano="44" />
        <span class="absolute -right-0.5 -bottom-0.5 size-3.5 rounded-full bg-brote-400 ring-[3px] ring-white dark:ring-noche-2" />
      </div>
      <div class="min-w-0 flex-1">
        <h2 class="truncate font-display text-lg font-bold tracking-tight">{{ $t('asistente.titulo') }}</h2>
        <p class="truncate text-xs text-stone-500 dark:text-stone-400">{{ $t('asistente.enLinea') }}</p>
      </div>
      <button
        v-if="chat.historial.length"
        type="button"
        class="inline-flex min-h-10 items-center gap-1.5 rounded-full px-3 text-xs font-semibold text-stone-600 ring-1 ring-tinta/10 transition hover:bg-arena dark:text-stone-300 dark:ring-white/10 dark:hover:bg-white/8"
        @click="chat.limpiar()"
      >
        <RotateCcw class="size-4" aria-hidden="true" />
        <span :class="compacto && 'sr-only sm:not-sr-only'">{{ $t('asistente.nuevaConversacion') }}</span>
      </button>
      <slot name="acciones" />
    </header>

    <!-- Mensajes -->
    <div ref="lista" class="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain px-4 py-5" aria-live="polite" aria-relevant="additions">
      <ChatBubble :mensaje="{ rol: 'asistente', texto: $t('asistente.bienvenida') }" />

      <SuggestedQuestions v-if="!chat.historial.length" :preguntas="sugeridas" :deshabilitado="chat.escribiendo" @elegir="enviar" />

      <TransitionGroup name="msg">
        <ChatBubble v-for="m in chat.historial" :key="m.id" :mensaje="m" />
      </TransitionGroup>

      <Transition name="msg">
        <TypingIndicator v-if="chat.escribiendo" />
      </Transition>

      <!-- Con conversación previa: ofrecer la pregunta del contexto si aún no se hizo -->
      <SuggestedQuestions
        v-if="chat.historial.length && !chat.escribiendo && contextoPendiente"
        :preguntas="[contextoPendiente]"
        @elegir="enviar"
      />
    </div>

    <!-- Aviso fijo + caja de texto -->
    <div class="border-t border-tinta/6 px-3 pt-2 pb-3 dark:border-white/8">
      <p class="mb-2 flex items-center justify-center gap-1.5 px-2 text-center text-xs leading-tight text-stone-500 dark:text-stone-400">
        <Info class="size-3.5 shrink-0" aria-hidden="true" />{{ $t('asistente.aviso') }}
      </p>
      <form class="flex items-end gap-2 rounded-[22px] bg-arena p-1.5 pl-4 ring-1 ring-tinta/8 focus-within:ring-2 focus-within:ring-agro-600 dark:bg-white/5 dark:ring-white/10" @submit.prevent="enviar()">
        <label class="sr-only" for="pregunta-asistente">{{ $t('asistente.placeholder') }}</label>
        <textarea
          id="pregunta-asistente"
          ref="entrada"
          v-model="texto"
          rows="1"
          :maxlength="MAX_CARACTERES"
          :placeholder="$t('asistente.placeholder')"
          aria-describedby="contador-asistente"
          class="max-h-32 min-h-11 flex-1 resize-none bg-transparent py-2.5 text-[16px] leading-snug outline-none placeholder:text-stone-400"
          @input="ajustarAltura"
          @keydown="teclado"
        />
        <button
          type="submit"
          :disabled="!texto.trim() || chat.escribiendo"
          :aria-label="$t('asistente.enviar')"
          class="grid size-11 shrink-0 place-items-center rounded-full bg-agro-700 text-white transition hover:bg-agro-800 active:scale-95 disabled:bg-tinta/10 disabled:text-stone-400 dark:bg-brote-400 dark:text-tinta dark:disabled:bg-white/10"
        >
          <ArrowUp class="size-5" aria-hidden="true" />
        </button>
      </form>
      <p
        id="contador-asistente"
        class="mt-1 pr-2 text-right text-xs tabular-nums"
        :class="texto.length >= MAX_CARACTERES ? 'font-semibold text-red-600 dark:text-red-400' : 'text-stone-400'"
        :aria-label="t('asistente.contador', { n: texto.length, max: MAX_CARACTERES })"
      >
        {{ texto.length }}/{{ MAX_CARACTERES }}
      </p>
    </div>
  </div>
</template>
