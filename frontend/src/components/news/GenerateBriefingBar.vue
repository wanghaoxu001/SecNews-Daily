<template>
  <div v-if="count > 0" class="briefing-bar-wrap">
    <div class="briefing-bar">
      <div class="briefing-bar__content">
        <p class="briefing-bar__title">已选择 {{ count }} 条新闻</p>
        <p class="briefing-bar__hint">确认后将进入快报编辑页面，可继续调整标题与内容。</p>
      </div>
      <n-button type="primary" strong size="large" @click="$emit('generate')">生成今日快报</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui'

defineProps<{ count: number }>()
defineEmits<{ generate: [] }>()
</script>

<style scoped>
.briefing-bar-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  padding: 0 var(--space-4) var(--mobile-bottom-safe);
}

.briefing-bar {
  margin: 0 auto;
  width: min(100%, var(--content-max-width));
  border: 1px solid color-mix(in srgb, var(--color-brand-500) 28%, var(--color-line-subtle));
  border-radius: var(--radius-m);
  background: color-mix(in srgb, var(--color-panel) 88%, var(--color-brand-soft) 12%);
  box-shadow: var(--shadow-3);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
}

.briefing-bar__content {
  min-width: 0;
}

.briefing-bar__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.briefing-bar__hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

@media (max-width: 767px) {
  .briefing-bar {
    flex-direction: column;
    align-items: stretch;
    padding: var(--space-3);
    gap: var(--space-3);
  }
}
</style>
