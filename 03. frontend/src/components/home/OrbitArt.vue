<template>
  <!-- Decoración: planeta con órbita y satélite girando -->
  <div class="pointer-events-none absolute -top-24 -right-24 size-60 opacity-70 sm:-top-20 sm:-right-16" aria-hidden="true">
    <div class="absolute inset-[30%] rounded-full bg-[radial-gradient(circle_at_35%_30%,#4cb373,#123f29_60%,#082316)] shadow-[0_0_60px_10px_rgb(91_133_245/0.25)]" />
    <div class="absolute inset-[30%] rounded-full bg-[radial-gradient(circle_at_70%_70%,transparent_40%,rgb(0_0_0/0.5))]" />
    <div class="absolute inset-[12%] rounded-full border border-white/12" />
    <div class="absolute inset-0 animate-orbit">
      <div class="absolute inset-[12%] rounded-full">
        <span class="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2">
          <span class="absolute inset-0 animate-pulse-ring rounded-full bg-brote-400" />
          <span class="relative block size-2.5 rounded-full bg-brote-300 shadow-[0_0_12px_3px_rgb(194_238_92/0.7)]" />
        </span>
      </div>
    </div>
    <div class="absolute inset-0 rounded-full border border-dashed border-white/8" />
  </div>
</template>
