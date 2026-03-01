import { computed } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { login as loginApi } from '../api/auth'
import { queryKeys } from '../shared/query/keys'

function getStoredToken(): string {
  return localStorage.getItem('token') || ''
}

function setStoredToken(token: string) {
  if (token) {
    localStorage.setItem('token', token)
  } else {
    localStorage.removeItem('token')
  }
}

export function useAuthTokenQuery() {
  return useQuery({
    queryKey: queryKeys.auth.token,
    queryFn: async () => getStoredToken(),
    initialData: getStoredToken,
    staleTime: Number.POSITIVE_INFINITY,
    gcTime: Number.POSITIVE_INFINITY,
  })
}

export function useAuthSession() {
  const queryClient = useQueryClient()
  const tokenQuery = useAuthTokenQuery()

  const loginMutation = useMutation({
    mutationFn: (params: { username: string; password: string }) => loginApi(params),
    onSuccess: (resp) => {
      setStoredToken(resp.access_token)
      queryClient.setQueryData(queryKeys.auth.token, resp.access_token)
    },
  })

  function logout() {
    setStoredToken('')
    queryClient.setQueryData(queryKeys.auth.token, '')
    queryClient.removeQueries({ queryKey: ['news'] })
  }

  const token = computed(() => tokenQuery.data.value || '')
  const isLoggedIn = computed(() => !!token.value)

  return {
    token,
    isLoggedIn,
    tokenQuery,
    loginMutation,
    logout,
  }
}
