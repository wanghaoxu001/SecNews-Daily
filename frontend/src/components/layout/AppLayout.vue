<template>
  <div class="app-shell">
    <NavBar />
    <main class="app-main">
      <div class="app-main__inner">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import NavBar from './NavBar.vue'
</script>
