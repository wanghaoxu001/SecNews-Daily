<template>
  <div class="app-shell">
    <NavBar />
    <main class="app-main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import NavBar from './NavBar.vue'
</script>
