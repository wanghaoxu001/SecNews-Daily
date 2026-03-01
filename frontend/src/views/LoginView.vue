<template>
  <div style="display: flex; justify-content: center; align-items: center; height: 100vh; background: #f5f5f5;">
    <n-card style="width: 380px;" title="SecNews Daily">
      <n-form @submit.prevent="handleLogin">
        <n-form-item label="用户名">
          <n-input v-model:value="username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="password" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="handleLogin">
          登录
        </n-button>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    message.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    router.push({ name: 'TodayNews' })
  } catch {
    message.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>
