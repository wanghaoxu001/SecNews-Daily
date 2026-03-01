<template>
  <div>
    <n-button @click="showModal = true" size="small" style="margin-bottom: 12px;">添加定时任务</n-button>
    <n-data-table :columns="columns" :data="configs" :loading="loading" size="small" />

    <n-modal v-model:show="showModal" preset="dialog" title="定时任务" style="width: 500px;">
      <n-form>
        <n-form-item label="名称"><n-input v-model:value="form.name" :disabled="!!form.id" /></n-form-item>
        <n-form-item label="Cron 表达式"><n-input v-model:value="form.cron_expression" placeholder="0 */2 * * *" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="form.description" /></n-form-item>
        <n-form-item label="启用"><n-switch v-model:value="form.enabled" /></n-form-item>
      </n-form>
      <template #action>
        <n-button @click="handleSave" type="primary" :loading="saving">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { NButton, NDataTable, NModal, NForm, NFormItem, NInput, NSwitch, NTag, useMessage } from 'naive-ui'
import { fetchTaskConfigs, createTaskConfig, updateTaskConfig, deleteTaskConfig } from '../../api/task_configs'
import type { TaskConfig } from '../../types'

const message = useMessage()
const configs = ref<TaskConfig[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const form = ref<Partial<TaskConfig>>({ enabled: true })

const columns = [
  { title: '名称', key: 'name', width: 150 },
  { title: 'Cron', key: 'cron_expression', width: 150 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '状态', key: 'enabled', width: 80,
    render(row: TaskConfig) {
      return h(NTag, { type: row.enabled ? 'success' : 'default', size: 'small' }, { default: () => row.enabled ? '启用' : '禁用' })
    },
  },
  {
    title: '操作', key: 'actions', width: 140,
    render(row: TaskConfig) {
      return h('div', { style: 'display:flex;gap:8px' }, [
        h(NButton, { size: 'tiny', onClick: () => { form.value = { ...row }; showModal.value = true } }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', type: 'error', onClick: () => handleDelete(row.id) }, { default: () => '删除' }),
      ])
    },
  },
]

async function loadData() {
  loading.value = true
  try { configs.value = await fetchTaskConfigs() } finally { loading.value = false }
}

async function handleSave() {
  saving.value = true
  try {
    if (form.value.id) { await updateTaskConfig(form.value.id, form.value) }
    else { await createTaskConfig(form.value) }
    showModal.value = false; form.value = { enabled: true }; await loadData(); message.success('保存成功')
  } catch { message.error('保存失败') } finally { saving.value = false }
}

async function handleDelete(id: number) {
  try { await deleteTaskConfig(id); await loadData(); message.success('已删除') } catch { message.error('删除失败') }
}

onMounted(loadData)
</script>
