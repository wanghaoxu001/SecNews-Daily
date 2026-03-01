<template>
  <div class="llm-config">
    <n-spin :show="configsQuery.isLoading.value || cooldownQuery.isLoading.value">
      <n-card title="全局默认配置" size="small" class="llm-config__card">
        <n-form v-if="defaultConfig.id" label-placement="left" label-width="100" class="llm-config__form">
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
                <n-input-number v-model:value="defaultConfig.temperature" :min="0" :max="2" :step="0.1" class="llm-config__number-input" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="Max Tokens">
                <n-input-number v-model:value="defaultConfig.max_tokens" :min="0" class="llm-config__number-input" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="请求冷却(秒)">
                <n-input-number v-model:value="cooldownSeconds" :min="0" :step="0.5" :precision="1" class="llm-config__number-input" placeholder="0 表示无冷却" />
              </n-form-item>
            </n-gi>
          </n-grid>
          <div class="actions-row actions-row--end">
            <n-button type="primary" size="small" :loading="saveDefaultMutation.isPending.value" @click="saveDefault">保存全局配置</n-button>
            <n-button size="small" :loading="testingDefault" @click="testConfig('default')">测试连接</n-button>
          </div>
        </n-form>
      </n-card>

      <n-card title="任务配置" size="small">
        <template #header-extra>
          <n-text depth="3" class="llm-config__hint">留空则继承全局默认值</n-text>
        </template>
        <n-data-table :columns="columns" :data="taskConfigs" size="small" />
      </n-card>

      <n-modal v-model:show="showModal" preset="dialog" :title="`编辑 ${editForm.task_type} 配置`" :style="modalStyle">
        <n-form label-placement="left" label-width="100" class="llm-config__form">
          <n-form-item label="模型">
            <n-input v-model:value="editForm.model" :placeholder="defaultConfig.model || ''" />
          </n-form-item>
          <n-form-item label="Temperature">
            <n-input-number
              v-model:value="editForm.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              :placeholder="defaultConfig.temperature?.toString() || ''"
              class="llm-config__number-input"
            />
          </n-form-item>
          <n-form-item label="Max Tokens">
            <n-input-number
              v-model:value="editForm.max_tokens"
              :min="0"
              :placeholder="defaultConfig.max_tokens?.toString() || ''"
              class="llm-config__number-input"
            />
          </n-form-item>
          <n-form-item label="Base URL">
            <n-input v-model:value="editForm.base_url" :placeholder="defaultConfig.base_url || '留空继承全局'" />
          </n-form-item>
          <n-form-item label="API Key">
            <n-input
              v-model:value="editForm.api_key"
              type="password"
              show-password-on="click"
              :placeholder="'留空继承全局'"
            />
          </n-form-item>
        </n-form>
        <template #action>
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saveTaskMutation.isPending.value" @click="saveTaskConfig">保存</n-button>
        </template>
      </n-modal>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, reactive, watch } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NGrid,
  NGi,
  NInput,
  NInputNumber,
  NModal,
  NSpin,
  NText,
  NTag,
  NSpace,
  useMessage,
} from 'naive-ui'
import { ensureLlmDefaults, updateLlmConfig, testLlmConfig, getLlmCooldown, setLlmCooldown } from '../../api/llm_configs'
import { queryKeys } from '../../shared/query/keys'
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
const queryClient = useQueryClient()

const showModal = ref(false)
const testingDefault = ref(false)
const testingTaskType = ref<string | null>(null)
const allConfigs = ref<LlmConfig[]>([])
const cooldownSeconds = ref<number>(0)
const defaultConfig = reactive<Partial<LlmConfig>>({})
const editForm = ref<Partial<LlmConfig>>({})
const modalStyle = {
  width: 'min(480px, 92vw)',
}

const configsQuery = useQuery({
  queryKey: queryKeys.llmConfigs.all,
  queryFn: ensureLlmDefaults,
})

const cooldownQuery = useQuery({
  queryKey: queryKeys.llmConfigs.cooldown,
  queryFn: getLlmCooldown,
})

watch(
  () => configsQuery.data.value,
  (configs) => {
    if (!configs) return
    allConfigs.value = configs
    const cfg = configs.find(c => c.task_type === 'default')
    if (cfg) {
      Object.assign(defaultConfig, cfg)
    }
  },
  { immediate: true }
)

watch(
  () => cooldownQuery.data.value,
  (cooldown) => {
    if (cooldown == null) return
    cooldownSeconds.value = cooldown
  },
  { immediate: true }
)

