<script setup lang="ts">
import { estado, irA, fechaHoy } from '../estado'
import { t } from '../i18n'
import Icono from './Icono.vue'
const fecha = fechaHoy.toLocaleDateString(estado.idioma === 'es' ? 'es-PE' : 'en-US', { day: 'numeric', month: 'long', year: 'numeric' })
</script>

<template>
  <div class="encabezado">
    <div>
      <span class="lugar"><Icono n="pin" :t="14" /> {{ estado.parcela.nombre }} <span class="tenue"><Icono n="calendario" :t="13" /> {{ fecha }}</span></span>
      <small class="tenue">{{ estado.parcela.lat.toFixed(3) }}, {{ estado.parcela.lon.toFixed(3) }}</small>
    </div>
    <button class="btn-borde" @click="irA('mapa')"><Icono n="lapiz" :t="14" /> {{ t('cambiarParcela') }}</button>
  </div>
</template>
