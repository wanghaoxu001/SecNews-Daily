<template>
  <div>
    <n-button @click="openCreate" size="small" style="margin-bottom: var(--space-3);">添加 RSS 源</n-button>
    <n-data-table :columns="columns" :data="sources" :loading="sourcesQuery.isLoading.value" size="small" />

    <n-modal v-model:show="showModal" preset="dialog" title="RSS 源" style="width: min(500px, 92vw);">
      <n-form>
        <n-form-item label="名称"><n-input v-model:value="form.name" /></n-form-item>
        <n-form-item label="URL"><n-input v-model:value="form.url" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="form.description" type="textarea" /></n-form-item>
        <n-form-item label="启用"><n-switch v-model:value="form.enabled" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="handleSave" type="primary" :loading="saveMutation.isPending.value">保存</n-button>
      </template>
    </n-modal>

    <n-drawer :show="showRunDrawer" @update:show="showRunDrawer = $event" :width="drawerWidth" placement="right">
      <n-drawer-content :title="`抓取: ${runSourceName}`">
        <div ref="logContainerRef" class="rss-run-log">
          <div v-for="(log, i) in runLogs" :key="i" class="rss-run-log__item">
            <div class="rss-run-log__row">
              <n-spin v-if="log.status === 'running'" :size="14" class="rss-run-log__spinner" />
              <span v-else-if="log.status === 'success'" class="rss-run-log__status rss-run-log__status--success">✓</span>
              <span v-else-if="log.status === 'error'" class="rss-run-log__status rss-run-log__status--error">✗</span>
              <span v-else class="rss-run-log__status rss-run-log__status--info">·</span>
              <span class="rss-run-log__message" :class="{ 'rss-run-log__message--error': log.status === 'error' }">{{ log.message }}</span>
              <span v-if="log.duration_ms != null" class="rss-run-log__duration">{{ formatDuration(log.duration_ms) }}</span>
            </div>
            <pre v-if="log.detail" class="rss-run-log__detail">{{ log.detail }}</pre>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, h, nextTick } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  NButton,
  NDataTable,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSwitch,
  NTag,
  NDrawer,
  NDrawerContent,
  NSpin,
  useMessage,
} from 'naive-ui'
import {
  fetchRssSources,
  createRssSource,
  updateRssSource,
  deleteRssSource,
  runSourcePipeline,
  probeSourceCrawlPolicy,
} from '../../api/rss_sources'
import type { PipelineEvent } from '../../api/rss_sources'
import { queryKeys } from '../../shared/query/keys'
import { useResponsive } from '../../composables/useResponsive'
import type { RssSource } from '../../types'
import { formatDateTime } from '../../utils/date'

const message = useMessage()
const queryClient = useQueryClient()
const { isMobile } = useResponsive()

const showModal = ref(false)
const form = ref<Partial<RssSource>>({ enabled: true })

const showRunDrawer = ref(false)
const runSourceName = ref('')
const runLogs = ref<PipelineEvent[]>([])
const running = ref(false)
const probingSourceId = ref<number | null>(null)
const logContainerRef = ref<HTMLElement | null>(null)

const drawerWidth = computed(() => (isMobile.value ? '100vw' : 520))

const sourcesQuery = useQuery({
  queryKey: queryKeys.rssSources.list,
  queryFn: fetchRssSources,
})

const saveMutation = useMutation({
  mutationFn: (payload: Partial<RssSource>) => {
    if (payload.id) return updateRssSource(payload.id, payload)
    return createRssSource(payload)
  },
  onSuccess: async () => {
    showModal.value = false
    form.value = { enabled: true }
    await queryClient.invalidateQueries({ queryKey: queryKeys.rssSources.list })
    message.success('保存成功')
  },
  onError: () => {
    message.error('保存失败')
  },
})

const deleteMutation = useMutation({
  mutationFn: deleteRssSource,
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.rssSources.list })
    message.success('已删除')
  },
  onError: () => {
    message.error('删除失败')
  },
})

const sources = computed(() => sourcesQuery.data.value ?? [])

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  const seconds = ms / 1000
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainSec = (seconds % 60).toFixed(0)
  return `${minutes}m${remainSec}s`
}

function scrollToBottom() {
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
    }
  })
}

async function handleRun(row: RssSource) {
  if (running.value) return

  runSourceName.value = row.name
  runLogs.value = []
  showRunDrawer.value = true
  running.value = true

  try {
    await runSourcePipeline(row.id, (event: PipelineEvent) => {
      runLogs.value.push(event)
      scrollToBottom()
    })
    await queryClient.invalidateQueries({ queryKey: ['news', 'list'] })
  } catch (e: any) {
    runLogs.value.push({ step: 'done', status: 'error', message: `连接失败: ${e.message}` })
  } finally {
    running.value = false
  }
}

function probeStatusLabel(status: string | null): string {
  if (status === 'success') return '已完成'
  if (status === 'running') return '探测中'
  if (status === 'failed') return '失败'
  if (status === 'pending') return '待探测'
  return '未知'
}

