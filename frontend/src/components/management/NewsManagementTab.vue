<template>
  <div class="news-management">
    <section class="news-management__filters surface-card">
      <n-input
        v-model:value="filters.keyword"
        placeholder="搜索标题..."
        clearable
        class="news-management__field news-management__field--keyword"
        @keyup.enter="handleQuery"
      />
      <n-select
        v-model:value="filters.status"
        placeholder="状态"
        clearable
        :options="statusOptions"
        class="news-management__field"
      />
      <n-select
        v-model:value="filters.category"
        placeholder="分类"
        clearable
        :options="categoryOptions"
        class="news-management__field"
      />
      <n-select
        v-model:value="filters.source_id"
        placeholder="来源"
        clearable
        :options="sourceOptions"
        class="news-management__field"
      />
      <n-select
        v-model:value="filters.is_similar"
        placeholder="相似"
        clearable
        :options="boolStringOptions('相似', '不相似')"
        class="news-management__field"
      />
      <n-select
        v-model:value="filters.is_important"
        placeholder="重要"
        clearable
        :options="boolStringOptions('重要', '不重要')"
        class="news-management__field"
      />
      <n-date-picker
        v-model:value="dateRange"
        type="daterange"
        clearable
        class="news-management__field news-management__field--range"
      />
      <div class="news-management__filter-actions">
        <n-button type="primary" @click="handleQuery">查询</n-button>
        <n-button @click="resetFilters">重置</n-button>
      </div>
    </section>

    <div v-if="checkedKeys.length > 0" class="news-management__batch-bar surface-card">
      <span>已选 {{ checkedKeys.length }} 条</span>
      <n-select
        v-model:value="reprocessTarget"
        :options="reprocessOptions"
        class="news-management__batch-select"
        size="small"
      />
      <n-button
        type="warning"
        size="small"
        :loading="batchReprocessMutation.isPending.value"
        @click="handleBatchReprocess"
      >
        批量重处理
      </n-button>
      <n-popconfirm @positive-click="handleBatchDelete">
        <template #trigger>
          <n-button type="error" size="small" :loading="batchDeleteMutation.isPending.value">
            批量删除
          </n-button>
        </template>
        确定删除选中的 {{ checkedKeys.length }} 条新闻？此操作不可恢复。
      </n-popconfirm>
    </div>

    <section class="news-management__content surface-card">
      <div v-if="isMobile" class="news-management__mobile-list">
        <article v-for="item in newsList" :key="item.id" class="news-management__mobile-item">
          <div class="news-management__mobile-item-head">
            <n-checkbox
              :checked="checkedKeys.includes(item.id)"
              @update:checked="(checked) => toggleChecked(item.id, checked)"
            />
            <div class="news-management__mobile-item-title">{{ item.title_zh || item.title }}</div>
          </div>

          <div class="news-management__mobile-meta">
            <n-tag size="small" :type="STATUS_COLORS[item.process_status] || 'default'">
              {{ STATUS_LABELS[item.process_status] || item.process_status }}
            </n-tag>
            <n-tag v-if="item.category" size="small" :bordered="false" :color="{ color: (CATEGORY_COLORS[item.category] || '#ccc') + '20', textColor: CATEGORY_COLORS[item.category] || '#666' }">
              {{ item.category }}
            </n-tag>
            <n-tag v-if="item.is_important" size="small" type="success">重要</n-tag>
            <n-tag v-if="item.is_similar" size="small" type="warning">重复</n-tag>
          </div>

          <div class="news-management__mobile-sub">来源：{{ item.source_name || '-' }}</div>
          <div class="news-management__mobile-sub">发布时间：{{ item.published_at ? formatDateTime(item.published_at) : '-' }}</div>

          <div class="actions-row">
            <n-button size="tiny" @click="openDetail(item)">详情</n-button>
          </div>
        </article>
      </div>

      <n-data-table
        v-else
        class="news-management__table"
        :columns="columns"
        :data="newsList"
        :loading="newsQuery.isLoading.value || newsQuery.isFetching.value"
        :row-key="(row: News) => row.id"
        size="small"
        :checked-row-keys="checkedKeys"
        @update:checked-row-keys="checkedKeys = $event as number[]"
        :scroll-x="1200"
      />
    </section>

    <div class="actions-row actions-row--end news-management__pagination">
      <n-pagination
        v-model:page="page"
        :page-size="pageSize"
        :item-count="total"
        show-size-picker
        :page-sizes="[20, 50, 100]"
        @update:page-size="handlePageSizeChange"
      />
    </div>

    <NewsDetailDrawer
      :visible="showDetail"
      :news="detailNews"
      @update:visible="showDetail = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  NInput,
  NSelect,
  NDatePicker,
  NButton,
  NDataTable,
  NPagination,
  NTag,
  NPopconfirm,
  NCheckbox,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { fetchNews, batchReprocessNews, batchDeleteNews } from '../../api/news'
