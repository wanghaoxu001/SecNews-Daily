<template>
  <section class="page-container page-container--wide tagger-page">
    <header class="surface-card tagger-page__hero">
      <div>
        <p class="section-eyebrow">Persistent Workflow</p>
        <h2 class="page-title">CSV 样本打标</h2>
        <p class="page-subtitle">
          上传固定模板 CSV 后逐条打标，进度自动保存到后端。空格标记并前进，回车前进，上方向键返回上一条。
        </p>
      </div>
      <div class="actions-row tagger-page__actions">
        <n-button @click="openFilePicker">上传 CSV</n-button>
        <n-button :disabled="!activeTaskId || currentIndex <= 0" @click="prevArticle">上一条</n-button>
        <n-button :disabled="!currentItem || isSavingLabel" @click="toggleCurrentMark">
          {{ currentIsImportant ? '取消重要' : '标记重要' }}
        </n-button>
        <n-button :disabled="!activeTaskId || isLastArticle || isSavingCursor" @click="nextArticle">下一条</n-button>
        <n-button
          :disabled="!canComplete || completeMutation.isPending.value"
          tertiary
          @click="handleCompleteTask"
        >
          标记完成
        </n-button>
        <n-button
          type="primary"
          :disabled="!canImport || importMutation.isPending.value"
          @click="handleImportTask"
        >
          导入样本库
        </n-button>
      </div>
      <p class="tagger-page__filename">{{ activeTask?.original_file_name || '未选择文件' }}</p>
      <p v-if="activeTask" class="tagger-page__saved-at">
        最近保存：{{ formatDateTime(activeTask.updated_at) || '-' }}
      </p>
      <p class="tagger-page__hint">CSV 模板列固定为 `title,summary,category,reason`。</p>
      <input
        ref="fileInput"
        class="tagger-page__file-input"
        type="file"
        accept=".csv,text/csv"
        @change="handleFileChange"
      />
    </header>

    <section class="surface-card tagger-page__history">
      <div class="tagger-page__history-head">
        <h3 class="tagger-page__section-title">历史任务</h3>
        <n-button size="small" tertiary :loading="tasksQuery.isFetching.value" @click="refreshTasks">刷新</n-button>
      </div>
      <div v-if="tasks.length === 0" class="empty-state">还没有打标任务，先上传一个 CSV。</div>
      <div v-else class="tagger-page__task-list">
        <button
          v-for="task in tasks"
          :key="task.id"
          type="button"
          class="tagger-page__task-card"
          :class="{ 'tagger-page__task-card--active': task.id === activeTaskId }"
          @click="openTask(task.id)"
        >
          <div class="tagger-page__task-card-head">
            <strong>{{ task.original_file_name }}</strong>
            <n-tag size="small" :type="statusTagType(task.status)">{{ statusLabel(task.status) }}</n-tag>
          </div>
          <span>已打标 {{ task.labeled_count }} / {{ task.total_count }}</span>
          <span>当前位置 {{ task.current_index + 1 }}</span>
          <span>更新时间 {{ formatDateTime(task.updated_at) || '-' }}</span>
        </button>
      </div>
    </section>

    <div v-if="isRestoring" class="empty-state">正在恢复任务...</div>
    <div v-else-if="!activeTask || !currentItem" class="empty-state">
      上传新的 CSV，或从上面的历史任务继续。
    </div>

    <template v-else>
      <section class="surface-card tagger-page__overview">
        <div class="tagger-page__stats">
          <n-tag type="default">总数 {{ activeTask.total_count }}</n-tag>
          <n-tag type="warning">当前位置 {{ currentIndex + 1 }}</n-tag>
          <n-tag :type="currentIsImportant ? 'success' : currentItem.is_important === false ? 'default' : 'warning'">
            当前 {{ currentLabelText }}
          </n-tag>
          <n-tag type="error">已打标 {{ activeTask.labeled_count }}</n-tag>
          <n-tag :type="statusTagType(activeTask.status)">{{ statusLabel(activeTask.status) }}</n-tag>
        </div>
        <n-progress
          type="line"
          :percentage="progressPercentage"
          :height="12"
          :show-indicator="true"
          processing
        />
      </section>

      <section class="surface-card tagger-page__article">
        <h3 class="tagger-page__article-title">样本信息</h3>
        <dl class="tagger-page__fields">
          <div class="tagger-page__field-item">
            <dt class="tagger-page__field-key">标题</dt>
            <dd class="tagger-page__field-value">{{ currentItem.title }}</dd>
          </div>
          <div class="tagger-page__field-item">
            <dt class="tagger-page__field-key">摘要</dt>
            <dd class="tagger-page__field-value">{{ currentItem.summary || '-' }}</dd>
          </div>
          <div class="tagger-page__field-item">
            <dt class="tagger-page__field-key">分类</dt>
            <dd class="tagger-page__field-value">{{ currentItem.category }}</dd>
          </div>
          <div class="tagger-page__field-item">
            <dt class="tagger-page__field-key">理由</dt>
            <dd class="tagger-page__field-value">{{ currentItem.reason || '-' }}</dd>
          </div>
        </dl>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { NButton, NProgress, NTag, useMessage } from 'naive-ui'
