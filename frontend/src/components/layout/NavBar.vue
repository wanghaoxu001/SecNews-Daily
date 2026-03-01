<template>
  <n-layout-header bordered style="height: 56px; display: flex; align-items: center; padding: 0 24px; justify-content: space-between;">
    <div style="display: flex; align-items: center; gap: 24px;">
      <h3 style="margin: 0;">SecNews Daily</h3>
      <n-menu mode="horizontal" :value="currentRoute" :options="menuOptions" @update:value="handleNav" />
    </div>
    <n-button size="small" @click="handleLogout">退出</n-button>
  </n-layout-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NLayoutHeader, NMenu, NButton } from 'naive-ui'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const currentRoute = computed(() => route.name as string)

const menuOptions = [
  { label: '今日新闻', key: 'TodayNews' },
  { label: '快报列表', key: 'BriefingList' },
  { label: '管理', key: 'Management' },
]

function handleNav(key: string) {
  router.push({ name: key })
}

function handleLogout() {
  authStore.logout()
  router.push({ name: 'Login' })
}
</script>
