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
import { fetchRssSources, createRssSource, updateRssSource, deleteRssSource, runSourcePipeline } from '../../api/rss_sources'
import type { PipelineEvent } from '../../api/rss_sources'
import { queryKeys } from '../../shared/query/keys'
import { useResponsive } from '../../composables/useResponsive'
import type { RssSource } from '../../types'

const message = useMessage()
const queryClient = useQueryClient()
const { isMobile } = useResponsive()

const showModal = ref(false)
const form = ref<Partial<RssSource>>({ enabled: true })

const showRunDrawer = ref(false)
const runSourceName = ref('')
const runLogs = ref<PipelineEvent[]>([])
const running = ref(false)
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

const columns = [
  { title: '名称', key: 'name', width: 150 },
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
    title: '操作',
    key: 'actions',
    width: 200,
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
