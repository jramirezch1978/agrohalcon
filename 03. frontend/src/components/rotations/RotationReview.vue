<script setup lang="ts">
import { AlertTriangle, CircleHelp, HandHeart, ThumbsUp, Users } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRotacion } from '@/composables/useRotacion'
import type { ClaveIndicador, Indicadores, PerfilRecomendacion, Rotacion } from '@/types/api'

/**
 * Lo que pide el reto para cada estrategia de rotación: ventajas, riesgos, vacíos de información
 * (incertidumbre) y lo que debe revisar el agricultor o un experto local. Todo se arma con los datos
 * que ya trae la rotación; no se inventa nada.
 */
const props = defineProps<{ rotacion: Rotacion; indicadores?: Indicadores; perfil?: PerfilRecomendacion }>()
const { t } = useI18n()
const { motivoDescuento } = useRotacion()

const ventajas = computed(() => {
  const r = props.rotacion
  const v = (r.descuentosSuelo ?? []).filter((d) => d.puntos > 0).map((d) => d.explicacion)
  if (r.usoAgua === 'bajo') v.push(t('revision.aguaBaja'))
  if ((r.riesgoClimatico ?? r.puntaje) >= 70) v.push(t('revision.climaBueno'))
  return v
})

const riesgos = computed(() => {
  const r = props.rotacion
  const v = (r.descuentos ?? []).filter((d) => d.puntos < 0).map((d) => `${t('revision.resta', { p: Math.abs(d.puntos) })} ${motivoDescuento(d, props.indicadores)}`)
  v.push(...(r.descuentosSuelo ?? []).filter((d) => d.puntos < 0).map((d) => d.explicacion))
  if (r.usoAgua === 'alto') v.push(t('revision.aguaAlta'))
  return v
})

const CLAVES: ClaveIndicador[] = ['lluvia', 'humedadSuelo', 'calor', 'elNino', 'vegetacion']
const vacios = computed(() => {
  const v: string[] = []
  const ind = props.indicadores ?? {}
  const faltan = CLAVES.filter((k) => !ind[k]).map((k) => t(`indicadores.${k}`).toLowerCase())
  if (faltan.length) v.push(t('revision.sinDato', { lista: faltan.join(', ') }))
  const gruesos = CLAVES.filter((k) => ind[k]?.fuente === 'NASA POWER').map((k) => t(`indicadores.${k}`).toLowerCase())
  if (gruesos.length) v.push(t('revision.power', { lista: gruesos.join(', ') }))
  const p = props.perfil
  if (!p?.tipoSuelo) v.push(t('revision.sueloDesconocido'))
  else if (p.fuenteSuelo === 'soilgrids') v.push(t('revision.sueloSoilgrids'))
  if (!p?.salinidad) v.push(t('revision.salinidadDesconocida'))
  v.push(t('revision.historial'))
  v.push(t('revision.umbrales'))
  return v
})

const revisarLocal = computed(() => [t('revision.mercado'), t('revision.plagas'), t('revision.agua'), t('revision.semilla')])
</script>

<template>
  <section class="mt-6 space-y-4" :aria-label="$t('revision.titulo')">
    <h3 class="text-sm font-bold">{{ $t('revision.titulo') }}</h3>

    <div v-if="ventajas.length" class="rounded-2xl bg-emerald-500/8 p-3 ring-1 ring-emerald-500/20">
      <p class="flex items-center gap-1.5 text-sm font-bold text-emerald-800 dark:text-emerald-300"><ThumbsUp class="size-4" aria-hidden="true" />{{ $t('revision.ventajas') }}</p>
      <ul class="mt-1.5 list-disc space-y-1 pl-5 text-sm leading-snug"><li v-for="(x, i) in ventajas" :key="i">{{ x }}</li></ul>
    </div>

    <div v-if="riesgos.length" class="rounded-2xl bg-red-500/8 p-3 ring-1 ring-red-500/20">
      <p class="flex items-center gap-1.5 text-sm font-bold text-red-800 dark:text-red-300"><AlertTriangle class="size-4" aria-hidden="true" />{{ $t('revision.riesgos') }}</p>
      <ul class="mt-1.5 list-disc space-y-1 pl-5 text-sm leading-snug"><li v-for="(x, i) in riesgos" :key="i">{{ x }}</li></ul>
    </div>

    <div class="rounded-2xl bg-amber-500/8 p-3 ring-1 ring-amber-500/25">
      <p class="flex items-center gap-1.5 text-sm font-bold text-amber-800 dark:text-amber-300"><CircleHelp class="size-4" aria-hidden="true" />{{ $t('revision.vacios') }}</p>
      <ul class="mt-1.5 list-disc space-y-1 pl-5 text-sm leading-snug"><li v-for="(x, i) in vacios" :key="i">{{ x }}</li></ul>
    </div>

    <div class="rounded-2xl bg-arena p-3 dark:bg-white/5">
      <p class="flex items-center gap-1.5 text-sm font-bold"><Users class="size-4" aria-hidden="true" />{{ $t('revision.revisarLocal') }}</p>
      <ul class="mt-1.5 list-disc space-y-1 pl-5 text-sm leading-snug"><li v-for="(x, i) in revisarLocal" :key="i">{{ x }}</li></ul>
    </div>

    <p class="flex items-start gap-2 text-xs leading-relaxed text-stone-600 dark:text-stone-300">
      <HandHeart class="mt-px size-4 shrink-0 text-agro-700 dark:text-brote-400" aria-hidden="true" />{{ $t('campana.apoyo') }}
    </p>
  </section>
</template>
