<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AlertBanner from '@/components/ui/AlertBanner.vue'
import { useIndicador } from '@/composables/useIndicador'
import { CLAVES_INDICADOR } from '@/composables/useRiesgo'
import type { Indicadores } from '@/types/api'

const props = defineProps<{ indicadores: Indicadores }>()
const { t } = useI18n()
const { textoAlerta } = useIndicador()

// "Alerta: humedad del suelo muy baja y lluvia muy baja"
const texto = computed(() =>
  CLAVES_INDICADOR.flatMap((k) => {
    const ind = props.indicadores[k]
    return ind?.nivel === 'alto' ? [textoAlerta(k, ind)] : []
  })
    .join(t('inicio.y')),
)
</script>

<template>
  <AlertBanner v-if="texto">
    <strong class="font-bold">{{ $t('inicio.alerta') }}:</strong> {{ texto }}
  </AlertBanner>
</template>