function probeStatusType(status: string | null): 'success' | 'info' | 'error' | 'warning' | 'default' {
  if (status === 'success') return 'success'
  if (status === 'running') return 'info'
  if (status === 'failed') return 'error'
  if (status === 'pending') return 'warning'
  return 'default'
}

function formatTime(value: string | null): string {
  return value ? formatDateTime(value) : '-'
}

function resolvePolicyAttempts(row: RssSource): Array<{ waitFor: string; timeoutMs: number }> {
  const timeouts = row.effective_timeouts_ms ?? []
  const waits = row.effective_wait_for_chain ?? []
  const fallbackWait = waits[waits.length - 1] ?? '-'

  return timeouts.map((timeoutMs, index) => ({
    waitFor: waits[index] ?? fallbackWait,
    timeoutMs,
  }))
}

async function handleProbe(row: RssSource) {
  if (probingSourceId.value != null) return
  probingSourceId.value = row.id
  try {
    await probeSourceCrawlPolicy(row.id)
    await queryClient.invalidateQueries({ queryKey: queryKeys.rssSources.list })
    message.success('探测完成')
  } catch (e: any) {
    message.error(`探测失败: ${e?.message || 'unknown error'}`)
  } finally {
    probingSourceId.value = null
  }
}

const columns = [
  { title: '名称', key: 'name', width: 150 },
  { title: '域名', key: 'domain', width: 170, render: (row: RssSource) => row.domain || '-' },
  { title: 'URL', key: 'url', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'enabled',
    width: 80,
    render(row: RssSource) {
      return h(NTag, { type: row.enabled ? 'success' : 'default', size: 'small' }, { default: () => (row.enabled ? '启用' : '禁用') })
    },
  },
  {
    title: '探测状态',
    key: 'probe_status',
    width: 110,
    render(row: RssSource) {
      return h(
        NTag,
        { type: probeStatusType(row.probe_status), size: 'small' },
        { default: () => probeStatusLabel(row.probe_status) }
      )
    },
  },
  {
    title: '最近探测',
    key: 'probe_last_run_at',
    width: 180,
    render(row: RssSource) {
      return formatTime(row.probe_last_run_at)
    },
  },
  {
    title: '超时配置',
    key: 'effective_timeouts_ms',
    width: 420,
    render(row: RssSource) {
      const attempts = resolvePolicyAttempts(row)
      if (attempts.length === 0) return '-'
      return h(
        'div',
        { class: 'policy-attempts' },
        attempts.map((attempt, index) =>
          h(
            NTag,
            {
              size: 'small',
              bordered: false,
              class: 'policy-tag',
            },
            { default: () => `R${index + 1} ${attempt.waitFor} ${attempt.timeoutMs}ms` }
          )
        )
      )
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 270,
    render(row: RssSource) {
      return h('div', { class: 'table-actions' }, [
        h(
          NButton,
          {
            size: 'tiny',
            type: 'primary',
            secondary: true,
            disabled: running.value,
            onClick: () => handleRun(row),
          },
          { default: () => '抓取' }
        ),
        h(
          NButton,
          {
            size: 'tiny',
            type: 'info',
            tertiary: true,
            disabled: probingSourceId.value != null,
            loading: probingSourceId.value === row.id,
            onClick: () => handleProbe(row),
          },
          { default: () => '重探测' }
        ),
        h(
          NButton,
          {
            size: 'tiny',
            onClick: () => {
              form.value = { ...row }
              showModal.value = true
            },
          },
          { default: () => '编辑' }
        ),
        h(
          NButton,
          {
            size: 'tiny',
            type: 'error',
            onClick: () => deleteMutation.mutate(row.id),
          },
          { default: () => '删除' }
        ),
      ])
    },
  },
]

function openCreate() {
  form.value = { enabled: true }
  showModal.value = true
}

async function handleSave() {
  await saveMutation.mutateAsync(form.value)
}
</script>

<style scoped>
.table-actions {
  display: flex;
  gap: var(--space-2);
}

.policy-attempts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.policy-tag {
  background: var(--color-surface-soft);
}

.rss-run-log {
  max-height: calc(100dvh - 140px);
  overflow-y: auto;
}

.rss-run-log__item {
  margin-bottom: var(--space-2);
  font-size: 13px;
}

.rss-run-log__row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.rss-run-log__spinner,
.rss-run-log__status {
  flex-shrink: 0;
  margin-top: 3px;
}

.rss-run-log__status--success {
  color: #18a058;
}

.rss-run-log__status--error {
  color: #d03050;
}

.rss-run-log__status--info {
  color: #2080f0;
}

.rss-run-log__message {
  flex: 1;
}

.rss-run-log__message--error {
  color: #d03050;
}

.rss-run-log__duration {
  flex-shrink: 0;
  color: var(--color-text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.rss-run-log__detail {
  margin: 4px 0 0 20px;
  padding: var(--space-2);
  background: var(--color-surface-soft);
  border-radius: var(--radius-s);
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
