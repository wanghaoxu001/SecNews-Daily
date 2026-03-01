<template>
  <n-layout has-sider style="height: 100vh">
    <n-layout>
      <NavBar />
      <n-layout-content style="padding: 24px;">
        <slot />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { NLayout, NLayoutContent } from 'naive-ui'
import NavBar from './NavBar.vue'
</script>
