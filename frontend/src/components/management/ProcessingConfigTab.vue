<template>
  <div>
    <n-button @click="showModal = true" size="small" style="margin-bottom: 12px;">添加参数</n-button>
    <n-data-table :columns="columns" :data="configs" :loading="loading" size="small" />

    <n-modal v-model:show="showModal" preset="dialog" title="处理参数" style="width: 500px;">
      <n-form>
        <n-form-item label="Key"><n-input v-model:value="form.key" :disabled="!!form.id" /></n-form-item>
        <n-form-item label="Value"><n-input v-model:value="form.value" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="form.description" type="textarea" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="handleSave" type="primary" :loading="saving">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, useMessage } from 'naive-ui'
import { fetchProcessingConfigs, createProcessingConfig, updateProcessingConfig, deleteProcessingConfig } from '../../api/processing_configs'
import type { ProcessingConfig } from '../../types'

const message = useMessage()
const configs = ref<ProcessingConfig[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const form = ref<Partial<ProcessingConfig>>({})

const columns = [
  { title: 'Key', key: 'key', width: 200 },
  { title: 'Value', key: 'value', width: 200 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '操作', key: 'actions', width: 140,
    render(row: ProcessingConfig) {
      return h('div', { style: 'display:flex;gap:8px' }, [
        h(NButton, { size: 'tiny', onClick: () => { form.value = { ...row }; showModal.value = true } }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', type: 'error', onClick: () => handleDelete(row.id) }, { default: () => '删除' }),
      ])
    },
  },
]

async function loadData() {
  loading.value = true
  try { configs.value = await fetchProcessingConfigs() } finally { loading.value = false }
}

async function handleSave() {
  saving.value = true
  try {
    if (form.value.id) { await updateProcessingConfig(form.value.id, form.value) }
    else { await createProcessingConfig(form.value) }
    showModal.value = false; form.value = {}; await loadData(); message.success('保存成功')
  } catch { message.error('保存失败') } finally { saving.value = false }
}

async function handleDelete(id: number) {
  try { await deleteProcessingConfig(id); await loadData(); message.success('已删除') } catch { message.error('删除失败') }
}

onMounted(loadData)
</script>
