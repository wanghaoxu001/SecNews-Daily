<template>
  <div v-if="count > 0" class="briefing-bar">
    <span>已选择 {{ count }} 条新闻</span>
    <n-button type="primary" @click="$emit('generate')">生成快报</n-button>
  </div>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui'

defineProps<{ count: number }>()
defineEmits<{ generate: [] }>()
</script>

<style scoped>
.briefing-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-6) var(--mobile-bottom-safe);
  border-top: 1px solid var(--color-border);
  background: color-mix(in srgb, var(--color-surface) 93%, #f8fbff 7%);
  backdrop-filter: blur(8px);
}

@media (max-width: 767px) {
  .briefing-bar {
    padding-left: var(--space-4);
    padding-right: var(--space-4);
  }
}
</style>
