<template>
  <n-card size="small" :bordered="true" class="news-card" @click="$emit('click')">
    <template #header>
      <div class="news-card__tags">
        <n-checkbox :checked="selected" @update:checked="$emit('toggle')" @click.stop />
        <n-tag v-if="news.is_similar" type="warning" size="small">重复</n-tag>
        <n-tag v-if="news.is_important" type="success" size="small">建议收录</n-tag>
        <n-tag v-if="news.category" :color="{ textColor: categoryColor }" size="small" :bordered="false">
          {{ news.category }}
        </n-tag>
      </div>
    </template>

    <h4 class="news-card__title">{{ news.title_zh || news.title }}</h4>
    <p class="news-card__summary">{{ news.summary_zh || news.summary || '暂无摘要' }}</p>

    <template #footer>
      <div class="news-card__footer">
        <span>{{ news.source_name || '未知来源' }}</span>
        <span>{{ formatTime(news.created_at) }}</span>
      </div>
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NCheckbox, NTag } from 'naive-ui'
import type { News } from '../../types'
import { CATEGORY_COLORS } from '../../types/enums'
import { formatDate } from '../../utils/date'

const props = defineProps<{
  news: News
  selected: boolean
}>()

defineEmits<{
  click: []
  toggle: []
}>()

const categoryColor = computed(() => CATEGORY_COLORS[props.news.category || ''] || '#8c8c8c')

function formatTime(t: string | null): string {
  return formatDate(t)
}
</script>

<style scoped>
.news-card {
  margin-bottom: var(--space-3);
  cursor: pointer;
}

.news-card__tags {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.news-card__title {
  margin: 0 0 var(--space-2) 0;
}

.news-card__summary {
  color: var(--color-text-muted);
  font-size: 13px;
  margin: 0;
  line-height: 1.45;
}

.news-card__footer {
  display: flex;
  justify-content: space-between;
  color: var(--color-text-muted);
  font-size: 12px;
  gap: var(--space-2);
}

@media (max-width: 767px) {
  .news-card__footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
