<template>
  <AppLayout>
    <section class="page-container">
      <h2 class="page-title briefing-list__title">快报列表</h2>

      <n-spin :show="briefingsQuery.isLoading.value">
        <div v-if="briefings.length === 0 && !briefingsQuery.isLoading.value" class="empty-state">
          暂无快报
        </div>

        <n-list bordered>
          <n-list-item
            v-for="b in briefings"
            :key="b.id"
            class="briefing-list__item"
            @click="goEdit(b.id)"
          >
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
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { NList, NListItem, NThing, NTag, NSpace, NSpin } from 'naive-ui'
import AppLayout from '../components/layout/AppLayout.vue'
import { fetchBriefings } from '../api/briefings'
import { queryKeys } from '../shared/query/keys'

const router = useRouter()

const briefingsQuery = useQuery({
  queryKey: queryKeys.briefings.list,
  queryFn: fetchBriefings,
})

const briefings = computed(() => briefingsQuery.data.value ?? [])

function goEdit(id: number) {
  router.push({ name: 'BriefingEdit', params: { id } })
}
</script>

<style scoped>
.briefing-list__title {
  margin-bottom: var(--space-4);
}

.briefing-list__item {
  cursor: pointer;
}
</style>
