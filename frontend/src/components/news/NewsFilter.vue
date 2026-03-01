<template>
  <section class="news-filter surface-card">
    <div class="news-filter__toolbar">
      <div class="news-filter__summary">
        <n-tag type="info" size="small" :bordered="false">已选 {{ selectedCount }} 条</n-tag>
        <n-tag v-if="hasFilters" size="small" :bordered="false" class="news-filter__active-tag">
          {{ activeFilterLabels.join(' / ') }}
        </n-tag>
      </div>

      <div class="news-filter__actions">
        <n-button tertiary size="small" @click="handleReset">清空筛选</n-button>
        <n-button secondary size="small" :loading="refreshLoading" @click="emit('refresh')">
          刷新数据
        </n-button>
      </div>
    </div>

    <div class="news-filter__controls">
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
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NSelect, NButton, NTag } from 'naive-ui'
import { NEWS_CATEGORIES, PROCESS_STATUSES, STATUS_LABELS } from '../../types/enums'

const props = defineProps<{
  filters: { status?: string; category?: string }
  selectedCount: number
  hasFilters: boolean
  activeFilterLabels: string[]
  refreshLoading: boolean
}>()

const emit = defineEmits<{
  change: [filters: { status?: string; category?: string }]
  reset: []
  refresh: []
}>()

const localCategory = ref<string | null>(null)
const localStatus = ref<string | null>(null)

const categoryOptions = NEWS_CATEGORIES.map(c => ({ label: c, value: c }))
const statusOptions = PROCESS_STATUSES.map(s => ({ label: STATUS_LABELS[s] || s, value: s }))

watch(
  () => props.filters,
  (next) => {
    localCategory.value = next.category ?? null
    localStatus.value = next.status ?? null
  },
  { immediate: true, deep: true }
)

function emitChange() {
  emit('change', {
    category: localCategory.value || undefined,
    status: localStatus.value || undefined,
  })
}

function handleReset() {
  localCategory.value = null
  localStatus.value = null
  emitChange()
  emit('reset')
}
</script>

<style scoped>
.news-filter {
  margin-bottom: var(--space-4);
  padding: var(--space-3);
}

.news-filter__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.news-filter__summary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  min-width: 0;
}

.news-filter__controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-3);
  align-items: center;
}

.news-filter__field {
  min-width: 0;
}

.news-filter__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
}

.news-filter__active-tag {
  max-width: min(46vw, 480px);
}

.news-filter__active-tag :deep(.n-tag__content) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .news-filter {
    margin-bottom: var(--space-3);
  }

  .news-filter__controls {
    grid-template-columns: 1fr;
  }

  .news-filter__actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
