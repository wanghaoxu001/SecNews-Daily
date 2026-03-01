import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const resp = await apiLogin({ username, password })
    token.value = resp.access_token
    localStorage.setItem('token', resp.access_token)
  }

  function logout() {
    token.value = ''
    localStorage.removeItem('token')
  }

  return { token, isLoggedIn, login, logout }
})
