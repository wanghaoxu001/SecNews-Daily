<template>
  <div>
    <n-button @click="showModal = true" size="small" style="margin-bottom: 12px;">添加 RSS 源</n-button>
    <n-data-table :columns="columns" :data="sources" :loading="loading" size="small" />

    <n-modal v-model:show="showModal" preset="dialog" title="RSS 源" style="width: 500px;">
      <n-form>
        <n-form-item label="名称"><n-input v-model:value="form.name" /></n-form-item>
        <n-form-item label="URL"><n-input v-model:value="form.url" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="form.description" type="textarea" /></n-form-item>
        <n-form-item label="启用"><n-switch v-model:value="form.enabled" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="handleSave" type="primary" :loading="saving">保存</n-button>
      </template>
    </n-modal>

    <n-drawer :show="showRunDrawer" @update:show="showRunDrawer = $event" :width="520" placement="right">
      <n-drawer-content :title="`抓取: ${runSourceName}`">
        <div ref="logContainerRef" style="max-height: calc(100vh - 120px); overflow-y: auto;">
          <div v-for="(log, i) in runLogs" :key="i" style="margin-bottom: 8px; font-size: 13px;">
            <div style="display: flex; align-items: flex-start; gap: 6px;">
              <n-spin v-if="log.status === 'running'" :size="14" style="flex-shrink: 0; margin-top: 3px;" />
              <span v-else-if="log.status === 'success'" style="color: #18a058; flex-shrink: 0;">✓</span>
              <span v-else-if="log.status === 'error'" style="color: #d03050; flex-shrink: 0;">✗</span>
              <span v-else style="color: #2080f0; flex-shrink: 0;">·</span>
              <span style="flex: 1;" :style="{ color: log.status === 'error' ? '#d03050' : undefined }">{{ log.message }}</span>
              <span v-if="log.duration_ms != null" style="flex-shrink: 0; color: #999; font-size: 12px; white-space: nowrap;">{{ formatDuration(log.duration_ms) }}</span>
            </div>
            <pre v-if="log.detail" style="margin: 4px 0 0 20px; padding: 8px; background: #f5f5f5; border-radius: 4px; font-size: 12px; overflow-x: auto; white-space: pre-wrap; word-break: break-all;">{{ log.detail }}</pre>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, nextTick } from 'vue'
import {
  NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSwitch, NTag,
  NDrawer, NDrawerContent, NSpin,
  useMessage,
} from 'naive-ui'
import { fetchRssSources, createRssSource, updateRssSource, deleteRssSource, runSourcePipeline } from '../../api/rss_sources'
import type { PipelineEvent } from '../../api/rss_sources'
import type { RssSource } from '../../types'

const message = useMessage()
const sources = ref<RssSource[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const form = ref<Partial<RssSource>>({ enabled: true })

// Run drawer state
const showRunDrawer = ref(false)
const runSourceName = ref('')
const runLogs = ref<PipelineEvent[]>([])
const running = ref(false)
const logContainerRef = ref<HTMLElement | null>(null)

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
    title: '状态', key: 'enabled', width: 80,
    render(row: RssSource) {
      return h(NTag, { type: row.enabled ? 'success' : 'default', size: 'small' }, { default: () => row.enabled ? '启用' : '禁用' })
    },
  },
  {
    title: '操作', key: 'actions', width: 200,
    render(row: RssSource) {
      return h('div', { style: 'display:flex;gap:8px' }, [
        h(NButton, {
          size: 'tiny',
          type: 'primary',
          secondary: true,
          disabled: running.value,
          onClick: () => handleRun(row),
        }, { default: () => '抓取' }),
        h(NButton, { size: 'tiny', onClick: () => { form.value = { ...row }; showModal.value = true } }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', type: 'error', onClick: () => handleDelete(row.id) }, { default: () => '删除' }),
      ])
    },
  },
]

async function loadData() {
  loading.value = true
  try { sources.value = await fetchRssSources() } finally { loading.value = false }
}

async function handleSave() {
  saving.value = true
  try {
    if (form.value.id) { await updateRssSource(form.value.id, form.value) }
    else { await createRssSource(form.value) }
    showModal.value = false; form.value = { enabled: true }; await loadData(); message.success('保存成功')
  } catch { message.error('保存失败') } finally { saving.value = false }
}

async function handleDelete(id: number) {
  try { await deleteRssSource(id); await loadData(); message.success('已删除') } catch { message.error('删除失败') }
}

onMounted(loadData)
</script>
