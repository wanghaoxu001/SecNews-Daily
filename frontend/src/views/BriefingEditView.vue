<template>
  <AppLayout>
    <section class="page-container">
      <n-spin :show="briefingQuery.isLoading.value">
        <template v-if="briefing">
          <div class="briefing-edit__header">
            <n-input v-model:value="briefing.title" class="briefing-edit__title-input" />
            <n-space>
              <n-button @click="handleSave" type="primary" :loading="savingMutation.isPending.value">保存</n-button>
              <n-button disabled title="PDF 导出（开发中）">导出 PDF</n-button>
            </n-space>
          </div>

          <section v-for="group in categoryGroups" :key="group.category" class="briefing-edit__group">
            <h3 class="briefing-edit__group-title">{{ group.category }}</h3>
            <article v-for="item in group.items" :key="item.id" class="briefing-edit__item surface-card">
              <n-input v-model:value="item.title" placeholder="标题" class="briefing-edit__item-title" />
              <n-input v-model:value="item.summary" type="textarea" placeholder="摘要" :rows="2" />
              <div class="briefing-edit__item-actions">
                <n-select v-model:value="item.category" :options="categoryOptions" size="small" class="briefing-edit__category-select" />
                <n-button size="small" type="error" @click="handleDeleteItem(item.id)">删除</n-button>
              </div>
            </article>
          </section>
        </template>
      </n-spin>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { NInput, NButton, NSpace, NSelect, NSpin, useMessage } from 'naive-ui'
import AppLayout from '../components/layout/AppLayout.vue'
import { fetchBriefing, updateBriefing, updateBriefingItem, deleteBriefingItem } from '../api/briefings'
import { NEWS_CATEGORIES } from '../types/enums'
import { queryKeys } from '../shared/query/keys'
import type { Briefing, BriefingItem } from '../types'

const route = useRoute()
const message = useMessage()
const queryClient = useQueryClient()

const categoryOptions = NEWS_CATEGORIES.map(c => ({ label: c, value: c }))
const briefing = ref<Briefing | null>(null)

const briefingId = computed(() => Number(route.params.id))

const briefingQuery = useQuery({
  queryKey: computed(() => queryKeys.briefings.detail(briefingId.value)),
  queryFn: () => fetchBriefing(briefingId.value),
  enabled: computed(() => Number.isFinite(briefingId.value)),
})

watch(
  () => briefingQuery.data.value,
  (next) => {
    if (!next) {
      briefing.value = null
      return
    }
    briefing.value = JSON.parse(JSON.stringify(next)) as Briefing
  },
  { immediate: true }
)

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

const savingMutation = useMutation({
  mutationFn: async (payload: Briefing) => {
    await updateBriefing(payload.id, { title: payload.title })
    for (const item of payload.items) {
      await updateBriefingItem(item.id, {
        title: item.title,
        summary: item.summary,
        category: item.category,
      })
    }
  },
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.briefings.detail(briefingId.value) })
    await queryClient.invalidateQueries({ queryKey: queryKeys.briefings.list })
  },
})

const deleteItemMutation = useMutation({
  mutationFn: deleteBriefingItem,
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.briefings.detail(briefingId.value) })
  },
})

async function handleSave() {
  if (!briefing.value) return

  try {
    await savingMutation.mutateAsync(briefing.value)
    message.success('保存成功')
  } catch {
    message.error('保存失败')
  }
}

async function handleDeleteItem(itemId: number) {
  try {
    await deleteItemMutation.mutateAsync(itemId)
    if (briefing.value) {
      briefing.value.items = briefing.value.items.filter(i => i.id !== itemId)
    }
    message.success('已删除')
  } catch {
    message.error('删除失败')
  }
}
</script>

<style scoped>
.briefing-edit__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.briefing-edit__title-input {
  max-width: 460px;
  font-size: 18px;
  font-weight: 700;
}

.briefing-edit__group {
  margin-bottom: var(--space-6);
}

.briefing-edit__group-title {
  margin: 0 0 var(--space-3) 0;
  border-bottom: 2px solid #18a058;
  padding-bottom: var(--space-1);
}

.briefing-edit__item {
  margin-bottom: var(--space-3);
  padding: var(--space-3);
}

.briefing-edit__item-title {
  margin-bottom: var(--space-2);
  font-weight: 600;
}

.briefing-edit__item-actions {
  margin-top: var(--space-2);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
}

.briefing-edit__category-select {
  width: 220px;
}

@media (max-width: 767px) {
  .briefing-edit__header {
    flex-direction: column;
    align-items: stretch;
  }

  .briefing-edit__title-input {
    max-width: 100%;
  }

  .briefing-edit__item-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .briefing-edit__category-select {
    width: 100%;
  }
}
</style>
