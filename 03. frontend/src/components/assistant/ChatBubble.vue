<script setup lang="ts">
import { Info } from 'lucide-vue-next'
import AppLogo from '@/components/ui/AppLogo.vue'
import NasaSourceTag from '@/components/ui/NasaSourceTag.vue'
import type { MensajeChat } from '@/stores/asistente'

defineProps<{ mensaje: Pick<MensajeChat, 'rol' | 'texto' | 'fuentes' | 'respaldo'> }>()
</script>

<template>
  <div class="flex items-end gap-2" :class="mensaje.rol === 'usuario' && 'justify-end'">
    <AppLogo v-if="mensaje.rol === 'asistente'" :tamano="30" class="mb-0.5 shrink-0" />
    <div
      class="max-w-[85%] px-4 py-3 text-[15px] leading-relaxed"
      :class="
        mensaje.rol === 'usuario'
          ? 'rounded-[22px] rounded-br-md bg-agro-700 text-white dark:bg-agro-600'
          : 'rounded-[22px] rounded-bl-md bg-white shadow-card ring-1 ring-tinta/5 dark:bg-noche-3 dark:ring-white/8'
      "
    >
      <span class="sr-only">{{ mensaje.rol === 'usuario' ? $t('asistente.tu') : 'AllpaShift' }}:</span>
      <p
        v-if="mensaje.respaldo"
        class="mb-2 inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-900 dark:bg-amber-400/15 dark:text-amber-200"
      >
        <Info class="size-3.5" aria-hidden="true" />{{ $t('asistente.respaldo') }}
      </p>
      <p class="whitespace-pre-line">{{ mensaje.texto || $t('estados.error') }}</p>
      <div v-if="mensaje.fuentes?.length" class="mt-3 flex flex-wrap items-center gap-1.5 border-t border-tinta/6 pt-3 dark:border-white/8">
        <span class="text-xs font-bold tracking-wide text-stone-500 uppercase dark:text-stone-400">{{ $t('asistente.fuentes') }}</span>
        <NasaSourceTag v-for="f in mensaje.fuentes" :key="f" :fuente="f" corta />
      </div>
    </div>
  </div>
</template>
