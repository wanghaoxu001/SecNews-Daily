<template>
  <n-card size="small" :bordered="true" style="margin-bottom: 12px; cursor: pointer;" @click="$emit('click')">
    <template #header>
      <div style="display: flex; align-items: center; gap: 8px;">
        <n-checkbox :checked="selected" @update:checked="$emit('toggle')" @click.stop />
        <n-tag v-if="news.is_similar" type="warning" size="small">重复</n-tag>
        <n-tag v-if="news.is_important" type="success" size="small">建议收录</n-tag>
        <n-tag v-if="news.category" :color="{ textColor: categoryColor }" size="small" :bordered="false">
          {{ news.category }}
        </n-tag>
      </div>
    </template>
    <h4 style="margin: 0 0 4px 0;">{{ news.title_zh || news.title }}</h4>
    <p style="color: #666; font-size: 13px; margin: 0;">
      {{ news.summary_zh || news.summary || '暂无摘要' }}
    </p>
    <template #footer>
      <div style="display: flex; justify-content: space-between; color: #999; font-size: 12px;">
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