import axios from 'axios'
import {
  completeTaggingTask,
  createTaggingTask,
  fetchTaggingTask,
  fetchTaggingTasks,
  importTaggingTask,
  updateTaggingTaskCursor,
  updateTaggingTaskItem,
} from '../api/taggingTasks'
import { queryKeys } from '../shared/query/keys'
import type { TaggingTaskDetailResponse, TaggingTaskItem, TaggingTaskListItem } from '../types'
import { formatDateTime } from '../utils/date'
import { applyUpdatedTaggingTaskItem, createTaggingTaskDetail } from '../utils/taggingTaskDetail'

const LAST_TASK_KEY = 'secnews-daily:tagging-task:last-id'

const message = useMessage()
const queryClient = useQueryClient()

const fileInput = ref<HTMLInputElement | null>(null)
const activeTaskId = ref<number | null>(null)
const isRestoring = ref(true)
const isSavingCursor = ref(false)
const isSavingLabel = ref(false)

const tasksQuery = useQuery({
  queryKey: queryKeys.taggingTasks.list,
  queryFn: fetchTaggingTasks,
})

const taskDetailQuery = useQuery({
  queryKey: computed(() => queryKeys.taggingTasks.detail(activeTaskId.value ?? -1)),
  queryFn: () => fetchTaggingTask(activeTaskId.value as number),
  enabled: computed(() => activeTaskId.value !== null),
})

const createMutation = useMutation({
  mutationFn: createTaggingTask,
  onSuccess: async (result) => {
    applyTaskDetail(createTaggingTaskDetail(result.task, result.current_item))
    message.success(`已创建打标任务：${result.task.original_file_name}`)
    await refreshTasks()
  },
  onError: (error) => {
    handleRequestError(error, '创建打标任务失败')
  },
})

const completeMutation = useMutation({
  mutationFn: completeTaggingTask,
  onSuccess: async (result) => {
    applyTaskDetail(result)
    message.success('任务已标记为完成')
    await refreshTasks()
  },
  onError: (error) => {
    handleRequestError(error, '标记完成失败')
  },
})

const importMutation = useMutation({
  mutationFn: importTaggingTask,
  onSuccess: async (result) => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.importanceExamples.all() })
    await taskDetailQuery.refetch()
    await refreshTasks()
    message.success(`导入完成：新增 ${result.imported_count}，跳过 ${result.skipped_count}`)
  },
  onError: (error) => {
    handleRequestError(error, '导入样本库失败')
  },
})

