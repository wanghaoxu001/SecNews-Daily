<template>
  <div class="login-shell">
    <section class="login-panel surface-card">
      <div class="login-hero">
        <p class="section-eyebrow">Security Briefing Console</p>
        <h1 class="login-hero__title">SecNews Daily</h1>
        <p class="login-hero__description">
          每日聚合网安情报，快速筛选高价值事件，自动生成可编辑的快报草稿。
        </p>
        <ul class="login-hero__highlights">
          <li>自动抓取与去重，减少人工筛查负担</li>
          <li>重要性标记辅助判断，提升收录效率</li>
          <li>统一管理 RSS、模型与处理参数</li>
        </ul>
      </div>

      <n-card class="login-card" :bordered="false">
        <div class="login-card__header">
          <h2>登录控制台</h2>
          <p>使用管理员账号继续</p>
        </div>

        <n-form class="login-form" label-placement="top" @submit.prevent="handleLogin">
          <n-form-item label="用户名">
            <n-input v-model:value="username" placeholder="请输入用户名" />
          </n-form-item>
          <n-form-item label="密码">
            <n-input
              v-model:value="password"
              type="password"
              placeholder="请输入密码"
              @keyup.enter="handleLogin"
            />
          </n-form-item>
          <n-button
            class="login-form__submit"
            type="primary"
            block
            size="large"
            :loading="loginMutation.isPending.value"
            @click="handleLogin"
          >
            登录
          </n-button>
        </n-form>
      </n-card>
    </section>
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
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6) var(--space-4);
}

.login-panel {
  width: min(980px, 100%);
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  overflow: hidden;
}

.login-hero {
  padding: var(--space-7);
  border-right: 1px solid color-mix(in srgb, var(--color-line-subtle) 72%, transparent);
  background: linear-gradient(
    160deg,
    color-mix(in srgb, var(--color-brand-soft) 58%, #ffffff 42%),
    color-mix(in srgb, var(--color-panel) 84%, #f4f8ff 16%)
  );
}

.login-hero__title {
  margin: 0;
  font-size: clamp(34px, 4vw, 42px);
  line-height: 1.05;
}

.login-hero__description {
  margin: var(--space-4) 0 0;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.login-hero__highlights {
  margin: var(--space-5) 0 0;
  padding-left: 18px;
  color: var(--color-text-secondary);
  display: grid;
  gap: var(--space-2);
}

.login-card {
  align-self: stretch;
  display: grid;
}

.login-card :deep(.n-card__content) {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: var(--space-7);
}

.login-card__header h2 {
  margin: 0;
  font-size: 28px;
}

.login-card__header p {
  margin: var(--space-2) 0 0;
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.login-form {
  margin-top: var(--space-5);
}

.login-form__submit {
  margin-top: var(--space-2);
}

@media (max-width: 900px) {
  .login-panel {
    grid-template-columns: 1fr;
  }

  .login-hero {
    padding: var(--space-5);
    border-right: 0;
    border-bottom: 1px solid color-mix(in srgb, var(--color-line-subtle) 72%, transparent);
  }

  .login-card :deep(.n-card__content) {
    padding: var(--space-5);
  }

  .login-hero__title {
    font-size: clamp(30px, 8vw, 36px);
  }
}
</style>
