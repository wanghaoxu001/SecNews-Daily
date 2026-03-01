<template>
  <div>
    <div style="display: flex; gap: 12px; margin-bottom: 12px;">
      <n-button @click="showModal = true" size="small">添加样本</n-button>
      <n-button @click="showBulkModal = true" size="small">JSON 批量导入</n-button>
    </div>

    <n-tabs type="line" v-model:value="activeCategory">
      <n-tab-pane v-for="cat in categories" :key="cat" :name="cat" :tab="cat">
        <n-data-table :columns="columns" :data="filteredExamples(cat)" :loading="loading" size="small" />
      </n-tab-pane>
    </n-tabs>

    <n-modal v-model:show="showModal" preset="dialog" title="重要性样本" style="width: 500px;">
      <n-form>
        <n-form-item label="标题"><n-input v-model:value="form.title" /></n-form-item>
        <n-form-item label="摘要"><n-input v-model:value="form.summary" type="textarea" /></n-form-item>
        <n-form-item label="分类"><n-select v-model:value="form.category" :options="categoryOptions" /></n-form-item>
        <n-form-item label="重要"><n-switch v-model:value="form.is_important" /></n-form-item>
        <n-form-item label="理由"><n-input v-model:value="form.reason" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="handleSave" type="primary" :loading="saving">保存</n-button>
      </template>
    </n-modal>

    <n-modal v-model:show="showBulkModal" preset="dialog" title="JSON 批量导入" style="width: 600px;">
      <n-input v-model:value="bulkJson" type="textarea" :rows="10" placeholder='[{"title":"...","category":"...","is_important":true}]' />
      <template #action>
        <n-button @click="handleBulkImport" type="primary" :loading="saving">导入</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSelect, NSwitch, NTabs, NTabPane, NTag, useMessage } from 'naive-ui'
import { fetchImportanceExamples, createImportanceExample, updateImportanceExample, deleteImportanceExample, bulkImportExamples } from '../../api/importance_examples'
import { NEWS_CATEGORIES } from '../../types/enums'
import type { ImportanceExample } from '../../types'

const message = useMessage()
const examples = ref<ImportanceExample[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const showBulkModal = ref(false)
const bulkJson = ref('')
const form = ref<Partial<ImportanceExample>>({ is_important: false })
const activeCategory = ref(NEWS_CATEGORIES[0])

const categories = NEWS_CATEGORIES
const categoryOptions = NEWS_CATEGORIES.map(c => ({ label: c, value: c }))

function filteredExamples(cat: string) {
  return examples.value.filter(e => e.category === cat)
}

const columns = [
  { title: '标题', key: 'title', ellipsis: { tooltip: true } },
  {
    title: '重要', key: 'is_important', width: 80,
    render(row: ImportanceExample) {
      return h(NTag, { type: row.is_important ? 'success' : 'default', size: 'small' }, { default: () => row.is_important ? '是' : '否' })
    },
  },
  { title: '理由', key: 'reason', ellipsis: { tooltip: true } },
  {
    title: '操作', key: 'actions', width: 140,
    render(row: ImportanceExample) {
      return h('div', { style: 'display:flex;gap:8px' }, [
        h(NButton, { size: 'tiny', onClick: () => { form.value = { ...row }; showModal.value = true } }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', type: 'error', onClick: () => handleDelete(row.id) }, { default: () => '删除' }),
      ])
    },
  },
]

async function loadData() {
  loading.value = true
  try { examples.value = await fetchImportanceExamples() } finally { loading.value = false }
}

async function handleSave() {
  saving.value = true
  try {
    if (form.value.id) { await updateImportanceExample(form.value.id, form.value) }
    else { await createImportanceExample(form.value) }
    showModal.value = false; form.value = { is_important: false }; await loadData(); message.success('保存成功')
  } catch { message.error('保存失败') } finally { saving.value = false }
}

async function handleBulkImport() {
  saving.value = true
  try {
    const items = JSON.parse(bulkJson.value)
    await bulkImportExamples(items)
    showBulkModal.value = false; bulkJson.value = ''; await loadData(); message.success(`导入 ${items.length} 条`)
  } catch { message.error('导入失败，请检查 JSON 格式') } finally { saving.value = false }
}

async function handleDelete(id: number) {
  try { await deleteImportanceExample(id); await loadData(); message.success('已删除') } catch { message.error('删除失败') }
}

onMounted(loadData)
</script>
