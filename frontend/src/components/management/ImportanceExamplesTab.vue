<template>
  <div>
    <div class="example-actions">
      <n-button @click="showModal = true" size="small">添加样本</n-button>
      <n-button @click="showBulkModal = true" size="small">JSON 批量导入</n-button>
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
const bulkJson = ref('')
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
    bulkJson.value = ''
    await queryClient.invalidateQueries({ queryKey: ['importance-examples', 'all'] })
    message.success(`导入 ${variables.length} 条`)
  },
  onError: () => {
    message.error('导入失败，请检查 JSON 格式')
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
    const items = JSON.parse(bulkJson.value)
    await bulkMutation.mutateAsync(items)
  } catch {
    message.error('导入失败，请检查 JSON 格式')
  }
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

@media (max-width: 767px) {
  .example-actions {
    flex-direction: column;
  }
}
</style>
