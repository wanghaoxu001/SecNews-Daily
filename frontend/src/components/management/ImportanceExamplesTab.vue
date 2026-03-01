<template>
  <div>
    <div class="example-actions">
      <n-button @click="showModal = true" size="small">添加样本</n-button>
      <n-button @click="showBulkModal = true" size="small">JSON 批量导入</n-button>
      <n-button @click="showCsvModal = true" size="small">CSV 批量导入</n-button>
      <n-button @click="downloadCsvTemplate" size="small">下载 CSV 模板</n-button>
    </div>

    <n-tabs type="line" v-model:value="activeCategory">
      <n-tab-pane v-for="cat in categories" :key="cat" :name="cat" :tab="cat">
        <n-data-table :columns="columns" :data="filteredExamples(cat)" :loading="examplesQuery.isLoading.value" size="small" />
      </n-tab-pane>
    </n-tabs>

    <n-modal v-model:show="showModal" preset="dialog" title="重要性样本" style="width: min(500px, 92vw);">
      <n-form>
        <n-form-item label="标题"><n-input v-model:value="form.title" /></n-form-item>
        <n-form-item label="摘要"><n-input v-model:value="form.summary" type="textarea" /></n-form-item>
        <n-form-item label="分类"><n-select v-model:value="form.category" :options="categoryOptions" /></n-form-item>
        <n-form-item label="重要"><n-switch v-model:value="form.is_important" /></n-form-item>
        <n-form-item label="理由"><n-input v-model:value="form.reason" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="handleSave" type="primary" :loading="saveMutation.isPending.value">保存</n-button>
      </template>
    </n-modal>

    <n-modal v-model:show="showBulkModal" preset="dialog" title="JSON 批量导入" style="width: min(600px, 94vw);">
      <n-input v-model:value="bulkJson" type="textarea" :rows="10" placeholder='[{"title":"...","category":"...","is_important":true}]' />
      <template #action>
        <n-button @click="handleBulkImport" type="primary" :loading="bulkMutation.isPending.value">导入</n-button>
      </template>
    </n-modal>

    <n-modal v-model:show="showCsvModal" preset="dialog" title="CSV 批量导入" style="width: min(700px, 96vw);">
      <div class="bulk-tip">表头：title,summary,category,is_important,reason（必填：title/category/is_important）</div>
      <div class="bulk-actions">
        <n-button size="small" @click="openCsvPicker">选择 CSV 文件</n-button>
        <n-button size="small" @click="downloadCsvTemplate">下载 CSV 模板</n-button>
      </div>
      <input ref="csvFileInput" class="csv-file-input" type="file" accept=".csv,text/csv" @change="handleCsvFileChange" />
      <n-input
        v-model:value="bulkCsv"
        type="textarea"
        :rows="10"
        placeholder="title,summary,category,is_important,reason&#10;示例标题,示例摘要,重大漏洞风险提示,true,已有在野利用"
      />
      <template #action>
        <n-button @click="handleCsvImport" type="primary" :loading="bulkMutation.isPending.value">导入</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSelect, NSwitch, NTabs, NTabPane, NTag, useMessage } from 'naive-ui'
import { fetchImportanceExamples, createImportanceExample, updateImportanceExample, deleteImportanceExample, bulkImportExamples } from '../../api/importance_examples'
import { NEWS_CATEGORIES } from '../../types/enums'
import { queryKeys } from '../../shared/query/keys'
import type { ImportanceExample } from '../../types'

const message = useMessage()
const queryClient = useQueryClient()

const showModal = ref(false)
const showBulkModal = ref(false)
const showCsvModal = ref(false)
const bulkJson = ref('')
const bulkCsv = ref('')
const csvFileInput = ref<HTMLInputElement | null>(null)
const form = ref<Partial<ImportanceExample>>({ is_important: false })
const activeCategory = ref(NEWS_CATEGORIES[0])

const categories = NEWS_CATEGORIES
const categoryOptions = NEWS_CATEGORIES.map(c => ({ label: c, value: c }))

const examplesQuery = useQuery({
  queryKey: queryKeys.importanceExamples.all(),
  queryFn: () => fetchImportanceExamples(),
})

const saveMutation = useMutation({
  mutationFn: (payload: Partial<ImportanceExample>) => {
    if (payload.id) return updateImportanceExample(payload.id, payload)
    return createImportanceExample(payload)
  },
  onSuccess: async () => {
    showModal.value = false
    form.value = { is_important: false }
    await queryClient.invalidateQueries({ queryKey: ['importance-examples', 'all'] })
    message.success('保存成功')
  },
  onError: () => {
    message.error('保存失败')
  },
})

const bulkMutation = useMutation({
  mutationFn: (items: Partial<ImportanceExample>[]) => bulkImportExamples(items),
  onSuccess: async (_data, variables) => {
    showBulkModal.value = false
    showCsvModal.value = false
    bulkJson.value = ''
    bulkCsv.value = ''
    await queryClient.invalidateQueries({ queryKey: ['importance-examples', 'all'] })
    message.success(`导入 ${variables.length} 条`)
  },
  onError: () => {
    message.error('导入失败，请检查导入内容')
  },
})

const deleteMutation = useMutation({
  mutationFn: deleteImportanceExample,
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: ['importance-examples', 'all'] })
    message.success('已删除')
  },
  onError: () => {
    message.error('删除失败')
  },
})

const examples = computed(() => examplesQuery.data.value ?? [])

function filteredExamples(cat: string) {
  return examples.value.filter(e => e.category === cat)
}

