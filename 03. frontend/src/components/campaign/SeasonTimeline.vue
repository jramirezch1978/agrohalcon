<script setup lang="ts">
import { Flag, Satellite, TriangleAlert } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { iconoEtapa, mayusculaInicial } from '@/composables/useEtapa'
import { useMeses } from '@/composables/useMeses'
import type { MesISO, MesRiesgo, NivelRiesgo } from '@/types/api'

type Mes = MesRiesgo & { etapa?: string }

const props = withDefaults(
  defineProps<{
    meses: Mes[]
    siembra?: MesISO
    cosecha?: MesISO
    duracionMeses?: number
    mesMasRiesgoso?: MesISO
    /** Sobre fondo oscuro (tarjeta recomendada) */
    sobreOscuro?: boolean
    /** Marca el mes actual (plan de cultivo permanente) */
    marcarHoy?: boolean
  }>(),
  { sobreOscuro: false, marcarHoy: false },
)

const { t } = useI18n()
const { largo, conAnio, inicial, hoy } = useMeses()
const seleccionado = ref<MesISO | null>(null)
const detalle = computed(() => props.meses.find((m) => m.mes === seleccionado.value) ?? null)

// Colores de celda con contraste AA para el texto
const CELDA: Record<NivelRiesgo, string> = {
  bajo: 'bg-emerald-700 text-white',
  medio: 'bg-amber-400 text-tinta',
  alto: 'bg-red-600 text-white',
}

/** Peor mes: el que manda la API o el primero con mayor riesgo */
const peor = computed<MesISO | undefined>(() => {
  if (props.mesMasRiesgoso) return props.mesMasRiesgoso
  const orden = { bajo: 0, medio: 1, alto: 2 }
  const m = props.meses.reduce<Mes | undefined>((a, b) => (!a || orden[b.riesgo] > orden[a.riesgo] ? b : a), undefined)
  return m && m.riesgo !== 'bajo' ? m.mes : undefined
})
const mesPeor = computed(() => props.meses.find((m) => m.mes === peor.value))

/** Banda de etapas: agrupa meses seguidos con la misma etapa */
const etapas = computed(() => {
  if (!props.meses.some((m) => m.etapa)) return []
  const grupos: { etapa: string; n: number }[] = []
  for (const m of props.meses) {
    const ultimo = grupos.at(-1)
    if (ultimo && ultimo.etapa === m.etapa) ultimo.n++
    else grupos.push({ etapa: m.etapa ?? '', n: 1 })
  }
  return grupos
})

function alternar(mes: MesISO) {
  seleccionado.value = seleccionado.value === mes ? null : mes
}
const etiquetaCelda = (m: Mes) =>
  `${conAnio(m.mes)}${m.etapa ? ` (${m.etapa})` : ''}: ${t('campana.riesgo', { nivel: t(`riesgo.${m.riesgo}`).toLowerCase() })}. ${m.motivo}`
</script>

