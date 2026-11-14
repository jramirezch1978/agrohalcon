<script setup lang="ts">
import { Moon, Sun } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { IDIOMAS } from '@/i18n'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const { t } = useI18n()
const etiquetaTema = computed(() =>
  t('ajustes.cambiarTema', { modo: t(store.tema === 'oscuro' ? 'ajustes.claro' : 'ajustes.oscuro') }),
)
</script>

<template>
  <div class="flex items-center gap-1.5">
    <div role="group" :aria-label="$t('ajustes.idioma')" class="flex rounded-full bg-tinta/5 p-1 dark:bg-white/8">
      <button
        v-for="l in IDIOMAS"
        :key="l"
        type="button"
        :aria-pressed="store.idioma === l"
        class="h-8 min-w-10 rounded-full px-2 text-xs font-bold tracking-wide uppercase transition"
        :class="
          store.idioma === l
            ? 'bg-tinta text-white shadow-sm dark:bg-brote-400 dark:text-tinta'
            : 'text-stone-500 hover:text-tinta dark:text-stone-400 dark:hover:text-white'
        "
        @click="store.idioma = l"
      >
        {{ l }}
      </button>
    </div>
    <button
      type="button"
      :aria-label="etiquetaTema"
      :title="etiquetaTema"
      class="grid size-10 place-items-center rounded-full text-stone-600 transition hover:bg-tinta/5 dark:text-stone-300 dark:hover:bg-white/8"
      @click="store.alternarTema()"
    >
      <Transition mode="out-in" enter-from-class="rotate-90 opacity-0" leave-to-class="-rotate-90 opacity-0" enter-active-class="transition duration-200" leave-active-class="transition duration-150">
        <Sun v-if="store.tema === 'oscuro'" class="size-5" aria-hidden="true" />
        <Moon v-else class="size-5" aria-hidden="true" />
      </Transition>
    </button>
  </div>
</template>
