<template>
  <AppLayout>
    <div style="max-width: 900px; margin: 0 auto;">
      <h2>快报列表</h2>
      <n-spin :show="loading">
        <div v-if="briefings.length === 0 && !loading" style="text-align: center; padding: 60px; color: #999;">
          暂无快报
        </div>
        <n-list bordered>
          <n-list-item v-for="b in briefings" :key="b.id" @click="goEdit(b.id)" style="cursor: pointer;">
            <n-thing>
              <template #header>{{ b.title }}</template>
              <template #description>
                <n-space>
                  <n-tag :type="b.status === 'published' ? 'success' : 'default'" size="small">{{ b.status }}</n-tag>
                  <span>{{ b.date }}</span>
                  <span>{{ b.item_count }} 条</span>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-spin>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NList, NListItem, NThing, NTag, NSpace, NSpin } from 'naive-ui'
import AppLayout from '../components/layout/AppLayout.vue'
import { fetchBriefings } from '../api/briefings'
import type { BriefingListItem } from '../types'

const router = useRouter()
const briefings = ref<BriefingListItem[]>([])
const loading = ref(false)

async function loadBriefings() {
  loading.value = true
  try {
    briefings.value = await fetchBriefings()
  } finally {
    loading.value = false
  }
}

function goEdit(id: number) {
  router.push({ name: 'BriefingEdit', params: { id } })
}

onMounted(loadBriefings)
</script>