<template>
  <div>
    <!-- Siembra · Cosecha · Duración -->
    <p
      v-if="siembra && cosecha"
      class="mb-2 flex flex-wrap gap-x-2 gap-y-0.5 text-xs"
      :class="sobreOscuro ? 'text-white/80' : 'text-stone-600 dark:text-stone-400'"
    >
      <span><strong class="font-semibold" :class="sobreOscuro ? 'text-white' : 'text-tinta dark:text-white'">{{ $t('campana.siembra') }}:</strong> {{ largo(siembra) }}</span>
      <span aria-hidden="true">·</span>
      <span><strong class="font-semibold" :class="sobreOscuro ? 'text-white' : 'text-tinta dark:text-white'">{{ $t('campana.cosecha') }}:</strong> {{ largo(cosecha) }}</span>
      <template v-if="duracionMeses">
        <span aria-hidden="true">·</span>
        <span><strong class="font-semibold" :class="sobreOscuro ? 'text-white' : 'text-tinta dark:text-white'">{{ $t('campana.duracion') }}:</strong> {{ $t('campana.meses', { n: duracionMeses }) }}</span>
      </template>
    </p>

    <!-- Banda de etapas (cultivo permanente) -->
    <div v-if="etapas.length" class="mb-1 flex gap-1" aria-hidden="true">
      <span
        v-for="(e, i) in etapas"
        :key="i"
        class="flex min-w-0 items-center justify-center gap-1 rounded-md px-1 py-1 text-[10px] font-bold tracking-wide uppercase"
        :class="sobreOscuro ? 'bg-white/10 text-white/85' : 'bg-tinta/6 text-stone-600 dark:bg-white/8 dark:text-stone-300'"
        :style="{ flex: `${e.n} 1 0%` }"
        :title="e.etapa"
      >
        <component :is="iconoEtapa(e.etapa)" class="size-3.5 shrink-0" />
        <span v-if="e.n >= 3" class="truncate">{{ e.etapa }}</span>
      </span>
    </div>

    <!-- Celdas por mes -->
    <div class="flex gap-1" role="group" :aria-label="$t('campana.titulo')">
      <button
        v-for="m in meses"
        :key="m.mes"
        type="button"
        :aria-pressed="seleccionado === m.mes"
        :aria-label="etiquetaCelda(m)"
        class="relative flex h-11 min-w-0 flex-1 flex-col items-center justify-center rounded-lg text-xs font-bold transition active:scale-95"
        :class="[
          CELDA[m.riesgo],
          seleccionado === m.mes && (sobreOscuro ? 'ring-[3px] ring-white' : 'ring-[3px] ring-tinta dark:ring-white'),
          peor === m.mes && 'outline-2 outline-offset-2 outline-dashed ' + (sobreOscuro ? 'outline-white/80' : 'outline-red-600 dark:outline-red-400'),
        ]"
        @click="alternar(m.mes)"
      >
        <TriangleAlert v-if="m.riesgo === 'alto'" class="size-3.5" aria-hidden="true" />
        <span>{{ inicial(m.mes) }}</span>
        <span
          v-if="marcarHoy && m.mes === hoy"
          class="absolute -top-2 rounded-full bg-tinta px-1.5 text-[9px] leading-4 text-white dark:bg-white dark:text-tinta"
        >{{ $t('campana.hoy') }}</span>
      </button>
    </div>

    <!-- Mes más riesgoso -->
    <p v-if="mesPeor" class="mt-2.5">
      <button
        type="button"
        class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold transition"
        :class="sobreOscuro ? 'bg-red-500/25 text-white ring-1 ring-red-300/40 hover:bg-red-500/35' : 'bg-red-50 text-red-800 ring-1 ring-red-600/20 hover:bg-red-100 dark:bg-red-400/10 dark:text-red-300 dark:ring-red-400/25'"
        @click="seleccionado = mesPeor.mes"
      >
        <Flag class="size-3.5" aria-hidden="true" />{{ $t('campana.masRiesgoso') }}: <span class="capitalize">{{ largo(mesPeor.mes) }}</span>
      </button>
    </p>

    <!-- Motivo del mes tocado -->
    <Transition enter-from-class="opacity-0 -translate-y-1" enter-active-class="transition duration-200" leave-to-class="opacity-0" leave-active-class="transition duration-100" mode="out-in">
      <div
        v-if="detalle"
        :key="detalle.mes"
        role="status"
        class="mt-2.5 rounded-xl p-3 text-sm"
        :class="sobreOscuro ? 'bg-white/10 ring-1 ring-white/15' : 'bg-arena dark:bg-white/5'"
      >
        <p>
          <strong class="font-bold">{{ mayusculaInicial(conAnio(detalle.mes)) }}</strong><template v-if="detalle.etapa"> · {{ detalle.etapa }}</template>:
          {{ detalle.motivo }}
          <span v-if="detalle.et0MmDia != null" class="mt-1 block text-xs opacity-80">{{ $t('campana.et0', { et0: detalle.et0MmDia }) }}</span>
        </p>
        <p class="mt-1 inline-flex items-center gap-1 text-xs font-semibold" :class="sobreOscuro ? 'text-nasa-200' : 'text-nasa-800 dark:text-nasa-200'">
          <Satellite class="size-3.5" aria-hidden="true" />{{ $t('campana.fuente', { fuente: detalle.fuente }) }}
        </p>
      </div>
      <p v-else class="mt-2 text-[11px]" :class="sobreOscuro ? 'text-white/60' : 'text-stone-500 dark:text-stone-400'">{{ $t('campana.tocaMes') }}</p>
    </Transition>
  </div>
</template>