const taskConfigs = computed(() =>
  allConfigs.value
    .filter(c => c.task_type !== 'default')
    .sort((a, b) => {
      const order = ['translate', 'summarize', 'classify', 'similarity', 'importance', 'embedding']
      return order.indexOf(a.task_type) - order.indexOf(b.task_type)
    })
)

const saveDefaultMutation = useMutation({
  mutationFn: async () => {
    if (!defaultConfig.id) return
    await updateLlmConfig(defaultConfig.id, {
      base_url: defaultConfig.base_url,
      api_key: defaultConfig.api_key,
      model: defaultConfig.model,
      temperature: defaultConfig.temperature,
      max_tokens: defaultConfig.max_tokens,
    })
    await setLlmCooldown(cooldownSeconds.value ?? 0)
  },
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.llmConfigs.all })
    await queryClient.invalidateQueries({ queryKey: queryKeys.llmConfigs.cooldown })
    message.success('全局配置已保存')
  },
  onError: () => {
    message.error('保存失败')
  },
})

const saveTaskMutation = useMutation({
  mutationFn: async (payload: Partial<LlmConfig>) => {
    if (!payload.id) return
    await updateLlmConfig(payload.id, {
      model: payload.model || null,
      temperature: payload.temperature ?? null,
      max_tokens: payload.max_tokens ?? null,
      base_url: payload.base_url || null,
      api_key: payload.api_key || null,
    })
  },
  onSuccess: async () => {
    showModal.value = false
    await queryClient.invalidateQueries({ queryKey: queryKeys.llmConfigs.all })
    message.success('配置已保存')
  },
  onError: () => {
    message.error('保存失败')
  },
})

const columns = [
  {
    title: '任务类型',
    key: 'task_type',
    width: 170,
    render(row: LlmConfig) {
      return h('span', {}, [
        h(NTag, { size: 'small', bordered: false, type: 'info' }, { default: () => row.task_type }),
        h('span', { class: 'llm-config__task-desc' }, TASK_TYPE_LABELS[row.task_type] || ''),
      ])
    },
  },
  {
    title: '模型',
    key: 'model',
    ellipsis: { tooltip: true },
    render: (row: LlmConfig) => row.model || h(NText, { depth: 3 }, { default: () => '继承全局' }),
  },
  {
    title: 'Temperature',
    key: 'temperature',
    width: 110,
    render: (row: LlmConfig) =>
      row.temperature != null
        ? String(row.temperature)
        : h(NText, { depth: 3 }, { default: () => '继承全局' }),
  },
  {
    title: 'Max Tokens',
    key: 'max_tokens',
    width: 110,
    render: (row: LlmConfig) =>
      row.max_tokens != null
        ? String(row.max_tokens)
        : h(NText, { depth: 3 }, { default: () => '继承全局' }),
  },
  {
    title: 'Base URL',
    key: 'base_url',
    width: 120,
    ellipsis: { tooltip: true },
    render: (row: LlmConfig) => row.base_url || h(NText, { depth: 3 }, { default: () => '继承全局' }),
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render(row: LlmConfig) {
      return h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: 'tiny', onClick: () => openEdit(row) }, { default: () => '编辑' }),
          h(NButton, {
            size: 'tiny',
            loading: testingTaskType.value === row.task_type,
            onClick: () => testConfig(row.task_type),
          }, { default: () => '测试' }),
        ],
      })
    },
  },
]

async function saveDefault() {
  await saveDefaultMutation.mutateAsync()
}

function openEdit(row: LlmConfig) {
  editForm.value = { ...row }
  showModal.value = true
}

async function saveTaskConfig() {
  await saveTaskMutation.mutateAsync(editForm.value)
}

async function testConfig(taskType: string) {
  if (taskType === 'default') {
    testingDefault.value = true
  } else {
    testingTaskType.value = taskType
  }

  try {
    const result = await testLlmConfig(taskType)
    if (result.success) {
      message.success(`连接成功（${result.latency_ms}ms）`)
    } else {
      message.error(`测试失败: ${result.message}（${result.latency_ms}ms）`)
    }
  } catch {
    message.error('测试请求失败')
  } finally {
    testingDefault.value = false
    testingTaskType.value = null
  }
}
</script>

<style scoped>
.llm-config {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.llm-config__card {
  margin-bottom: var(--space-4);
}

.llm-config__hint {
  font-size: 12px;
}

.llm-config__number-input {
  width: 100%;
}

.llm-config__task-desc {
  margin-left: 8px;
  color: var(--color-text-tertiary);
  font-size: 12px;
}

@media (max-width: 767px) {
  .llm-config__card {
    margin-bottom: var(--space-3);
  }
}
</style>
