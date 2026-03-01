<template>
  <div
    v-if="count > 0"
    style="position: fixed; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #eee; padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; z-index: 100;"
  >
    <span>已选择 {{ count }} 条新闻</span>
    <n-button type="primary" @click="$emit('generate')">生成快报</n-button>
  </div>
</template>

<script setup lang="ts">
import { NButton } from 'naive-ui'

defineProps<{ count: number }>()
defineEmits<{ generate: [] }>()
</script>