const tasks = computed(() => tasksQuery.data.value ?? [])
const activeDetail = computed<TaggingTaskDetailResponse | null>(() => taskDetailQuery.data.value ?? null)
const activeTask = computed<TaggingTaskListItem | null>(() => activeDetail.value?.task ?? null)
const currentItem = computed<TaggingTaskItem | null>(() => activeDetail.value?.current_item ?? null)
const currentIndex = computed(() => activeTask.value?.current_index ?? 0)
const progressPercentage = computed(() => {
  if (!activeTask.value || activeTask.value.total_count === 0) return 0
  return Math.round((activeTask.value.labeled_count / activeTask.value.total_count) * 100)
})
const currentIsImportant = computed(() => currentItem.value?.is_important === true)
const currentLabelText = computed(() => {
  if (currentItem.value?.is_important === true) return '重要'
  if (currentItem.value?.is_important === false) return '不重要'
  return '未打标'
})
const isLastArticle = computed(() => {
  if (!activeTask.value) return false
  return activeTask.value.current_index >= activeTask.value.total_count - 1
})
const canComplete = computed(() => {
  if (!activeTask.value) return false
  return activeTask.value.labeled_count === activeTask.value.total_count && activeTask.value.status === 'in_progress'
})
const canImport = computed(() => activeTask.value?.status === 'completed')

watch(activeTaskId, (value) => {
  if (value === null) {
    localStorage.removeItem(LAST_TASK_KEY)
    return
  }
  localStorage.setItem(LAST_TASK_KEY, String(value))
})

function statusLabel(status: string): string {
  if (status === 'in_progress') return '进行中'
  if (status === 'completed') return '已完成'
  if (status === 'imported') return '已导入'
  return status
}

function statusTagType(status: string): 'default' | 'success' | 'warning' | 'info' {
  if (status === 'completed') return 'success'
  if (status === 'imported') return 'info'
  return 'warning'
}

function applyTaskDetail(detail: TaggingTaskDetailResponse) {
  activeTaskId.value = detail.task.id
  queryClient.setQueryData(queryKeys.taggingTasks.detail(detail.task.id), detail)
}

function openFilePicker() {
  fileInput.value?.click()
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    await createMutation.mutateAsync(file)
  } finally {
    target.value = ''
  }
}

async function openTask(taskId: number) {
  activeTaskId.value = taskId
  await taskDetailQuery.refetch()
}

async function refreshTasks() {
  await tasksQuery.refetch()
}

async function persistCursor(currentIndexValue: number) {
  if (!activeTaskId.value) return
  isSavingCursor.value = true
  try {
    const result = await updateTaggingTaskCursor(activeTaskId.value, currentIndexValue)
    applyTaskDetail(result)
  } catch (error) {
    handleRequestError(error, '保存当前位置失败')
  } finally {
    isSavingCursor.value = false
  }
}

async function setCurrentMark(isImportant: boolean | null) {
  if (!activeTaskId.value || !currentItem.value) return
  isSavingLabel.value = true
  try {
    const result = await updateTaggingTaskItem(activeTaskId.value, currentItem.value.id, isImportant)
    const detail = activeDetail.value
    if (!detail) return
    applyTaskDetail(applyUpdatedTaggingTaskItem(detail, result))
    await refreshTasks()
  } catch (error) {
    handleRequestError(error, '保存打标结果失败')
  } finally {
    isSavingLabel.value = false
  }
}

async function toggleCurrentMark() {
  if (!currentItem.value) return
  const nextValue = currentItem.value.is_important === true ? false : true
  await setCurrentMark(nextValue)
}

async function markCurrentAndNext() {
  if (!currentItem.value) return
  await setCurrentMark(true)
  if (!isLastArticle.value) {
    await nextArticle()
  }
}

async function nextArticle() {
  if (!activeTask.value || isLastArticle.value) return
  await persistCursor(activeTask.value.current_index + 1)
}

