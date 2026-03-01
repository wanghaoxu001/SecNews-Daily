<template>
  <AppLayout>
    <ScrollProgressBar :progress="progress" />

    <section class="page-container">
      <div class="page-header">
        <h2 class="page-title">今日新闻</h2>
        <n-space>
          <n-button size="small" :loading="newsQuery.isFetching.value" @click="handleRefresh">刷新</n-button>
        </n-space>
      </div>

      <NewsFilter @change="handleFilterChange" />

      <n-spin :show="newsQuery.isFetching.value">
        <div v-if="newsList.length === 0 && !newsQuery.isFetching.value" class="empty-state">
          暂无新闻
        </div>
        <NewsCard
          v-for="item in newsList"
          :key="item.id"
          :news="item"
          :selected="selection.isSelected(item.id)"
          @toggle="selection.toggle(item.id)"
          @click="openDetail(item)"
        />
      </n-spin>

      <div v-if="total > pageSize" class="today-news__pagination actions-row">
        <n-pagination
          v-model:page="page"
          :page-count="Math.ceil(total / pageSize)"
        />
      </div>
    </section>

    <NewsDetailDrawer
      :visible="drawerVisible"
      :news="selectedNews"
      @update:visible="drawerVisible = $event"
    />

    <GenerateBriefingBar :count="selectedCount" @generate="handleGenerate" />
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation, useQuery, useQueryClient, keepPreviousData } from '@tanstack/vue-query'
import { NSpin, NPagination, NButton, NSpace, useMessage } from 'naive-ui'
import AppLayout from '../components/layout/AppLayout.vue'
import NewsCard from '../components/news/NewsCard.vue'
import NewsFilter from '../components/news/NewsFilter.vue'
import NewsDetailDrawer from '../components/news/NewsDetailDrawer.vue'
import ScrollProgressBar from '../components/news/ScrollProgressBar.vue'
import GenerateBriefingBar from '../components/news/GenerateBriefingBar.vue'
import { useNewsSelection } from '../composables/useNewsSelection'
import { useScrollProgress } from '../composables/useScrollProgress'
import { createBriefing } from '../api/briefings'
import { fetchNews } from '../api/news'
import { todayInChina } from '../utils/date'
import { queryKeys } from '../shared/query/keys'
import type { News } from '../types'

const router = useRouter()
const message = useMessage()
const queryClient = useQueryClient()
const selection = useNewsSelection()
const { progress } = useScrollProgress()

const page = ref(1)
const pageSize = 20
const filters = ref<{ status?: string; category?: string }>({})

const drawerVisible = ref(false)
const selectedNews = ref<News | null>(null)

const newsQuery = useQuery({
  queryKey: computed(() => queryKeys.news.list({
    page: page.value,
    page_size: pageSize,
    ...filters.value,
  })),
  queryFn: () => fetchNews({
    page: page.value,
    page_size: pageSize,
    ...filters.value,
  }),
  placeholderData: keepPreviousData,
})

const createBriefingMutation = useMutation({
  mutationFn: createBriefing,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.briefings.list })
  },
})

const newsList = computed(() => newsQuery.data.value?.items ?? [])
const total = computed(() => newsQuery.data.value?.total ?? 0)
const selectedCount = computed(() => selection.selectedIds.value.size)

function openDetail(news: News) {
  selectedNews.value = news
  drawerVisible.value = true
}

function handleFilterChange(nextFilters: { status?: string; category?: string }) {
  filters.value = nextFilters
  page.value = 1
}

async function handleRefresh() {
  await newsQuery.refetch()
}

async function handleGenerate() {
  const ids = selection.getSelectedIds()
  if (ids.length === 0) return

  try {
    const today = todayInChina()
    const briefing = await createBriefingMutation.mutateAsync({
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
</script>

<style scoped>
.today-news__pagination {
  justify-content: center;
  margin-top: var(--space-4);
}
</style>
