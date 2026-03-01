<template>
  <n-spin :show="loading">
    <!-- Global default config -->
    <n-card title="全局默认配置" size="small" style="margin-bottom: 16px;">
      <n-form v-if="defaultConfig" label-placement="left" label-width="100">
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="Base URL">
              <n-input v-model:value="defaultConfig.base_url" placeholder="http://localhost:11434" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="API Key">
              <n-input v-model:value="defaultConfig.api_key" type="password" show-password-on="click" placeholder="sk-..." />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="默认模型">
              <n-input v-model:value="defaultConfig.model" placeholder="gpt-4o-mini" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="Temperature">
              <n-input-number v-model:value="defaultConfig.temperature" :min="0" :max="2" :step="0.1" style="width: 100%;" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="Max Tokens">
              <n-input-number v-model:value="defaultConfig.max_tokens" :min="0" style="width: 100%;" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <div style="text-align: right;">
          <n-button type="primary" size="small" :loading="savingDefault" @click="saveDefault">保存全局配置</n-button>
        </div>
      </n-form>
    </n-card>

    <!-- Task-specific configs -->
    <n-card title="任务配置" size="small">
      <template #header-extra>
        <n-text depth="3" style="font-size: 12px;">留空则继承全局默认值</n-text>
      </template>
      <n-data-table :columns="columns" :data="taskConfigs" size="small" />
    </n-card>

    <!-- Edit modal for task config -->
    <n-modal v-model:show="showModal" preset="dialog" :title="`编辑 ${editForm.task_type} 配置`" style="width: 480px;">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="模型">
          <n-input v-model:value="editForm.model" :placeholder="defaultConfig?.model || ''" />
        </n-form-item>
        <n-form-item label="Temperature">
          <n-input-number v-model:value="editForm.temperature" :min="0" :max="2" :step="0.1"
            :placeholder="defaultConfig?.temperature?.toString() || ''" style="width: 100%;" />
        </n-form-item>
        <n-form-item label="Max Tokens">
          <n-input-number v-model:value="editForm.max_tokens" :min="0"
            :placeholder="defaultConfig?.max_tokens?.toString() || ''" style="width: 100%;" />
        </n-form-item>
        <n-form-item label="Base URL">
          <n-input v-model:value="editForm.base_url" :placeholder="defaultConfig?.base_url || '留空继承全局'" />
        </n-form-item>
        <n-form-item label="API Key">
          <n-input v-model:value="editForm.api_key" type="password" show-password-on="click"
            :placeholder="'留空继承全局'" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showModal = false" style="margin-right: 8px;">取消</n-button>
        <n-button type="primary" :loading="savingTask" @click="saveTaskConfig">保存</n-button>
      </template>
    </n-modal>
  </n-spin>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NButton, NCard, NDataTable, NForm, NFormItem, NGrid, NGi,
  NInput, NInputNumber, NModal, NSpin, NText, NTag,
  useMessage,
} from 'naive-ui'
import { ensureLlmDefaults, updateLlmConfig } from '../../api/llm_configs'
import type { LlmConfig } from '../../types'

const TASK_TYPE_LABELS: Record<string, string> = {
  translate: '翻译',
  summarize: '摘要',
  classify: '分类',
  similarity: '相似性判断',
  importance: '重要性判断',
  embedding: '向量生成',
}

const message = useMessage()
const loading = ref(false)
const savingDefault = ref(false)
const savingTask = ref(false)
const showModal = ref(false)

const allConfigs = ref<LlmConfig[]>([])

const defaultConfig = computed(() => {
  const cfg = allConfigs.value.find(c => c.task_type === 'default')
  return cfg ? { ...cfg } : null
})

const taskConfigs = computed(() =>
  allConfigs.value
    .filter(c => c.task_type !== 'default')
    .sort((a, b) => {
      const order = ['translate', 'summarize', 'classify', 'similarity', 'importance', 'embedding']
      return order.indexOf(a.task_type) - order.indexOf(b.task_type)
    })
)

const editForm = ref<Partial<LlmConfig>>({})

const columns = [
  {
    title: '任务类型',
    key: 'task_type',
    width: 140,
    render(row: LlmConfig) {
      return h('span', {}, [
        h(NTag, { size: 'small', bordered: false, type: 'info' }, { default: () => row.task_type }),
        h('span', { style: 'margin-left: 8px; color: #666; font-size: 12px;' }, TASK_TYPE_LABELS[row.task_type] || ''),
      ])
    },
  },
  { title: '模型', key: 'model', ellipsis: { tooltip: true }, render: (row: LlmConfig) => row.model || h(NText, { depth: 3 }, { default: () => '继承全局' }) },
  { title: 'Temperature', key: 'temperature', width: 110, render: (row: LlmConfig) => row.temperature != null ? String(row.temperature) : h(NText, { depth: 3 }, { default: () => '继承全局' }) },
  { title: 'Max Tokens', key: 'max_tokens', width: 110, render: (row: LlmConfig) => row.max_tokens != null ? String(row.max_tokens) : h(NText, { depth: 3 }, { default: () => '继承全局' }) },
  { title: 'Base URL', key: 'base_url', width: 120, ellipsis: { tooltip: true }, render: (row: LlmConfig) => row.base_url || h(NText, { depth: 3 }, { default: () => '继承全局' }) },
  {
    title: '操作', key: 'actions', width: 80,
    render(row: LlmConfig) {
      return h(NButton, { size: 'tiny', onClick: () => openEdit(row) }, { default: () => '编辑' })
    },
  },
]

async function loadData() {
  loading.value = true
  try {
    allConfigs.value = await ensureLlmDefaults()
  } finally {
    loading.value = false
  }
}

async function saveDefault() {
  if (!defaultConfig.value?.id) return
  savingDefault.value = true
  try {
    await updateLlmConfig(defaultConfig.value.id, {
      base_url: defaultConfig.value.base_url,
      api_key: defaultConfig.value.api_key,
      model: defaultConfig.value.model,
      temperature: defaultConfig.value.temperature,
      max_tokens: defaultConfig.value.max_tokens,
    })
    await loadData()
    message.success('全局配置已保存')
  } catch {
    message.error('保存失败')
  } finally {
    savingDefault.value = false
  }
}

function openEdit(row: LlmConfig) {
  editForm.value = { ...row }
  showModal.value = true
}

async function saveTaskConfig() {
  if (!editForm.value.id) return
  savingTask.value = true
  try {
    await updateLlmConfig(editForm.value.id, {
      model: editForm.value.model || null,
      temperature: editForm.value.temperature ?? null,
      max_tokens: editForm.value.max_tokens ?? null,
      base_url: editForm.value.base_url || null,
      api_key: editForm.value.api_key || null,
    })
    showModal.value = false
    await loadData()
    message.success('配置已保存')
  } catch {
    message.error('保存失败')
  } finally {
    savingTask.value = false
  }
}

onMounted(loadData)
</script>
