<script setup lang="ts">
import { CheckCircle2, Info, PlayCircle } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppLogo from '@/components/ui/AppLogo.vue'

/** "¿Qué es AgroShift?": qué es, para quién, qué te da y qué NO hace. */
const { tm, rt } = useI18n()
const teDa = computed(() => (tm('ayuda.teDa') as unknown[]).map((x) => rt(x as never)))
</script>

<template>
  <section class="bosque relative overflow-hidden rounded-[28px] p-6 text-white shadow-float sm:p-7" :aria-label="$t('ayuda.queEsTitulo')">
    <div class="flex items-center gap-3">
      <AppLogo :tamano="44" />
      <h2 class="font-display text-2xl font-extrabold tracking-tight">{{ $t('ayuda.queEsTitulo') }}</h2>
    </div>
    <p class="mt-4 max-w-2xl text-[17px] leading-relaxed font-medium">{{ $t('ayuda.queEs') }}</p>
    <p class="mt-2 max-w-2xl text-[15px] text-white/75">{{ $t('ayuda.paraQuien') }}</p>

    <h3 class="mt-5 text-xs font-bold tracking-[0.14em] text-brote-400 uppercase">{{ $t('ayuda.teDaTitulo') }}</h3>
    <ul class="mt-2 space-y-2">
      <li v-for="(t, i) in teDa" :key="i" class="flex items-start gap-2.5 text-[15px]">
        <CheckCircle2 class="mt-0.5 size-5 shrink-0 text-brote-400" aria-hidden="true" />{{ t }}
      </li>
    </ul>

    <p class="mt-5 flex max-w-2xl items-start gap-2 rounded-2xl bg-white/8 p-4 text-sm text-white/85 ring-1 ring-white/10">
      <Info class="mt-0.5 size-4 shrink-0" aria-hidden="true" />{{ $t('ayuda.noHace') }}
    </p>

    <RouterLink
      to="/bienvenida"
      class="mt-5 inline-flex min-h-12 items-center gap-2 rounded-2xl bg-brote-400 px-5 text-[15px] font-semibold text-tinta transition hover:brightness-105 active:scale-[0.98]"
    >
      <PlayCircle class="size-5" aria-hidden="true" />{{ $t('ayuda.verBienvenida') }}
    </RouterLink>
  </section>
</template>
