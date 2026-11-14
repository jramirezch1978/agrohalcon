<script setup lang="ts">
withDefaults(defineProps<{ as?: string; interactiva?: boolean; padding?: 'none' | 'sm' | 'md' | 'lg' }>(), {
  as: 'div',
  interactiva: false,
  padding: 'md',
})
</script>

<template>
  <component
    :is="as"
    class="superficie"
    :class="[
      { none: '', sm: 'p-4', md: 'p-5', lg: 'p-6 sm:p-7' }[padding],
      interactiva &&
        'block w-full cursor-pointer text-left transition duration-300 ease-out hover:-translate-y-0.5 hover:shadow-float active:scale-[0.985]',
    ]"
  >
    <slot />
  </component>
</template>
