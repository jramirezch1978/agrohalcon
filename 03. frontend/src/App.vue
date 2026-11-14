<script setup lang="ts">
import { computed } from 'vue'
import { estado, irA, type Ruta } from './estado'
import { t } from './i18n'
import Mapa from './vistas/Mapa.vue'
import QueHago from './vistas/QueHago.vue'
import QueSiembro from './vistas/QueSiembro.vue'
import Funciona from './vistas/Funciona.vue'
import Ayuda from './vistas/Ayuda.vue'
import Asistente from './componentes/Asistente.vue'
import Icono from './componentes/Icono.vue'

const menu = computed(() => [
  { r: 'campana' as Ruta, txt: t('queHago'), ico: 'sol' },
  { r: 'siembro' as Ruta, txt: t('queSiembro'), ico: 'brote' },
  { r: 'mapa' as Ruta, txt: t('mapa'), ico: 'mapa' },
  { r: 'funciona' as Ruta, txt: t('funciona'), ico: 'check' },
  { r: 'ayuda' as Ruta, txt: t('ayuda'), ico: 'ayuda' },
])
const parcelaCorta = computed(() => estado.parcela.nombre.split(',')[0])
</script>

<template>
  <div class="app">
    <aside class="lateral">
      <div class="marca">
        <img src="/favicon.png" alt="" />
        <div>
          <b>AllpaShift</b>
          <small>{{ t('sub') }}</small>
        </div>
      </div>
      <nav>
        <a v-for="m in menu" :key="m.r" :class="{ activo: estado.ruta === m.r }" :href="'#/' + m.r">
          <Icono :n="m.ico" /> {{ m.txt }}
        </a>
      </nav>
      <div class="lateral-pie">
        <button class="parcela-chip" :title="estado.parcela.nombre" @click="irA('mapa')">
          <Icono n="pin" /> <span>{{ parcelaCorta }}</span> <Icono n="abajo" />
        </button>
        <div class="ajustes">
          <div class="idioma">
            <button :class="{ on: estado.idioma === 'es' }" @click="estado.idioma = 'es'">ES</button>
            <button :class="{ on: estado.idioma === 'en' }" @click="estado.idioma = 'en'">EN</button>
          </div>
          <button class="tema" :aria-label="estado.tema === 'oscuro' ? 'Modo claro' : 'Modo oscuro'" @click="estado.tema = estado.tema === 'oscuro' ? 'claro' : 'oscuro'">
            <Icono :n="estado.tema === 'oscuro' ? 'sol' : 'luna'" />
          </button>
        </div>
      </div>
    </aside>

    <main class="contenido">
      <Mapa v-if="estado.ruta === 'mapa'" />
      <QueHago v-else-if="estado.ruta === 'campana'" />
      <QueSiembro v-else-if="estado.ruta === 'siembro'" />
      <Funciona v-else-if="estado.ruta === 'funciona'" />
      <Ayuda v-else />
    </main>

    <button v-if="estado.ruta !== 'mapa'" class="flotante" @click="estado.asistenteAbierto = !estado.asistenteAbierto">
      <span class="flotante-ico"><Icono n="chispa" /></span> {{ t('pregunta') }}
    </button>
    <Asistente v-if="estado.asistenteAbierto" />
  </div>
</template>
