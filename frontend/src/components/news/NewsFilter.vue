<template>
  <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center;">
    <n-select
      v-model:value="localCategory"
      placeholder="分类筛选"
      clearable
      :options="categoryOptions"
      style="width: 200px;"
      @update:value="emitChange"
    />
    <n-select
      v-model:value="localStatus"
      placeholder="状态筛选"
      clearable
      :options="statusOptions"
      style="width: 160px;"
      @update:value="emitChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NSelect } from 'naive-ui'
import { NEWS_CATEGORIES, PROCESS_STATUSES } from '../../types/enums'

const emit = defineEmits<{
  change: [filters: { status?: string; category?: string }]
}>()

const localCategory = ref<string | null>(null)
const localStatus = ref<string | null>(null)

const categoryOptions = NEWS_CATEGORIES.map(c => ({ label: c, value: c }))
const statusOptions = PROCESS_STATUSES.map(s => ({ label: s, value: s }))

function emitChange() {
  emit('change', {
    category: localCategory.value || undefined,
    status: localStatus.value || undefined,
  })
}
</script>
