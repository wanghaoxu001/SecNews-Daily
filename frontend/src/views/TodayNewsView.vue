<template>
  <AppLayout>
    <ScrollProgressBar :progress="progress" />

    <section class="page-container today-news">
      <NewsFilter
        :filters="filters"
        :selected-count="selectedCount"
        :active-filter-labels="activeFilterLabels"
        :has-filters="hasFilters"
        :refresh-loading="newsQuery.isFetching.value"
        @change="handleFilterChange"
        @reset="handleFilterReset"
        @refresh="handleRefresh"
      />

      <n-spin :show="newsQuery.isFetching.value">
        <div v-if="newsList.length === 0 && !newsQuery.isFetching.value" class="empty-state">
          <h3 class="today-news__empty-title">暂无新闻</h3>
          <p class="today-news__empty-hint">可以点击“刷新数据”尝试重新拉取。</p>
        </div>

        <div v-else class="today-news__list">
          <NewsCard
            v-for="item in newsList"
            :key="item.id"
            :news="item"
            :selected="selection.isSelected(item.id)"
            @toggle="selection.toggle(item.id)"
            @click="openDetail(item)"
          />
        </div>
      </n-spin>

      <div v-if="total > pageSize" class="today-news__pagination actions-row">
        <n-pagination v-model:page="page" :page-count="Math.ceil(total / pageSize)" />
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
import { NSpin, NPagination, useMessage } from 'naive-ui'
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
import { STATUS_LABELS } from '../types/enums'
import type { News } from '../types'

type NewsFilters = {
  status?: string
  category?: string
}

const router = useRouter()
const message = useMessage()
const queryClient = useQueryClient()
const selection = useNewsSelection()
const { progress } = useScrollProgress()

const page = ref(1)
const pageSize = 20
const filters = ref<NewsFilters>({})

const drawerVisible = ref(false)
const selectedNews = ref<News | null>(null)

const newsQuery = useQuery({
  queryKey: computed(() =>
    queryKeys.news.list({
      page: page.value,
      page_size: pageSize,
      ...filters.value,
    })
  ),
  queryFn: () =>
    fetchNews({
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
const hasFilters = computed(() => Boolean(filters.value.status || filters.value.category))
const activeFilterLabels = computed(() => {
  const labels: string[] = []
  if (filters.value.category) {
    labels.push(`分类: ${filters.value.category}`)
  }
  if (filters.value.status) {
    labels.push(`状态: ${STATUS_LABELS[filters.value.status] || filters.value.status}`)
  }
  return labels
})

function openDetail(news: News) {
  selectedNews.value = news
  drawerVisible.value = true
}

function handleFilterChange(nextFilters: NewsFilters) {
  filters.value = nextFilters
  page.value = 1
}

function handleFilterReset() {
  filters.value = {}
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
.today-news {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.today-news__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.today-news__empty-title {
  margin: 0;
  font-size: 18px;
  color: var(--color-text-secondary);
}

.today-news__empty-hint {
  margin: var(--space-2) 0 0;
  font-size: 14px;
}

.today-news__pagination {
  justify-content: center;
  margin-top: calc(var(--space-2) * -1);
}

</style>
