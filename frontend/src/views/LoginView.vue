<template>
  <div class="login-shell">
    <n-card class="login-card" title="SecNews Daily">
      <n-form @submit.prevent="handleLogin">
        <n-form-item label="用户名">
          <n-input v-model:value="username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="password" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />
        </n-form-item>
        <n-button type="primary" block :loading="loginMutation.isPending.value" @click="handleLogin">
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
import { useAuthSession } from '../composables/useAuthQuery'

const router = useRouter()
const message = useMessage()
const { loginMutation } = useAuthSession()

const username = ref('')
const password = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    message.warning('请输入用户名和密码')
    return
  }

  try {
    await loginMutation.mutateAsync({
      username: username.value,
      password: password.value,
    })
    router.push({ name: 'TodayNews' })
  } catch {
    message.error('登录失败，请检查用户名和密码')
  }
}
</script>

<style scoped>
.login-shell {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100dvh;
  padding: var(--space-4);
}

.login-card {
  width: min(420px, 100%);
}
</style>
