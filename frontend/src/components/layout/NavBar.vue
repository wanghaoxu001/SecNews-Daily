<template>
  <header class="nav-shell">
    <div class="nav-shell__inner page-container page-container--wide">
      <button class="nav-brand" type="button" @click="handleNav('TodayNews')">
        <span class="nav-brand__badge">SD</span>
        <span class="nav-brand__text-group">
          <span class="nav-brand__title">SecNews Daily</span>
          <span class="nav-brand__subtitle">网安情报快报</span>
        </span>
      </button>

      <nav v-if="!isMobile" class="nav-links" aria-label="主导航">
        <button
          v-for="item in menuOptions"
          :key="item.key"
          type="button"
          class="nav-link"
          :class="{ 'nav-link--active': currentRoute === item.key }"
          :aria-current="currentRoute === item.key ? 'page' : undefined"
          @click="handleNav(item.key)"
        >
          {{ item.label }}
        </button>
      </nav>

      <div class="nav-actions" v-if="!isMobile">
        <n-button size="small" tertiary @click="handleLogout">退出</n-button>
      </div>

      <div class="nav-actions" v-else>
        <n-button size="small" secondary @click="mobileMenuVisible = true">菜单</n-button>
      </div>
    </div>
  </header>

  <n-drawer v-model:show="mobileMenuVisible" placement="left" :width="300">
    <n-drawer-content title="导航">
      <div class="mobile-menu-body">
        <div class="mobile-menu-head">
          <strong>SecNews Daily</strong>
          <span>网安情报快报</span>
        </div>
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
  z-index: 30;
  border-bottom: 1px solid color-mix(in srgb, var(--color-line-subtle) 85%, #ffffff 15%);
  background: color-mix(in srgb, var(--color-panel) 86%, #f6f9ff 14%);
  backdrop-filter: blur(12px);
}

.nav-shell__inner {
  height: var(--header-height);
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-4);
}

.nav-brand {
  border: 0;
  padding: 0;
  background: none;
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  cursor: pointer;
}

.nav-brand__badge {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, var(--color-brand-500), color-mix(in srgb, var(--color-brand-600) 82%, #0f274f 18%));
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  box-shadow: var(--shadow-1);
}

.nav-brand__text-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.nav-brand__title {
  font-size: 18px;
  font-weight: 800;
  line-height: 1;
  color: var(--color-text-primary);
}

.nav-brand__subtitle {
  margin-top: 2px;
  font-size: 11px;
  color: var(--color-text-tertiary);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.nav-link {
  border: 0;
  background: transparent;
  color: var(--color-text-secondary);
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition:
    color var(--motion-fast) ease,
    background-color var(--motion-fast) ease,
    box-shadow var(--motion-fast) ease;
}

.nav-link:hover {
  color: var(--color-brand-600);
  background: color-mix(in srgb, var(--color-brand-soft) 65%, #ffffff 35%);
}

.nav-link--active {
  color: var(--color-brand-600);
  background: color-mix(in srgb, var(--color-brand-soft) 78%, #ffffff 22%);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-brand-500) 38%, transparent);
}

.nav-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.mobile-menu-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-top: var(--space-2);
}

.mobile-menu-head {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.mobile-menu-head strong {
  font-size: 16px;
}

.mobile-menu-head span {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

@media (max-width: 767px) {
  .nav-shell__inner {
    gap: var(--space-2);
  }

  .nav-brand__badge {
    width: 30px;
    height: 30px;
    border-radius: 9px;
    font-size: 11px;
  }

  .nav-brand__title {
    font-size: 16px;
  }

  .nav-brand__subtitle {
    display: none;
  }
}
</style>
