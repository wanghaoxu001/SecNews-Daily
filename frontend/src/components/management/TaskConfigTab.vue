<template>
  <div>
    <n-button @click="openCreate" size="small" style="margin-bottom: var(--space-3);">添加定时任务</n-button>
    <n-data-table :columns="columns" :data="configs" :loading="configsQuery.isLoading.value" size="small" />

    <n-modal v-model:show="showModal" preset="dialog" title="定时任务" style="width: min(500px, 92vw);">
      <n-form>
        <n-form-item label="名称"><n-input v-model:value="form.name" :disabled="!!form.id" /></n-form-item>
        <n-form-item label="Cron 表达式"><n-input v-model:value="form.cron_expression" placeholder="0 */2 * * *" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="form.description" /></n-form-item>
        <n-form-item label="启用"><n-switch v-model:value="form.enabled" /></n-form-item>
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
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSwitch, NTag, useMessage } from 'naive-ui'
import { fetchTaskConfigs, createTaskConfig, updateTaskConfig, deleteTaskConfig } from '../../api/task_configs'
import { queryKeys } from '../../shared/query/keys'
import type { TaskConfig } from '../../types'

const message = useMessage()
const queryClient = useQueryClient()

const showModal = ref(false)
const form = ref<Partial<TaskConfig>>({ enabled: true })

const configsQuery = useQuery({
  queryKey: queryKeys.taskConfigs.all,
  queryFn: fetchTaskConfigs,
})

const saveMutation = useMutation({
  mutationFn: (payload: Partial<TaskConfig>) => {
    if (payload.id) return updateTaskConfig(payload.id, payload)
    return createTaskConfig(payload)
  },
  onSuccess: async () => {
    showModal.value = false
    form.value = { enabled: true }
    await queryClient.invalidateQueries({ queryKey: queryKeys.taskConfigs.all })
    message.success('保存成功')
  },
  onError: () => {
    message.error('保存失败')
  },
})

const deleteMutation = useMutation({
  mutationFn: deleteTaskConfig,
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.taskConfigs.all })
    message.success('已删除')
  },
  onError: () => {
    message.error('删除失败')
  },
})

const configs = computed(() => configsQuery.data.value ?? [])

const columns = [
  { title: '名称', key: 'name', width: 150 },
  { title: 'Cron', key: 'cron_expression', width: 150 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '状态',
    key: 'enabled',
    width: 80,
    render(row: TaskConfig) {
      return h(NTag, { type: row.enabled ? 'success' : 'default', size: 'small' }, { default: () => (row.enabled ? '启用' : '禁用') })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render(row: TaskConfig) {
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
  form.value = { enabled: true }
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
