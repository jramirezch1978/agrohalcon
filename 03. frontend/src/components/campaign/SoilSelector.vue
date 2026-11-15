<script setup lang="ts">
import { BookOpen, Layers, Loader2 } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import { api } from '@/services/api'
import { useAppStore } from '@/stores/app'
import type { Salinidad, SueloPropuesto, TipoSuelo } from '@/types/api'

/**
 * Suelo de la parcela: tipo (arenoso / franco / arcilloso) y salinidad. Los elige el agricultor.
 * Si aún no eligió el tipo, se propone el de SoilGrids (ISRIC, CC-BY 4.0): NO es dato de la NASA y se puede cambiar.
 */
const store = useAppStore()
const TIPOS: TipoSuelo[] = ['arenoso', 'franco', 'arcilloso']
const SALES: Salinidad[] = ['no', 'leve', 'alta']
const INFILTRACION: Record<TipoSuelo, 'alta' | 'media' | 'baja'> = { arenoso: 'alta', franco: 'media', arcilloso: 'baja' }

const propuesta = ref<SueloPropuesto | null>(null)
const buscando = ref(false)
const tipo = computed(() => store.parcela?.tipoSuelo)
const sal = computed(() => store.parcela?.salinidad)

watch(
  () => store.parcela && `${store.parcela.lat},${store.parcela.lon}`,
  async () => {
    propuesta.value = null
    const p = store.parcela
    if (!p || p.tipoSuelo) return
    buscando.value = true
    const r = await api.getSuelo(p.lat, p.lon)
    // la parcela pudo cambiar mientras se esperaba
    if (store.parcela && store.parcela.lat === p.lat && store.parcela.lon === p.lon) propuesta.value = r
    buscando.value = false
  },
  { immediate: true },
)

function elegirTipo(t: TipoSuelo) {
  // Tocar el elegido lo quita (vuelve a "sin dato")
  store.elegirSuelo(tipo.value === t ? { tipoSuelo: undefined, fuenteSuelo: undefined } : { tipoSuelo: t, fuenteSuelo: 'agricultor' })
}
function usarPropuesta() {
  if (propuesta.value?.tipoSuelo) store.elegirSuelo({ tipoSuelo: propuesta.value.tipoSuelo, fuenteSuelo: 'soilgrids' })
}
function elegirSal(s: Salinidad) {
  store.elegirSuelo({ salinidad: sal.value === s ? undefined : s })
}
const chip = (activo: boolean) =>
  activo
    ? 'bg-tinta text-white dark:bg-brote-400 dark:text-tinta'
    : 'bg-arena text-tinta ring-1 ring-tinta/8 hover:bg-arena-2 dark:bg-white/5 dark:text-stone-200 dark:ring-white/10'
</script>

<template>
  <section class="superficie p-3 sm:p-4">
    <p class="mb-2 flex items-center gap-1.5 px-1 text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">
      <Layers class="size-3.5" aria-hidden="true" />{{ $t('suelo.titulo') }}
    </p>

    <p id="titulo-tipo-suelo" class="px-1 text-xs font-semibold text-stone-600 dark:text-stone-300">{{ $t('suelo.tipo') }}</p>
    <div role="radiogroup" aria-labelledby="titulo-tipo-suelo" class="mt-1 grid grid-cols-3 gap-2">
      <button
        v-for="t in TIPOS"
        :key="t"
        type="button"
        role="radio"
        :aria-checked="tipo === t"
        :disabled="store.cargando"
        class="flex min-h-14 flex-col items-center justify-center rounded-2xl px-1 py-1.5 text-center transition active:scale-[0.97] disabled:cursor-wait"
        :class="chip(tipo === t)"
        @click="elegirTipo(t)"
      >
        <span class="font-display text-sm leading-tight font-bold">{{ $t(`suelo.${t}`) }}</span>
        <span class="text-[10.5px] leading-tight opacity-75">{{ $t(`suelo.ayuda_${t}`) }}</span>
      </button>
    </div>

    <!-- Origen del tipo de suelo / propuesta de SoilGrids -->
    <template v-if="tipo">
      <p class="mt-1.5 flex items-center gap-1 px-1 text-[11px] text-stone-500 dark:text-stone-400">
        <BookOpen class="size-3 shrink-0" aria-hidden="true" />{{ store.parcela?.fuenteSuelo === 'soilgrids' ? $t('suelo.fuenteSoilgrids') : $t('suelo.fuenteAgricultor') }}
      </p>
      <p class="mt-0.5 px-1 text-[11px] text-stone-600 dark:text-stone-300">{{ $t(`suelo.infiltracion_${INFILTRACION[tipo]}`) }}</p>
    </template>
    <p v-else-if="buscando" class="mt-1.5 flex items-center gap-1 px-1 text-[11px] text-stone-500 dark:text-stone-400" role="status">
      <Loader2 class="size-3 animate-spin" aria-hidden="true" />{{ $t('suelo.buscando') }}
    </p>
    <div v-else-if="propuesta?.tipoSuelo" class="mt-2 flex items-center gap-2 rounded-2xl bg-nasa-50/60 px-3 py-2 ring-1 ring-tinta/8 dark:bg-white/5 dark:ring-white/10">
      <p class="min-w-0 flex-1 text-xs leading-snug text-stone-700 dark:text-stone-200">
        {{ $t('suelo.propuesta', { tipo: $t(`suelo.${propuesta.tipoSuelo}`).toLowerCase(), arena: Math.round(propuesta.arena ?? 0), arcilla: Math.round(propuesta.arcilla ?? 0) }) }}
        <template v-if="propuesta.carbonoOrganico != null"> {{ $t('suelo.materiaOrganica', { soc: propuesta.carbonoOrganico }) }}</template>
        <span class="block text-[10.5px] text-stone-500 dark:text-stone-400">{{ $t('suelo.fuenteSoilgrids') }}</span>
      </p>
      <button type="button" class="shrink-0 rounded-full bg-tinta px-3 py-1.5 text-xs font-bold text-white dark:bg-brote-400 dark:text-tinta" @click="usarPropuesta">
        {{ $t('suelo.usar') }}
      </button>
    </div>
    <p v-else class="mt-1.5 px-1 text-[11px] text-stone-500 dark:text-stone-400">{{ $t('suelo.sinDato') }}</p>

    <p id="titulo-salinidad" class="mt-3 px-1 text-xs font-semibold text-stone-600 dark:text-stone-300">{{ $t('suelo.salinidad') }}</p>
    <div role="radiogroup" aria-labelledby="titulo-salinidad" class="mt-1 grid grid-cols-3 gap-2">
      <button
        v-for="s in SALES"
        :key="s"
        type="button"
        role="radio"
        :aria-checked="sal === s"
        :disabled="store.cargando"
        class="min-h-10 rounded-2xl px-1 py-1.5 text-center text-sm font-bold transition active:scale-[0.97] disabled:cursor-wait"
        :class="chip(sal === s)"
        @click="elegirSal(s)"
      >
        {{ $t(`suelo.sal_${s}`) }}
      </button>
    </div>
  </section>
</template>