const columns = [
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  {
    title: '重要',
    key: 'is_important',
    width: 80,
    render(row: ImportanceExample) {
      return h(NTag, { type: row.is_important ? 'success' : 'default', size: 'small' }, { default: () => (row.is_important ? '是' : '否') })
    },
  },
  { title: '理由', key: 'reason', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render(row: ImportanceExample) {
      return h('div', { class: 'table-actions' }, [
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

async function handleSave() {
  await saveMutation.mutateAsync(form.value)
}

async function handleBulkImport() {
  try {
    const items = JSON.parse(bulkJson.value) as unknown
    if (!Array.isArray(items)) {
      message.error('导入失败，JSON 必须是数组')
      return
    }
    await bulkMutation.mutateAsync(items as Partial<ImportanceExample>[])
  } catch {
    message.error('导入失败，请检查 JSON 格式')
  }
}

function parseBooleanCell(value: string): boolean | null {
  const normalized = value.trim().toLowerCase()
  if (['true', '1', 'yes', 'y', '是'].includes(normalized)) return true
  if (['false', '0', 'no', 'n', '否'].includes(normalized)) return false
  return null
}

function parseCsvRows(content: string): { rows: string[][]; error?: string } {
  const rows: string[][] = []
  let row: string[] = []
  let cell = ''
  let inQuotes = false

  for (let index = 0; index < content.length; index += 1) {
    const char = content[index]

    if (char === '"') {
      if (inQuotes && content[index + 1] === '"') {
        cell += '"'
        index += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }

    if (char === ',' && !inQuotes) {
      row.push(cell)
      cell = ''
      continue
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && content[index + 1] === '\n') {
        index += 1
      }
      row.push(cell)
      rows.push(row)
      row = []
      cell = ''
      continue
    }

    cell += char
  }

  if (inQuotes) {
    return { rows: [], error: 'CSV 引号未闭合' }
  }

  row.push(cell)
  rows.push(row)
  return { rows }
}

function getCsvCell(row: string[], index: number | undefined): string {
  if (index === undefined || index < 0) return ''
  return (row[index] ?? '').trim()
}

function parseCsvExamples(content: string): { items: Partial<ImportanceExample>[]; error?: string } {
  const sanitized = content.replace(/^\uFEFF/, '').trim()
  if (!sanitized) {
    return { items: [], error: 'CSV 内容为空' }
  }

  const parsed = parseCsvRows(sanitized)
  if (parsed.error) {
    return { items: [], error: parsed.error }
  }

  const rows = parsed.rows.filter(row => row.some(cell => cell.trim() !== ''))
  if (rows.length < 2) {
    return { items: [], error: 'CSV 至少需要 1 行数据' }
  }

  const header = rows[0].map(cell => cell.trim().toLowerCase())
  const titleIndex = header.indexOf('title')
  const summaryIndex = header.indexOf('summary')
  const categoryIndex = header.indexOf('category')
  const importantIndex = header.indexOf('is_important')
  const reasonIndex = header.indexOf('reason')

  if (titleIndex < 0 || categoryIndex < 0 || importantIndex < 0) {
    return { items: [], error: '缺少必需表头：title/category/is_important' }
  }

  const categorySet = new Set<string>(categories)
  const items: Partial<ImportanceExample>[] = []

  for (let index = 1; index < rows.length; index += 1) {
    const row = rows[index]
    if (row.every(cell => cell.trim() === '')) continue

    const line = index + 1
    const title = getCsvCell(row, titleIndex)
    const category = getCsvCell(row, categoryIndex)
    const isImportantRaw = getCsvCell(row, importantIndex)
    const summary = getCsvCell(row, summaryIndex)
    const reason = getCsvCell(row, reasonIndex)

    if (!title) {
      return { items: [], error: `第 ${line} 行缺少 title` }
    }
    if (!category) {
      return { items: [], error: `第 ${line} 行缺少 category` }
    }
    if (!categorySet.has(category)) {
      return { items: [], error: `第 ${line} 行 category 不合法：${category}` }
    }

    const isImportant = parseBooleanCell(isImportantRaw)
    if (isImportant === null) {
      return { items: [], error: `第 ${line} 行 is_important 不合法：${isImportantRaw}` }
    }

    items.push({
      title,
      summary: summary || null,
      category,
      is_important: isImportant,
      reason: reason || null,
    })
  }

  if (!items.length) {
    return { items: [], error: 'CSV 没有可导入的数据' }
  }

  return { items }
}

function openCsvPicker() {
  csvFileInput.value?.click()
}

async function handleCsvFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    bulkCsv.value = await file.text()
    message.success(`已读取文件：${file.name}`)
  } catch {
    message.error('读取 CSV 失败')
  } finally {
    target.value = ''
  }
}

function downloadCsvTemplate() {
  const link = document.createElement('a')
  link.href = '/templates/importance-examples-template.csv'
  link.download = 'importance-examples-template.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

async function handleCsvImport() {
  const parsed = parseCsvExamples(bulkCsv.value)
  if (parsed.error) {
    message.error(`导入失败：${parsed.error}`)
    return
  }
  await bulkMutation.mutateAsync(parsed.items)
}
</script>

<style scoped>
.example-actions {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.table-actions {
  display: flex;
  gap: var(--space-2);
}

.bulk-tip {
  margin-bottom: var(--space-2);
  color: var(--text-color-2);
  font-size: 12px;
}

.bulk-actions {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.csv-file-input {
  display: none;
}

@media (max-width: 767px) {
  .example-actions {
    flex-direction: column;
  }

  .bulk-actions {
    flex-direction: column;
  }
}
</style>
