<script setup lang="ts">
import { ArrowRight, CloudRain, CloudSun, Droplets, Layers, Leaf, Satellite, Scale, Shuffle, Sprout, Target, Thermometer, Trophy, Waves } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * El reto de la NASA (Field Shift) y cómo lo cumple AllpaShift, en palabras simples:
 * lo que pide el reto → qué hace la app, y cómo se puntúa una rotación (clima, suelo, agua y prioridad).
 */
const { tm, rt } = useI18n()
const ICONOS = [Satellite, Layers, Leaf, Target, Shuffle, Sprout, CloudSun]
const cumple = computed(() =>
  (tm('reto.cumple') as { pide: unknown; app: unknown }[]).map((x, i) => ({ pide: rt(x.pide as never), app: rt(x.app as never), icono: ICONOS[i] ?? Leaf })),
)
const PRES_ICONOS = [Thermometer, CloudRain, Droplets, Waves, Sprout]
const presiones = computed(() =>
  (tm('reto.presiones') as { pide: unknown; app: unknown }[]).map((x, i) => ({ pide: rt(x.pide as never), app: rt(x.app as never), icono: PRES_ICONOS[i] ?? Leaf })),
)
const metas = computed(() => (tm('reto.metas') as { meta: unknown; app: unknown }[]).map((x) => ({ meta: rt(x.meta as never), app: rt(x.app as never) })))
const suelo = computed(() => (tm('reto.reglasSuelo') as { p: unknown; t: unknown }[]).map((x) => ({ p: rt(x.p as never), t: rt(x.t as never) })))
const PESOS = [
  { id: 'arriesgar_menos', clima: 60, suelo: 25, agua: 15 },
  { id: 'cuidar_suelo', clima: 35, suelo: 50, agua: 15 },
  { id: 'ahorrar_agua', clima: 35, suelo: 15, agua: 50 },
] as const
</script>

