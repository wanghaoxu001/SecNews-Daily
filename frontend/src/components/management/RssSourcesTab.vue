<template>
  <div>
    <n-button @click="showModal = true" size="small" style="margin-bottom: 12px;">添加 RSS 源</n-button>
    <n-data-table :columns="columns" :data="sources" :loading="loading" size="small" />

    <n-modal v-model:show="showModal" preset="dialog" title="RSS 源" style="width: 500px;">
      <n-form>
        <n-form-item label="名称"><n-input v-model:value="form.name" /></n-form-item>
        <n-form-item label="URL"><n-input v-model:value="form.url" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="form.description" type="textarea" /></n-form-item>
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
import { fetchRssSources, createRssSource, updateRssSource, deleteRssSource } from '../../api/rss_sources'
import type { RssSource } from '../../types'

const message = useMessage()
const sources = ref<RssSource[]>([])
const loading = ref(false)
const saving = ref(false)
const showModal = ref(false)
const form = ref<Partial<RssSource>>({ enabled: true })

const columns = [
  { title: '名称', key: 'name', width: 150 },
  { title: 'URL', key: 'url', ellipsis: { tooltip: true } },
  {
    title: '状态', key: 'enabled', width: 80,
    render(row: RssSource) {
      return h(NTag, { type: row.enabled ? 'success' : 'default', size: 'small' }, { default: () => row.enabled ? '启用' : '禁用' })
    },
  },
  {
    title: '操作', key: 'actions', width: 140,
    render(row: RssSource) {
      return h('div', { style: 'display:flex;gap:8px' }, [
        h(NButton, { size: 'tiny', onClick: () => { form.value = { ...row }; showModal.value = true } }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', type: 'error', onClick: () => handleDelete(row.id) }, { default: () => '删除' }),
      ])
    },
  },
]

async function loadData() {
  loading.value = true
  try { sources.value = await fetchRssSources() } finally { loading.value = false }
}

async function handleSave() {
  saving.value = true
  try {
    if (form.value.id) { await updateRssSource(form.value.id, form.value) }
    else { await createRssSource(form.value) }
    showModal.value = false; form.value = { enabled: true }; await loadData(); message.success('保存成功')
  } catch { message.error('保存失败') } finally { saving.value = false }
}

async function handleDelete(id: number) {
  try { await deleteRssSource(id); await loadData(); message.success('已删除') } catch { message.error('删除失败') }
}

onMounted(loadData)
</script>
