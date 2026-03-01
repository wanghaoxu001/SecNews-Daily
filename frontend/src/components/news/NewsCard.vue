<template>
  <n-card
    size="small"
    :bordered="false"
    class="news-card"
    :class="{
      'news-card--selected': selected,
      'news-card--important': news.is_important === true,
    }"
    @click="$emit('click')"
  >
    <div class="news-card__head">
      <div class="news-card__tags">
        <n-tag v-if="news.is_important" type="success" size="small">建议收录</n-tag>
        <n-tag v-if="news.is_similar" type="warning" size="small">重复</n-tag>
        <n-tag v-if="news.category" :color="{ color: categoryBgColor, textColor: categoryColor }" size="small" :bordered="false">
          {{ news.category }}
        </n-tag>
      </div>
      <span class="news-card__time">{{ savedTime || '--' }}</span>
    </div>

    <h3 class="news-card__title">{{ news.title_zh || news.title }}</h3>
    <p class="news-card__summary">{{ summaryText }}</p>

    <div class="news-card__footer">
      <span class="news-card__source">{{ news.source_name || '未知来源' }}</span>
      <n-button
        size="tiny"
        :type="selected ? 'primary' : 'default'"
        :ghost="!selected"
        class="news-card__select-btn"
        @click.stop="$emit('toggle')"
      >
        {{ selected ? '已选' : '选择' }}
      </n-button>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NCard, NTag } from 'naive-ui'
import type { News } from '../../types'
import { CATEGORY_COLORS } from '../../types/enums'
import { formatMonthDayTime } from '../../utils/date'

const props = defineProps<{
  news: News
  selected: boolean
}>()

defineEmits<{
  click: []
  toggle: []
}>()

const categoryColor = computed(() => CATEGORY_COLORS[props.news.category || ''] || '#6c7d90')
const categoryBgColor = computed(() => colorToSoftBg(categoryColor.value))
const summaryText = computed(() => props.news.summary_zh || props.news.summary || '暂无摘要')
const savedTime = computed(() => formatMonthDayTime(props.news.created_at))

function colorToSoftBg(color: string): string {
  if (color.startsWith('#') && color.length === 7) {
    return `${color}24`
  }
  return 'var(--color-brand-soft)'
}
</script>

<style scoped>
.news-card {
  border: 1px solid var(--color-line-subtle);
  border-radius: var(--radius-m);
  background: #ffffff;
  box-shadow: var(--shadow-1);
  cursor: pointer;
  transition:
    transform var(--motion-fast) ease,
    box-shadow var(--motion-fast) ease,
    border-color var(--motion-fast) ease;
}

.news-card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-brand-500) 42%, var(--color-line-subtle));
  box-shadow: var(--shadow-2);
}

.news-card--selected {
  border-color: color-mix(in srgb, var(--color-brand-500) 60%, #ffffff 40%);
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--color-brand-500) 30%, transparent),
    var(--shadow-2);
}

.news-card--important {
  border-color: color-mix(in srgb, var(--color-success-500) 38%, var(--color-line-subtle));
  background: color-mix(in srgb, #ffffff 94%, #ecfff5 6%);
}

.news-card :deep(.n-card__content) {
  padding: 10px 14px 12px;
}

.news-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
}

.news-card__tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.news-card__time {
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.news-card__title {
  margin: 8px 0 6px;
  font-size: 18px;
  line-height: 1.34;
  font-weight: 800;
  color: var(--color-text-primary);
}

.news-card__summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 16px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.news-card__footer {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid color-mix(in srgb, var(--color-line-subtle) 78%, transparent);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
}

.news-card__source,
.news-card__select-btn {
  font-size: 12px;
}

.news-card__source {
  color: var(--color-text-secondary);
}

.news-card__select-btn :deep(.n-button__content) {
  font-weight: 600;
}

@media (max-width: 767px) {
  .news-card__title {
    font-size: 16px;
    margin-top: 6px;
  }

  .news-card__head,
  .news-card__footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .news-card__time {
    margin-left: 26px;
  }
}
</style>
