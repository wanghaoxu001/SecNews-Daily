<template>
  <div>
    <n-button @click="openCreate" size="small" style="margin-bottom: var(--space-3);">添加参数</n-button>
    <n-data-table :columns="columns" :data="configs" :loading="configsQuery.isLoading.value" size="small" />

    <n-modal v-model:show="showModal" preset="dialog" title="处理参数" style="width: min(500px, 92vw);">
      <n-form>
        <n-form-item label="Key"><n-input v-model:value="form.key" :disabled="!!form.id" /></n-form-item>
        <n-form-item label="Value"><n-input v-model:value="form.value" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="form.description" type="textarea" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="handleSave" type="primary" :loading="saveMutation.isPending.value">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, useMessage } from 'naive-ui'
import { fetchProcessingConfigs, createProcessingConfig, updateProcessingConfig, deleteProcessingConfig } from '../../api/processing_configs'
import { queryKeys } from '../../shared/query/keys'
import type { ProcessingConfig } from '../../types'

const message = useMessage()
const queryClient = useQueryClient()

const showModal = ref(false)
const form = ref<Partial<ProcessingConfig>>({})

const configsQuery = useQuery({
  queryKey: queryKeys.processingConfigs.all,
  queryFn: fetchProcessingConfigs,
})

const saveMutation = useMutation({
  mutationFn: (payload: Partial<ProcessingConfig>) => {
    if (payload.id) return updateProcessingConfig(payload.id, payload)
    return createProcessingConfig(payload)
  },
  onSuccess: async () => {
    showModal.value = false
    form.value = {}
    await queryClient.invalidateQueries({ queryKey: queryKeys.processingConfigs.all })
    message.success('保存成功')
  },
  onError: () => {
    message.error('保存失败')
  },
})

const deleteMutation = useMutation({
  mutationFn: deleteProcessingConfig,
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.processingConfigs.all })
    message.success('已删除')
  },
  onError: () => {
    message.error('删除失败')
  },
})

const configs = computed(() => configsQuery.data.value ?? [])

const columns = [
  { title: 'Key', key: 'key', width: 200 },
  { title: 'Value', key: 'value', width: 200 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render(row: ProcessingConfig) {
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

function openCreate() {
  form.value = {}
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
</style>
