<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CloudRain, CloudSun, Info, Sun, Waves } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import type { Escenario } from '@/types/api'

/**
 * "¿Y si el año viene seco o lluvioso?": escenario HIPOTÉTICO sobre la lluvia normal y el agua de riego (no es un pronóstico).
 * "¿Y si el mar sube?": anomalía HIPOTÉTICA de El Niño; las reglas son las mismas que con el dato real de MUR SST.
 */
const store = useAppStore()
const OPCIONES: { id: Escenario; icono: typeof Sun }[] = [
  { id: 'seco', icono: Sun },
  { id: 'normal', icono: CloudSun },
  { id: 'lluvioso', icono: CloudRain },
]

const perfil = computed(() => store.recomendacion?.perfil)
const sinEfecto = computed(() => store.escenario !== 'normal' && perfil.value?.escenarioSinEfecto ? perfil.value.notaEscenario : null)
const ninoReal = computed(() => store.recomendacion?.indicadores?.elNino?.valor ?? null)

// El control se mueve libre; la recomendación se recalcula solo al soltarlo (una petición, no una por paso)
const MIN = -1
const MAX = 4
const borrador = ref<number>(store.ninoHipotetico ?? Math.min(MAX, Math.max(MIN, Math.round((ninoReal.value ?? 0) * 2) / 2)))
watch(ninoReal, (v) => {
  if (store.ninoHipotetico === null && v !== null) borrador.value = Math.min(MAX, Math.max(MIN, Math.round(v * 2) / 2))
})
const fmt = (v: number) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(1)} °C`
function aplicar() {
  store.ninoHipotetico = borrador.value
}
function usarReal() {
  store.ninoHipotetico = null
  if (ninoReal.value !== null) borrador.value = Math.min(MAX, Math.max(MIN, Math.round(ninoReal.value * 2) / 2))
}
</script>

<template>
  <section class="superficie p-3 sm:p-4">
    <p id="titulo-escenario" class="px-1 text-xs font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">{{ $t('escenario.titulo') }}</p>
    <div role="radiogroup" aria-labelledby="titulo-escenario" class="mt-2 grid grid-cols-3 gap-2">
      <button
        v-for="o in OPCIONES"
        :key="o.id"
        type="button"
        role="radio"
        :aria-checked="store.escenario === o.id"
        :disabled="store.cargando"
        class="flex min-h-12 items-center justify-center gap-1.5 rounded-2xl px-2 py-1.5 text-sm font-bold transition active:scale-[0.97] disabled:cursor-wait"
        :class="
          store.escenario === o.id
            ? 'bg-tinta text-white dark:bg-brote-400 dark:text-tinta'
            : 'bg-arena text-tinta ring-1 ring-tinta/8 hover:bg-arena-2 dark:bg-white/5 dark:text-stone-200 dark:ring-white/10'
        "
        @click="store.escenario = o.id"
      >
        <component :is="o.icono" class="size-4" aria-hidden="true" />{{ $t(`escenario.${o.id}`) }}
      </button>
    </div>
    <p class="mt-2 px-1 text-xs leading-snug text-stone-500 dark:text-stone-400">
      {{ store.escenario === 'normal' ? $t('escenario.notaNormal') : $t(`escenario.nota_${store.escenario}`) }}
    </p>
    <p
      v-if="sinEfecto"
      role="status"
      class="mt-2 flex gap-1.5 rounded-xl bg-amber-50 px-2.5 py-2 text-xs leading-snug text-amber-900 dark:bg-amber-400/10 dark:text-amber-200"
    >
      <Info class="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />{{ sinEfecto }}
    </p>

    <!-- ¿Y si el mar sube? (simulador de El Niño) -->
    <div class="mt-4 border-t border-tinta/8 pt-3 dark:border-white/10">
      <div class="flex items-center justify-between gap-2 px-1">
        <label for="nino-sim" class="flex items-center gap-1.5 text-xs font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">
          <Waves class="size-3.5" aria-hidden="true" />{{ $t('escenario.marTitulo') }}
        </label>
        <span class="text-sm font-bold tabular-nums" :class="store.ninoHipotetico !== null ? 'text-amber-700 dark:text-amber-300' : 'text-tinta dark:text-stone-200'">
          {{ fmt(borrador) }}
        </span>
      </div>
      <input
        id="nino-sim"
        v-model.number="borrador"
        type="range"
        :min="MIN"
        :max="MAX"
        step="0.5"
        :disabled="store.cargando"
        :aria-valuetext="fmt(borrador)"
        class="mt-2 h-11 w-full cursor-pointer accent-amber-600 disabled:cursor-wait"
        @change="aplicar"
      />
      <div class="flex justify-between px-1 text-xs text-stone-500 tabular-nums dark:text-stone-400" aria-hidden="true">
        <span>{{ fmt(MIN) }}</span><span>+1.5 °C</span><span>+3.0 °C</span><span>{{ fmt(MAX) }}</span>
      </div>
      <p class="mt-2 px-1 text-xs leading-snug text-stone-500 dark:text-stone-400">
        <template v-if="store.ninoHipotetico !== null">{{ $t('escenario.marSimulado', { v: fmt(store.ninoHipotetico) }) }}</template>
        <template v-else-if="ninoReal !== null">{{ $t('escenario.marReal', { v: fmt(ninoReal) }) }}</template>
        <template v-else>{{ $t('escenario.marSinDato') }}</template>
      </p>
      <button
        v-if="store.ninoHipotetico !== null"
        type="button"
        class="mt-2 min-h-11 rounded-xl px-3 text-sm font-bold text-tinta underline underline-offset-4 dark:text-stone-200"
        :disabled="store.cargando"
        @click="usarReal"
      >
        {{ $t('escenario.marUsarReal') }}
      </button>
    </div>
  </section>
</template>