import { fetchRssSources } from '../../api/rss_sources'
import NewsDetailDrawer from '../news/NewsDetailDrawer.vue'
import type { News } from '../../types'
import {
  NEWS_CATEGORIES,
  PROCESS_STATUSES,
  STATUS_LABELS,
  STATUS_COLORS,
  REPROCESS_TARGETS,
  CATEGORY_COLORS,
} from '../../types/enums'
import { formatDateTime } from '../../utils/date'
import { useResponsive } from '../../composables/useResponsive'
import { queryKeys } from '../../shared/query/keys'

const message = useMessage()
const queryClient = useQueryClient()
const { isMobile } = useResponsive()

const page = ref(1)
const pageSize = ref(20)
const checkedKeys = ref<number[]>([])
const reprocessTarget = ref('pending')
const showDetail = ref(false)
const detailNews = ref<News | null>(null)
const dateRange = ref<[number, number] | null>(null)

const filters = ref<{
  keyword: string | null
  status: string | null
  category: string | null
  source_id: number | null
  is_similar: string | null
  is_important: string | null
}>({
  keyword: null,
  status: null,
  category: null,
  source_id: null,
  is_similar: null,
  is_important: null,
})

const statusOptions = PROCESS_STATUSES.map(s => ({ label: STATUS_LABELS[s] || s, value: s }))
const categoryOptions = NEWS_CATEGORIES.map(c => ({ label: c, value: c }))
const reprocessOptions = REPROCESS_TARGETS.map(t => ({ label: t.label, value: t.value }))

const sourceQuery = useQuery({
  queryKey: queryKeys.rssSources.list,
  queryFn: fetchRssSources,
})

const sourceOptions = computed(() =>
  (sourceQuery.data.value ?? []).map(s => ({ label: s.name, value: s.id }))
)

const requestParams = computed(() => {
  const params: Record<string, unknown> = {
    page: page.value,
    page_size: pageSize.value,
  }

  if (filters.value.keyword) params.keyword = filters.value.keyword
  if (filters.value.status) params.status = filters.value.status
  if (filters.value.category) params.category = filters.value.category
  if (filters.value.source_id) params.source_id = filters.value.source_id
  if (filters.value.is_similar !== null) params.is_similar = filters.value.is_similar === 'true'
  if (filters.value.is_important !== null) params.is_important = filters.value.is_important === 'true'
  if (dateRange.value) {
    params.date_from = new Date(dateRange.value[0]).toISOString()
    params.date_to = new Date(dateRange.value[1]).toISOString()
  }

  return params
})

const newsQuery = useQuery({
  queryKey: computed(() => queryKeys.news.list(requestParams.value as any)),
  queryFn: () => fetchNews(requestParams.value as any),
})

const batchReprocessMutation = useMutation({
  mutationFn: (payload: { ids: number[]; target: string }) => batchReprocessNews(payload.ids, payload.target),
  onSuccess: async (result) => {
    message.success(`已重置 ${result.reset_count} 条新闻，Pipeline 执行完成`)
    checkedKeys.value = []
    await queryClient.invalidateQueries({ queryKey: ['news', 'list'] })
  },
  onError: () => {
    message.error('批量重处理失败')
  },
})

const batchDeleteMutation = useMutation({
  mutationFn: (ids: number[]) => batchDeleteNews(ids),
  onSuccess: async (result) => {
    message.success(`已删除 ${result.deleted_count} 条新闻`)
    checkedKeys.value = []
    await queryClient.invalidateQueries({ queryKey: ['news', 'list'] })
  },
  onError: () => {
    message.error('批量删除失败')
  },
})

const newsList = computed(() => newsQuery.data.value?.items ?? [])
const total = computed(() => newsQuery.data.value?.total ?? 0)

