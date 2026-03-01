<template>
  <AppLayout>
    <ScrollProgressBar :progress="progress" />
    <div style="max-width: 900px; margin: 0 auto;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h2 style="margin: 0;">今日新闻</h2>
        <n-space>
          <n-button size="small" @click="handleRefresh" :loading="refreshing">刷新</n-button>
        </n-space>
      </div>

      <NewsFilter @change="handleFilterChange" />

      <n-spin :show="newsStore.loading">
        <div v-if="newsStore.newsList.length === 0 && !newsStore.loading" style="text-align: center; padding: 60px; color: #999;">
          暂无新闻
        </div>
        <NewsCard
          v-for="item in newsStore.newsList"
          :key="item.id"
          :news="item"
          :selected="selection.isSelected(item.id)"
          @toggle="selection.toggle(item.id)"
          @click="openDetail(item)"
        />
      </n-spin>

      <div v-if="newsStore.total > newsStore.pageSize" style="display: flex; justify-content: center; margin-top: 16px;">
        <n-pagination
          v-model:page="newsStore.page"
          :page-count="Math.ceil(newsStore.total / newsStore.pageSize)"
          @update:page="newsStore.loadNews()"
        />
      </div>
    </div>

    <NewsDetailDrawer
      :visible="drawerVisible"
      :news="selectedNews"
      @update:visible="drawerVisible = $event"
    />

    <GenerateBriefingBar
      :count="selection.getSelectedIds().length"
      @generate="handleGenerate"
    />
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NSpin, NPagination, NButton, NSpace, useMessage } from 'naive-ui'
import AppLayout from '../components/layout/AppLayout.vue'
import NewsCard from '../components/news/NewsCard.vue'
import NewsFilter from '../components/news/NewsFilter.vue'
import NewsDetailDrawer from '../components/news/NewsDetailDrawer.vue'
import ScrollProgressBar from '../components/news/ScrollProgressBar.vue'
import GenerateBriefingBar from '../components/news/GenerateBriefingBar.vue'
import { useNewsStore } from '../stores/news'
import { useNewsSelection } from '../composables/useNewsSelection'
import { useScrollProgress } from '../composables/useScrollProgress'
import { createBriefing } from '../api/briefings'
import { todayInChina } from '../utils/date'
import type { News } from '../types'

const router = useRouter()
const message = useMessage()
const newsStore = useNewsStore()
const selection = useNewsSelection()
const { progress } = useScrollProgress()

const drawerVisible = ref(false)
const selectedNews = ref<News | null>(null)
const refreshing = ref(false)

function openDetail(news: News) {
  selectedNews.value = news
  drawerVisible.value = true
}

function handleFilterChange(filters: { status?: string; category?: string }) {
  newsStore.setFilters(filters)
  newsStore.loadNews()
}

async function handleRefresh() {
  refreshing.value = true
  try {
    await newsStore.loadNews()
  } finally {
    refreshing.value = false
  }
}

async function handleGenerate() {
  const ids = selection.getSelectedIds()
  if (ids.length === 0) return
  try {
    const today = todayInChina()
    const briefing = await createBriefing({
      title: `网安情报快报 ${today}`,
      date: today,
      news_ids: ids,
    })
    selection.clear()
    message.success('快报已创建')
    router.push({ name: 'BriefingEdit', params: { id: briefing.id } })
  } catch {
    message.error('创建快报失败')
  }
}

onMounted(() => {
  newsStore.loadNews()
})
</script>
