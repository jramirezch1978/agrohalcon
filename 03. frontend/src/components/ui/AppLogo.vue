<script setup lang="ts">
withDefaults(defineProps<{ tamano?: number }>(), { tamano: 36 })
</script>

<template>
  <svg :width="tamano" :height="tamano" viewBox="0 0 64 64" aria-hidden="true">
    <rect width="64" height="64" rx="18" fill="#0f2a1f" />
    <ellipse cx="32" cy="34" rx="25" ry="9" fill="none" stroke="#5b85f5" stroke-width="2" transform="rotate(-24 32 34)" opacity=".9" />
    <path d="M32 50V30" stroke="#fff" stroke-width="4.5" stroke-linecap="round" />
    <path d="M32 33c0-9 6-15 15-15 0 9-6 15-15 15z" fill="#c2ee5c" />
    <path d="M32 39c0-7.5-5-12.5-13-12.5 0 8 5 13 13 12.5z" fill="#80cf9c" />
    <circle cx="52" cy="22" r="3.5" fill="#fff" />
  </svg>
</template>
