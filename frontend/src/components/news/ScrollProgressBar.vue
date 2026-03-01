<template>
  <div
    class="scroll-progress-bar"
    :style="{ width: `${progress}%`, opacity: progress > 0 ? 1 : 0 }"
  />
</template>

<script setup lang="ts">
defineProps<{ progress: number }>()
</script>

<style scoped>
.scroll-progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  z-index: 999;
  background: linear-gradient(90deg, var(--color-brand-500), color-mix(in srgb, var(--color-brand-500) 68%, #5ca6ff 32%));
  box-shadow: 0 0 12px rgba(28, 94, 200, 0.6);
  transition:
    width 200ms ease,
    opacity 160ms ease;
}
</style>
