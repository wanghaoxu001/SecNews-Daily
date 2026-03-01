<template>
  <div class="news-filter">
    <n-select
      v-model:value="localCategory"
      placeholder="分类筛选"
      clearable
      :options="categoryOptions"
      class="news-filter__field"
      @update:value="emitChange"
    />
    <n-select
      v-model:value="localStatus"
      placeholder="状态筛选"
      clearable
      :options="statusOptions"
      class="news-filter__field"
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

<style scoped>
.news-filter {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.news-filter__field {
  min-width: 0;
}

@media (max-width: 767px) {
  .news-filter {
    grid-template-columns: 1fr;
  }
}
</style>