<template>
  <section class="superficie p-5 sm:p-6" :aria-label="$t('reto.titulo')">
    <p class="flex items-center gap-1.5 text-xs font-bold tracking-[0.14em] text-agro-700 uppercase dark:text-brote-400">
      <Trophy class="size-4" aria-hidden="true" />{{ $t('reto.etiqueta') }}
    </p>
    <h2 class="mt-2 font-display text-2xl font-extrabold tracking-tight text-balance">{{ $t('reto.titulo') }}</h2>
    <p class="mt-1 text-sm text-stone-500 dark:text-stone-400">{{ $t('reto.subtitulo') }}</p>

    <!-- El texto del reto, completo -->
    <blockquote class="mt-4 max-w-3xl rounded-2xl border-l-4 border-brote-400 bg-arena p-4 dark:bg-white/5">
      <p class="text-xs font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">{{ $t('reto.desafioTitulo') }}</p>
      <p class="mt-2 text-[15px] leading-relaxed">{{ $t('reto.problema') }}</p>
      <p class="mt-3 text-[15px] leading-relaxed font-semibold">{{ $t('reto.cita') }}</p>
      <span class="mt-2 block text-xs text-stone-500 dark:text-stone-400">{{ $t('reto.citaFuente') }}</span>
    </blockquote>

    <!-- Cada presión del reto → qué hace la app -->
    <h3 class="mt-6 text-sm font-bold">{{ $t('reto.presionesTitulo') }}</h3>
    <ul class="mt-3 space-y-2">
      <li v-for="(c, i) in presiones" :key="i" class="flex items-start gap-3 rounded-2xl bg-arena p-3 dark:bg-white/5">
        <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-red-500/10 text-red-700 dark:text-red-300">
          <component :is="c.icono" class="size-5" aria-hidden="true" />
        </span>
        <span class="min-w-0">
          <span class="block font-display text-[15px] font-bold">{{ c.pide }}</span>
          <span class="mt-0.5 block text-[14px] leading-snug text-stone-600 dark:text-stone-300">{{ c.app }}</span>
        </span>
      </li>
    </ul>

    <!-- Las 3 metas de las rotaciones → los 3 puntajes -->
    <h3 class="mt-6 text-sm font-bold">{{ $t('reto.metasTitulo') }}</h3>
    <ul class="mt-2 grid grid-cols-1 gap-2 md:grid-cols-3">
      <li v-for="(m, i) in metas" :key="i" class="rounded-2xl p-3 ring-1 ring-agro-600/25 dark:ring-brote-400/25">
        <span class="block font-display text-[15px] font-bold text-agro-800 dark:text-brote-300">…{{ m.meta }}</span>
        <span class="mt-1 flex items-start gap-1.5 text-[14px] leading-snug text-stone-600 dark:text-stone-300">
          <ArrowRight class="mt-0.5 size-4 shrink-0" aria-hidden="true" />{{ m.app }}
        </span>
      </li>
    </ul>

    <!-- Lo que pide el reto → cómo lo cumple AllpaShift -->
    <h3 class="mt-6 text-sm font-bold">{{ $t('reto.cumpleTitulo') }}</h3>
    <ul class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
      <li v-for="(c, i) in cumple" :key="i" class="flex items-start gap-3 rounded-2xl bg-arena p-3 dark:bg-white/5">
        <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-agro-600/12 text-agro-700 dark:bg-brote-400/12 dark:text-brote-400">
          <component :is="c.icono" class="size-5" aria-hidden="true" />
        </span>
        <span class="min-w-0">
          <span class="block text-xs font-bold tracking-[0.1em] text-stone-500 uppercase dark:text-stone-400">{{ c.pide }}</span>
          <span class="mt-0.5 block text-[15px] leading-snug">{{ c.app }}</span>
        </span>
      </li>
    </ul>

    <!-- Cómo se puntúa una rotación -->
    <h3 class="mt-7 flex items-center gap-1.5 text-sm font-bold"><Scale class="size-4" aria-hidden="true" />{{ $t('reto.puntajeTitulo') }}</h3>
    <p class="mt-1 max-w-2xl text-[15px] text-stone-600 dark:text-stone-300">{{ $t('reto.puntajeTexto') }}</p>
    <div class="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
      <div class="rounded-2xl bg-arena p-4 dark:bg-white/5">
        <p class="flex items-center gap-1.5 font-display font-bold"><CloudSun class="size-5 text-nasa-700 dark:text-nasa-300" aria-hidden="true" />{{ $t('rotaciones.clima') }}</p>
        <p class="mt-1 text-sm text-stone-600 dark:text-stone-300">{{ $t('reto.clima') }}</p>
      </div>
      <div class="rounded-2xl bg-arena p-4 dark:bg-white/5">
        <p class="flex items-center gap-1.5 font-display font-bold"><Sprout class="size-5 text-agro-700 dark:text-brote-400" aria-hidden="true" />{{ $t('rotaciones.suelo') }}</p>
        <ul class="mt-1 space-y-0.5 text-sm text-stone-600 dark:text-stone-300">
          <li v-for="(r, i) in suelo" :key="i" class="flex gap-2">
            <strong class="w-8 shrink-0 text-right tabular-nums" :class="r.p.startsWith('+') ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-700 dark:text-red-300'">{{ r.p }}</strong>{{ r.t }}
          </li>
        </ul>
      </div>
      <div class="rounded-2xl bg-arena p-4 dark:bg-white/5">
        <p class="flex items-center gap-1.5 font-display font-bold"><Droplets class="size-5 text-sky-700 dark:text-sky-300" aria-hidden="true" />{{ $t('prioridad.agua') }}</p>
        <p class="mt-1 text-sm text-stone-600 dark:text-stone-300">{{ $t('reto.agua') }}</p>
      </div>
    </div>

    <p class="mt-4 text-sm font-semibold">{{ $t('reto.pesosTitulo') }}</p>
    <div class="mt-2 overflow-x-auto">
      <table class="w-full min-w-[19rem] text-sm">
        <thead>
          <tr class="text-left text-xs text-stone-500 dark:text-stone-400">
            <th class="py-1.5 pr-2 font-semibold">{{ $t('reto.siEliges') }}</th>
            <th class="px-2 py-1.5 text-center font-semibold">{{ $t('rotaciones.clima') }}</th>
            <th class="px-2 py-1.5 text-center font-semibold">{{ $t('rotaciones.suelo') }}</th>
            <th class="px-2 py-1.5 text-center font-semibold">{{ $t('prioridad.agua') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-tinta/8 dark:divide-white/10">
          <tr v-for="p in PESOS" :key="p.id">
            <td class="py-2 pr-2 font-semibold">{{ $t(`prioridad.${p.id}`) }}</td>
            <td class="px-2 py-2 text-center tabular-nums">{{ p.clima }} %</td>
            <td class="px-2 py-2 text-center tabular-nums">{{ p.suelo }} %</td>
            <td class="px-2 py-2 text-center tabular-nums">{{ p.agua }} %</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="mt-3 text-xs text-stone-500 dark:text-stone-400">{{ $t('reto.fuentesSuelo') }}</p>
  </section>
</template>
