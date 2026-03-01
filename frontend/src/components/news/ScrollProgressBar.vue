<template>
  <div
    style="position: fixed; top: 0; left: 0; height: 3px; z-index: 9999; transition: width 0.2s;"
    :style="{ width: progress + '%', background: progress > 0 ? '#18a058' : 'transparent' }"
  />
</template>

<script setup lang="ts">
defineProps<{ progress: number }>()
</script>
