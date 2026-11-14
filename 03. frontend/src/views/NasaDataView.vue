<script setup lang="ts">
import HonestyNote from '@/components/campaign/HonestyNote.vue'
import AboutApp from '@/components/datasets/AboutApp.vue'
import DatasetCard from '@/components/datasets/DatasetCard.vue'
import HelpFaq from '@/components/datasets/HelpFaq.vue'
import HowItWorks from '@/components/datasets/HowItWorks.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { NASA_DATASETS } from '@/data/nasaDatasets'
</script>

<template>
  <!-- Ayuda: ¿Qué es? → Cómo funciona → Preguntas frecuentes → Los satélites (detalles técnicos plegados) -->
  <section>
    <PageHeader :titulo="$t('datos.titulo')" :subtitulo="$t('datos.subtitulo')" />
    <AboutApp class="stagger mb-6" style="--i: 1" />
    <HowItWorks class="stagger mb-6" style="--i: 2" />
    <HelpFaq class="stagger mb-8" style="--i: 3" />
    <SectionTitle :titulo="$t('datos.satelitesTitulo')" class="mb-4" />
    <ul class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <li v-for="(d, i) in NASA_DATASETS" :key="d.id" class="stagger" :style="{ '--i': i + 4 }">
        <DatasetCard :dataset="d" />
      </li>
    </ul>
    <HonestyNote class="mt-6 max-w-2xl" />
  </section>
</template>
