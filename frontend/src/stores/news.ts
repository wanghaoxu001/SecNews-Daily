import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchNews } from '../api/news'
import type { News, NewsListResponse } from '../types'

export const useNewsStore = defineStore('news', () => {
  const newsList = ref<News[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const filters = ref<{
    status?: string
    category?: string
  }>({})

  async function loadNews() {
    loading.value = true
    try {
      const resp = await fetchNews({
        page: page.value,
        page_size: pageSize.value,
        ...filters.value,
      })
      newsList.value = resp.items
      total.value = resp.total
    } finally {
      loading.value = false
    }
  }

  function setFilters(f: { status?: string; category?: string }) {
    filters.value = f
    page.value = 1
  }

  return { newsList, total, page, pageSize, loading, filters, loadNews, setFilters }
})