async function prevArticle() {
  if (!activeTask.value || activeTask.value.current_index <= 0) return
  await persistCursor(activeTask.value.current_index - 1)
}

async function handleCompleteTask() {
  if (!activeTaskId.value) return
  await completeMutation.mutateAsync(activeTaskId.value)
}

async function handleImportTask() {
  if (!activeTaskId.value) return
  await importMutation.mutateAsync(activeTaskId.value)
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  const tag = target.tagName.toLowerCase()
  return (
    tag === 'button' ||
    tag === 'a' ||
    tag === 'input' ||
    tag === 'textarea' ||
    tag === 'select' ||
    target.isContentEditable
  )
}

function handleRequestError(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string' && detail) {
      message.error(detail)
      return
    }
  }
  message.error(fallback)
}

function handleKeydown(event: KeyboardEvent) {
  if (!activeTask.value || !currentItem.value || isEditableTarget(event.target)) return

  if (event.code === 'Space') {
    event.preventDefault()
    void markCurrentAndNext()
    return
  }

  if (event.code === 'Enter') {
    event.preventDefault()
    void nextArticle()
    return
  }

  if (event.code === 'ArrowUp') {
    event.preventDefault()
    void prevArticle()
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  await refreshTasks()
  const persistedTaskId = Number(localStorage.getItem(LAST_TASK_KEY) || '')
  const latestTaskId = tasks.value[0]?.id
  const targetTaskId = Number.isInteger(persistedTaskId) && persistedTaskId > 0
    ? persistedTaskId
    : latestTaskId

  if (targetTaskId) {
    activeTaskId.value = targetTaskId
    await taskDetailQuery.refetch()
  }
  isRestoring.value = false
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.tagger-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-top: var(--space-6);
  padding-bottom: var(--space-7);
}

.tagger-page__hero,
.tagger-page__history,
.tagger-page__overview,
.tagger-page__article {
  padding: var(--space-4);
}

.tagger-page__actions {
  margin-top: var(--space-3);
}

.tagger-page__filename,
.tagger-page__saved-at,
.tagger-page__hint {
  margin: var(--space-2) 0 0;
  color: var(--color-text-secondary);
}

.tagger-page__hint {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.tagger-page__file-input {
  display: none;
}

.tagger-page__history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.tagger-page__section-title,
.tagger-page__article-title {
  margin: 0;
  font-size: 20px;
  color: var(--color-text-primary);
}

.tagger-page__task-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-3);
}

.tagger-page__task-card {
  border: 1px solid var(--color-line-subtle);
  border-radius: 18px;
  background: color-mix(in srgb, var(--color-panel) 92%, #f7f9ff 8%);
  padding: var(--space-3);
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  cursor: pointer;
}

.tagger-page__task-card--active {
  border-color: color-mix(in srgb, var(--color-brand-500) 45%, var(--color-line-subtle));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-brand-500) 25%, transparent);
}

.tagger-page__task-card-head {
  display: flex;
  justify-content: space-between;
  gap: var(--space-2);
  align-items: flex-start;
}

.tagger-page__stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.tagger-page__fields {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.tagger-page__field-item {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  border-top: 1px solid var(--color-line-subtle);
}

.tagger-page__field-item:first-child {
  border-top: none;
  padding-top: 0;
}

.tagger-page__field-key {
  margin: 0;
  color: var(--color-text-tertiary);
  font-weight: 600;
}

.tagger-page__field-value {
  margin: 0;
  color: var(--color-text-primary);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 767px) {
  .tagger-page {
    padding-top: var(--space-5);
    padding-bottom: var(--space-6);
  }

  .tagger-page__hero,
  .tagger-page__history,
  .tagger-page__overview,
  .tagger-page__article {
    padding: var(--space-3);
  }

  .tagger-page__field-item {
    grid-template-columns: 1fr;
    gap: var(--space-1);
  }
}
</style>
