<template>
  <AppLayout>
    <div style="max-width: 900px; margin: 0 auto;">
      <n-spin :show="loading">
        <template v-if="briefing">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <n-input v-model:value="briefing.title" style="max-width: 400px; font-size: 18px; font-weight: bold;" />
            <n-space>
              <n-button @click="handleSave" type="primary" :loading="saving">保存</n-button>
              <n-button disabled title="PDF 导出（开发中）">导出 PDF</n-button>
            </n-space>
          </div>

          <div v-for="group in categoryGroups" :key="group.category" style="margin-bottom: 24px;">
            <h3 style="border-bottom: 2px solid #18a058; padding-bottom: 4px;">{{ group.category }}</h3>
            <div v-for="item in group.items" :key="item.id" style="margin-bottom: 12px; padding: 12px; border: 1px solid #eee; border-radius: 4px;">
              <n-input v-model:value="item.title" placeholder="标题" style="margin-bottom: 8px; font-weight: 600;" />
              <n-input v-model:value="item.summary" type="textarea" placeholder="摘要" :rows="2" />
              <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                <n-select v-model:value="item.category" :options="categoryOptions" size="small" style="width: 200px;" />
                <n-button size="small" type="error" @click="handleDeleteItem(item.id)">删除</n-button>
              </div>
            </div>
          </div>
        </template>
      </n-spin>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NInput, NButton, NSpace, NSelect, NSpin, useMessage } from 'naive-ui'
import AppLayout from '../components/layout/AppLayout.vue'
import { fetchBriefing, updateBriefing, updateBriefingItem, deleteBriefingItem } from '../api/briefings'
import { NEWS_CATEGORIES } from '../types/enums'
import type { Briefing, BriefingItem } from '../types'

const route = useRoute()
const message = useMessage()

const briefing = ref<Briefing | null>(null)
const loading = ref(false)
const saving = ref(false)

const categoryOptions = NEWS_CATEGORIES.map(c => ({ label: c, value: c }))

const categoryGroups = computed(() => {
  if (!briefing.value) return []
  const groups: Record<string, BriefingItem[]> = {}
  for (const item of briefing.value.items) {
    const cat = item.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(item)
  }
  return NEWS_CATEGORIES
    .filter(c => groups[c])
    .map(c => ({ category: c, items: groups[c] }))
})

async function loadBriefing() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    briefing.value = await fetchBriefing(id)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!briefing.value) return
  saving.value = true
  try {
    await updateBriefing(briefing.value.id, { title: briefing.value.title })
    for (const item of briefing.value.items) {
      await updateBriefingItem(item.id, {
        title: item.title,
        summary: item.summary,
        category: item.category,
      })
    }
    message.success('保存成功')
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDeleteItem(itemId: number) {
  try {
    await deleteBriefingItem(itemId)
    if (briefing.value) {
      briefing.value.items = briefing.value.items.filter(i => i.id !== itemId)
    }
    message.success('已删除')
  } catch {
    message.error('删除失败')
  }
}

onMounted(loadBriefing)
</script>
