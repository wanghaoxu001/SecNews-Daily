<template>
  <header class="nav-shell">
    <div class="nav-brand-wrap">
      <h1 class="nav-brand" @click="handleNav('TodayNews')">SecNews Daily</h1>
      <n-menu
        v-if="!isMobile"
        mode="horizontal"
        :value="currentRoute"
        :options="menuOptions"
        @update:value="handleNav"
      />
    </div>

    <div class="nav-actions" v-if="!isMobile">
      <n-button size="small" secondary @click="handleLogout">退出</n-button>
    </div>

    <div class="nav-actions" v-else>
      <n-button size="small" secondary @click="mobileMenuVisible = true">菜单</n-button>
    </div>
  </header>

  <n-drawer v-model:show="mobileMenuVisible" placement="left" :width="280">
    <n-drawer-content title="导航">
      <div class="mobile-menu-body">
        <n-menu :value="currentRoute" :options="menuOptions" @update:value="handleMobileNav" />
        <n-button block type="error" ghost @click="handleLogout">退出登录</n-button>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NMenu, NButton, NDrawer, NDrawerContent } from 'naive-ui'
import { useAuthSession } from '../../composables/useAuthQuery'
import { useResponsive } from '../../composables/useResponsive'

const router = useRouter()
const route = useRoute()
const { logout } = useAuthSession()
const { isMobile } = useResponsive()

const mobileMenuVisible = ref(false)
const currentRoute = computed(() => (route.name as string) || 'TodayNews')

const menuOptions = [
  { label: '今日新闻', key: 'TodayNews' },
  { label: '快报列表', key: 'BriefingList' },
  { label: '管理', key: 'Management' },
]

function handleNav(key: string) {
  router.push({ name: key })
}

function handleMobileNav(key: string) {
  mobileMenuVisible.value = false
  handleNav(key)
}

function handleLogout() {
  logout()
  mobileMenuVisible.value = false
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.nav-shell {
  position: sticky;
  top: 0;
  z-index: 20;
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 var(--space-6);
  border-bottom: 1px solid var(--color-border);
  background: color-mix(in srgb, var(--color-surface) 92%, #f8fbff 8%);
  backdrop-filter: blur(8px);
}

.nav-brand-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  min-width: 0;
}

.nav-brand {
  margin: 0;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  white-space: nowrap;
}

.nav-actions {
  display: flex;
  align-items: center;
}

.mobile-menu-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

@media (max-width: 767px) {
  .nav-shell {
    padding: 0 var(--space-4);
  }

  .nav-brand {
    font-size: 16px;
  }
}
</style>
