<script setup lang="ts">
// Iconos de línea (estilo Lucide, dibujados a mano) para no depender de una librería.
defineProps<{ n: string; t?: number }>()
const P: Record<string, string> = {
  sol: 'M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  brote: 'M7 20h10M12 20v-8M12 12c0-4 3-6 7-6 0 4-3 6-7 6zM12 14c0-3-2.5-5-6-5 0 3.5 2.5 5 6 5z',
  mapa: 'M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15M15 6v15',
  check: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM8 12l3 3 5-6',
  ayuda: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.7M12 17h.01',
  pin: 'M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11zM12 7.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z',
  abajo: 'M6 9l6 6 6-6',
  luna: 'M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z',
  chispa: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z',
  buscar: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM20 20l-4-4',
  gps: 'M12 2v3M12 19v3M2 12h3M19 12h3M12 6a6 6 0 1 0 0 12 6 6 0 0 0 0-12zM12 10a2 2 0 1 0 0 4 2 2 0 0 0 0-4z',
  satelite: 'M13 7l4 4M7 13l4 4M3 21l4-4M14 3l7 7-4 4-7-7zM6.5 10.5l7 7M9 12a3 3 0 0 0 3 3',
  alerta: 'M12 3L2 20h20zM12 10v4M12 17h.01',
  info: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 11v5M12 8h.01',
  reloj: 'M7 3h10M7 21h10M8 3c0 5 8 5 8 9s-8 4-8 9M16 3c0 5-8 5-8 9',
  semilla: 'M12 20V10M12 10c-4 0-7-2.5-7-6 4 0 7 2.5 7 6zM12 13c3 0 6-2 6-5-3 0-6 2-6 5z',
  escudo: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z',
  gota: 'M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z',
  calendario: 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
  enviar: 'M21 3L10 14M21 3l-7 18-4-7-7-4z',
  flecha: 'M5 12h14M13 6l6 6-6 6',
  diagonal: 'M7 17L17 7M9 7h8v8',
  cerrar: 'M6 6l12 12M18 6L6 18',
  lapiz: 'M4 20h4L19 9l-4-4L4 16zM14 6l4 4',
  bandera: 'M5 21V4M5 4h11l-2 4 2 4H5',
  capas: 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5',
  ola: 'M2 12c2.5-3 5-3 7.5 0s5 3 7.5 0 3.5-2.5 5-1M2 17c2.5-3 5-3 7.5 0s5 3 7.5 0 3.5-2.5 5-1',
  termometro: 'M10 14V5a2 2 0 1 1 4 0v9a4 4 0 1 1-4 0z',
  hoja: 'M5 19c0-8 5-14 15-14 0 10-6 15-14 15zM5 19l8-8',
}
</script>

<template>
  <svg class="ico" :width="t ?? 18" :height="t ?? 18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path :d="P[n] ?? ''" />
  </svg>
</template>
