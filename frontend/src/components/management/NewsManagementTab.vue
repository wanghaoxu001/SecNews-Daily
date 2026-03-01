<template>
  <div>
    <!-- Filter bar -->
    <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; align-items: flex-end;">
      <n-input
        v-model:value="filters.keyword"
        placeholder="搜索标题..."
        clearable
        style="width: 200px;"
        @keyup.enter="loadData"
      />
      <n-select
        v-model:value="filters.status"
        placeholder="状态"
        clearable
        :options="statusOptions"
        style="width: 130px;"
      />
      <n-select
        v-model:value="filters.category"
        placeholder="分类"
        clearable
        :options="categoryOptions"
        style="width: 180px;"
      />
      <n-select
        v-model:value="filters.source_id"
        placeholder="来源"
        clearable
        :options="sourceOptions"
        style="width: 160px;"
      />
      <n-select
        v-model:value="filters.is_similar"
        placeholder="相似"
        clearable
        :options="boolStringOptions('相似', '不相似')"
        style="width: 110px;"
      />
      <n-select
        v-model:value="filters.is_important"
        placeholder="重要"
        clearable
        :options="boolStringOptions('重要', '不重要')"
        style="width: 110px;"
      />
      <n-date-picker
        v-model:value="dateRange"
        type="daterange"
        clearable
        style="width: 260px;"
      />
      <n-button type="primary" @click="loadData">查询</n-button>
      <n-button @click="resetFilters">重置</n-button>
    </div>

    <!-- Batch action bar -->
    <div v-if="checkedKeys.length > 0" style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; padding: 8px 12px; background: #f0f9ff; border-radius: 6px;">
      <span>已选 {{ checkedKeys.length }} 条</span>
      <n-select
        v-model:value="reprocessTarget"
        :options="reprocessOptions"
        style="width: 240px;"
        size="small"
      />
      <n-button
        type="warning"
        size="small"
        :loading="reprocessing"
        @click="handleBatchReprocess"
      >
        批量重处理
      </n-button>
      <n-popconfirm @positive-click="handleBatchDelete">
        <template #trigger>
          <n-button type="error" size="small" :loading="deleting">
            批量删除
          </n-button>
        </template>
        确定删除选中的 {{ checkedKeys.length }} 条新闻？此操作不可恢复。
      </n-popconfirm>
    </div>

    <!-- Data table -->
    <n-data-table
      :columns="columns"
      :data="newsList"
      :loading="loading"
      :row-key="(row: News) => row.id"
      size="small"
      :checked-row-keys="checkedKeys"
      @update:checked-row-keys="checkedKeys = $event as number[]"
      :scroll-x="1200"
    />

    <!-- Pagination -->
    <div style="display: flex; justify-content: flex-end; margin-top: 12px;">
      <n-pagination
        v-model:page="page"
        :page-size="pageSize"
        :item-count="total"
        show-size-picker
        :page-sizes="[20, 50, 100]"
        @update:page="loadData"
        @update:page-size="handlePageSizeChange"
      />
    </div>

    <!-- Detail drawer -->
    <NewsDetailDrawer
      :visible="showDetail"
      :news="detailNews"
      @update:visible="showDetail = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import {
  NInput, NSelect, NDatePicker, NButton, NDataTable, NPagination,
  NTag, NPopconfirm, useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { fetchNews, batchReprocessNews, batchDeleteNews } from '../../api/news'
import { fetchRssSources } from '../../api/rss_sources'
import NewsDetailDrawer from '../news/NewsDetailDrawer.vue'
import type { News, RssSource } from '../../types'
import {
  NEWS_CATEGORIES, PROCESS_STATUSES,
  STATUS_LABELS, STATUS_COLORS, REPROCESS_TARGETS, CATEGORY_COLORS,
} from '../../types/enums'
import { formatDateTime } from '../../utils/date'

const message = useMessage()

// State
const newsList = ref<News[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const checkedKeys = ref<number[]>([])
const reprocessTarget = ref('pending')
const reprocessing = ref(false)
const deleting = ref(false)
const showDetail = ref(false)
const detailNews = ref<News | null>(null)
const sources = ref<RssSource[]>([])
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

// Options
const statusOptions = PROCESS_STATUSES.map(s => ({ label: STATUS_LABELS[s] || s, value: s }))
const categoryOptions = NEWS_CATEGORIES.map(c => ({ label: c, value: c }))
const sourceOptions = computed(() =>
  sources.value.map(s => ({ label: s.name, value: s.id }))
)
const reprocessOptions = REPROCESS_TARGETS.map(t => ({ label: t.label, value: t.value }))

function boolStringOptions(trueLabel: string, falseLabel: string) {
  return [
    { label: trueLabel, value: 'true' },
    { label: falseLabel, value: 'false' },
  ]
}

// Columns
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
      return h(NTag, {
        size: 'small',
        bordered: false,
        color: { color: CATEGORY_COLORS[row.category] + '20', textColor: CATEGORY_COLORS[row.category] },
      }, { default: () => row.category })
    },
  },
  {
    title: '状态',
    key: 'process_status',
    width: 90,
    render(row) {
      return h(NTag, {
        size: 'small',
        type: STATUS_COLORS[row.process_status] || 'default',
      }, { default: () => STATUS_LABELS[row.process_status] || row.process_status })
    },
  },
  {
    title: '相似',
    key: 'is_similar',
    width: 60,
    render(row) {
      return row.is_similar
        ? h(NTag, { size: 'small', type: 'warning' }, { default: () => '是' })
        : '-'
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
      return h(NButton, {
        size: 'tiny',
        onClick: () => { detailNews.value = row; showDetail.value = true },
      }, { default: () => '详情' })
    },
  },
]

// Methods
async function loadData() {
  loading.value = true
  try {
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

    const resp = await fetchNews(params as any)
    newsList.value = resp.items
    total.value = resp.total
  } catch {
    message.error('加载新闻列表失败')
  } finally {
    loading.value = false
  }
}

function handlePageSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  loadData()
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
  loadData()
}

async function handleBatchReprocess() {
  if (checkedKeys.value.length === 0) return
  reprocessing.value = true
  try {
    const result = await batchReprocessNews(checkedKeys.value, reprocessTarget.value)
    message.success(`已重置 ${result.reset_count} 条新闻，Pipeline 执行完成`)
    checkedKeys.value = []
    await loadData()
  } catch {
    message.error('批量重处理失败')
  } finally {
    reprocessing.value = false
  }
}

async function handleBatchDelete() {
  if (checkedKeys.value.length === 0) return
  deleting.value = true
  try {
    const result = await batchDeleteNews(checkedKeys.value)
    message.success(`已删除 ${result.deleted_count} 条新闻`)
    checkedKeys.value = []
    await loadData()
  } catch {
    message.error('批量删除失败')
  } finally {
    deleting.value = false
  }
}

async function loadSources() {
  try {
    sources.value = await fetchRssSources()
  } catch {
    // ignore
  }
}

onMounted(() => {
  loadData()
  loadSources()
})
</script>
