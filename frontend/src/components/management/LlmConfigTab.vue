<template>
  <div>
    <n-button @click="showModal = true" size="small" style="margin-bottom: 12px;">添加配置</n-button>
    <n-data-table :columns="columns" :data="configs" :loading="loading" size="small" />

    <n-modal v-model:show="showModal" preset="dialog" title="LLM 配置" style="width: 500px;">
      <n-form>
        <n-form-item label="任务类型">
          <n-input v-model:value="form.task_type" :disabled="!!form.id" />
        </n-form-item>
        <n-form-item label="Base URL">
          <n-input v-model:value="form.base_url" />
        </n-form-item>
        <n-form-item label="API Key">
          <n-input v-model:value="form.api_key" type="password" />
        </n-form-item>
        <n-form-item label="模型">
          <n-input v-model:value="form.model" />
        </n-form-item>
        <n-form-item label="Temperature">
          <n-input-number v-model:value="form.temperature" :min="0" :max="2" :step="0.1" />
        </n-form-item>
        <n-form-item label="Max Tokens">
          <n-input-number v-model:value="form.max_tokens" :min="0" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="handleSave" type="primary" :loading="saving">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, NInputNumber, useMessage } from 'naive-ui'
import { fetchLlmConfigs, createLlmConfig, updateLlmConfig, deleteLlmConfig } from '../../api/llm_configs'
import type { LlmConfig } from '../../types'

const message = useMessage()
const configs = ref<LlmConfig[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)

const form = ref<Partial<LlmConfig>>({})

const columns = [
  { title: '任务类型', key: 'task_type', width: 120 },
  { title: 'Base URL', key: 'base_url', ellipsis: { tooltip: true } },
  { title: '模型', key: 'model', width: 150 },
  { title: 'Temperature', key: 'temperature', width: 100 },
  { title: 'Max Tokens', key: 'max_tokens', width: 100 },
  {
    title: '操作', key: 'actions', width: 140,
    render(row: LlmConfig) {
      return h('div', { style: 'display:flex;gap:8px' }, [
        h(NButton, { size: 'tiny', onClick: () => editRow(row) }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', type: 'error', onClick: () => handleDelete(row.id) }, { default: () => '删除' }),
      ])
    },
  },
]

async function loadData() {
  loading.value = true
  try { configs.value = await fetchLlmConfigs() } finally { loading.value = false }
}

function editRow(row: LlmConfig) {
  form.value = { ...row }
  showModal.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (form.value.id) {
      await updateLlmConfig(form.value.id, form.value)
    } else {
      await createLlmConfig(form.value)
    }
    showModal.value = false
    form.value = {}
    await loadData()
    message.success('保存成功')
  } catch { message.error('保存失败') } finally { saving.value = false }
}

async function handleDelete(id: number) {
  try { await deleteLlmConfig(id); await loadData(); message.success('已删除') } catch { message.error('删除失败') }
}

onMounted(loadData)
</script>
