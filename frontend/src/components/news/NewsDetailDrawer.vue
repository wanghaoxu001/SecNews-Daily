<template>
  <n-drawer
    :show="visible"
    :width="drawerWidth"
    placement="right"
    @update:show="$emit('update:visible', $event)"
  >
    <n-drawer-content :title="news?.title_zh || news?.title || ''" closable>
      <template v-if="news">
        <n-descriptions :column="1" bordered size="small" class="news-drawer__meta">
          <n-descriptions-item label="原标题">{{ news.title }}</n-descriptions-item>
          <n-descriptions-item label="来源">{{ news.source_name || '未知' }}</n-descriptions-item>
          <n-descriptions-item label="分类">{{ news.category || '未分类' }}</n-descriptions-item>
          <n-descriptions-item label="状态">{{ news.process_status }}</n-descriptions-item>
          <n-descriptions-item label="保存时间">{{ formatTime(news.created_at) }}</n-descriptions-item>
          <n-descriptions-item label="发布时间">{{ formatTime(news.published_at) }}</n-descriptions-item>
          <n-descriptions-item label="重复">{{ news.is_similar ? '是' : '否' }}</n-descriptions-item>
          <n-descriptions-item label="重要">{{ news.is_important === null ? '未判定' : news.is_important ? '是' : '否' }}</n-descriptions-item>
        </n-descriptions>

        <h4>中文摘要</h4>
        <p>{{ news.summary_zh || '暂无' }}</p>

        <h4>原文摘要</h4>
        <p>{{ news.summary || '暂无' }}</p>

        <div v-if="news.importance_reason">
          <h4>重要性理由</h4>
          <p>{{ news.importance_reason }}</p>
        </div>

        <n-button tag="a" :href="news.url" target="_blank" type="primary" size="small">
          查看原文
        </n-button>
      </template>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NDrawer, NDrawerContent, NDescriptions, NDescriptionsItem, NButton } from 'naive-ui'
import type { News } from '../../types'
import { formatDateTime } from '../../utils/date'
import { useResponsive } from '../../composables/useResponsive'

defineProps<{
  visible: boolean
  news: News | null
}>()

defineEmits<{
  'update:visible': [value: boolean]
}>()

const { isMobile } = useResponsive()

const drawerWidth = computed(() => (isMobile.value ? '100vw' : 640))

function formatTime(t: string | null): string {
  return t ? formatDateTime(t) : '未知'
}
</script>

<style scoped>
.news-drawer__meta {
  margin-bottom: var(--space-4);
}
</style>