const columns: DataTableColumns<News> = [
  { type: 'selection' },
  { title: 'ID', key: 'id', width: 60, sorter: 'default' },
  {
    title: '标题',
    key: 'title_zh',
    ellipsis: { tooltip: true },
    minWidth: 200,
    render(row) {
      return h('span', {}, row.title_zh || row.title)
    },
  },
  {
    title: '来源',
    key: 'source_name',
    width: 120,
    ellipsis: { tooltip: true },
    render(row) {
      return row.source_name || '-'
    },
  },
  {
    title: '分类',
    key: 'category',
    width: 150,
    render(row) {
      if (!row.category) return '-'
      return h(
        NTag,
        {
          size: 'small',
          bordered: false,
          color: { color: CATEGORY_COLORS[row.category] + '20', textColor: CATEGORY_COLORS[row.category] },
        },
        { default: () => row.category }
      )
    },
  },
  {
    title: '状态',
    key: 'process_status',
    width: 90,
    render(row) {
      return h(
        NTag,
        {
          size: 'small',
          type: STATUS_COLORS[row.process_status] || 'default',
        },
        { default: () => STATUS_LABELS[row.process_status] || row.process_status }
      )
    },
  },
  {
    title: '相似',
    key: 'is_similar',
    width: 60,
    render(row) {
      return row.is_similar ? h(NTag, { size: 'small', type: 'warning' }, { default: () => '是' }) : '-'
    },
  },
  {
    title: '重要',
    key: 'is_important',
    width: 60,
    render(row) {
      if (row.is_important === null) return '-'
      return row.is_important
        ? h(NTag, { size: 'small', type: 'success' }, { default: () => '是' })
        : h(NTag, { size: 'small', type: 'default' }, { default: () => '否' })
    },
  },
  {
    title: '发布时间',
    key: 'published_at',
    width: 160,
    render(row) {
      if (!row.published_at) return '-'
      return formatDateTime(row.published_at)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 70,
    render(row) {
      return h(
        NButton,
        {
          size: 'tiny',
          onClick: () => openDetail(row),
        },
        { default: () => '详情' }
      )
    },
  },
]

function boolStringOptions(trueLabel: string, falseLabel: string) {
  return [
    { label: trueLabel, value: 'true' },
    { label: falseLabel, value: 'false' },
  ]
}

function handleQuery() {
  page.value = 1
  queryClient.invalidateQueries({ queryKey: ['news', 'list'] })
}

function handlePageSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
}

function resetFilters() {
  filters.value = {
    keyword: null,
    status: null,
    category: null,
    source_id: null,
    is_similar: null,
    is_important: null,
  }
  dateRange.value = null
  page.value = 1
}

function openDetail(news: News) {
  detailNews.value = news
  showDetail.value = true
}

function toggleChecked(id: number, checked: boolean) {
  const exists = checkedKeys.value.includes(id)
  if (checked && !exists) {
    checkedKeys.value = [...checkedKeys.value, id]
  }
  if (!checked && exists) {
    checkedKeys.value = checkedKeys.value.filter(key => key !== id)
  }
}

async function handleBatchReprocess() {
  if (checkedKeys.value.length === 0) return
  await batchReprocessMutation.mutateAsync({ ids: checkedKeys.value, target: reprocessTarget.value })
}

async function handleBatchDelete() {
  if (checkedKeys.value.length === 0) return
  await batchDeleteMutation.mutateAsync(checkedKeys.value)
}
</script>

<style scoped>
.news-management {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.news-management__filters {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: var(--space-3);
  padding: var(--space-4);
  align-items: end;
}

.news-management__field {
  min-width: 0;
  grid-column: span 1;
}

.news-management__field--keyword {
  grid-column: span 2;
}

.news-management__field--range {
  grid-column: span 2;
}

.news-management__filter-actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}

.news-management__batch-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: color-mix(in srgb, var(--color-brand-soft) 58%, #ffffff 42%);
}

.news-management__batch-select {
  width: 220px;
}

.news-management__content {
  padding: var(--space-3);
}

.news-management__table :deep(.n-data-table-wrapper) {
  border-radius: var(--radius-s);
  overflow: hidden;
}

.news-management__mobile-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.news-management__mobile-item {
  border: 1px solid var(--color-line-subtle);
  border-radius: var(--radius-s);
  background: color-mix(in srgb, var(--color-panel) 88%, var(--color-panel-muted) 12%);
  padding: var(--space-3);
}

.news-management__mobile-item-head {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
}

.news-management__mobile-item-title {
  font-weight: 600;
  line-height: 1.4;
}

.news-management__mobile-meta {
  margin-top: var(--space-2);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.news-management__mobile-sub {
  margin-top: var(--space-2);
  font-size: 12px;
  color: var(--color-text-muted);
}

.news-management__pagination {
  margin-top: calc(var(--space-2) * -1);
}

@media (max-width: 1279px) {
  .news-management__filters {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .news-management__field--keyword,
  .news-management__field--range {
    grid-column: span 2;
  }

  .news-management__filter-actions {
    grid-column: span 4;
    justify-content: flex-start;
  }
}

@media (max-width: 767px) {
  .news-management__filters {
    grid-template-columns: 1fr;
    padding: var(--space-3);
  }

  .news-management__field,
  .news-management__field--keyword,
  .news-management__field--range,
  .news-management__filter-actions {
    grid-column: span 1;
  }

  .news-management__batch-select {
    width: 100%;
  }
}
</style>
