<script setup lang="ts">
import { ref } from 'vue'
import { estado } from '../estado'
import { t } from '../i18n'
import { chat, preguntar } from './asistente'
import Icono from './Icono.vue'

const texto = ref('')
function enviar() {
  if (!texto.value.trim()) return
  preguntar(texto.value.trim())
  texto.value = ''
}
</script>

<template>
  <div class="asistente tarjeta" role="dialog" :aria-label="t('pregunta')">
    <div class="asis-cab">
      <span class="preg-ico"><Icono n="chispa" /></span>
      <div><b>{{ t('pregunta') }}</b><small class="tenue">Responde con los datos NASA ya calculados</small></div>
      <button class="x" aria-label="Cerrar" @click="estado.asistenteAbierto = false"><Icono n="cerrar" /></button>
    </div>
    <div class="asis-cuerpo">
      <p v-if="!chat.mensajes.length" class="tenue">Pregunta, por ejemplo: «¿Por qué no me conviene sembrar arroz?»</p>
      <div v-for="(m, k) in chat.mensajes" :key="k" :class="['burbuja', m.de]">{{ m.txt }}</div>
    </div>
    <form class="asis-form" @submit.prevent="enviar">
      <input v-model="texto" placeholder="Escribe tu pregunta…" />
      <button class="btn-primario" aria-label="Enviar"><Icono n="enviar" /></button>
    </form>
  </div>
</template>
