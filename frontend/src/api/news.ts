import client from './client'
import type { NewsListResponse } from '../types'

export async function fetchNews(params: {
  page?: number
  page_size?: number
  status?: string
  category?: string
}): Promise<NewsListResponse> {
  const resp = await client.get<NewsListResponse>('/news', { params })
  return resp.data
}

export async function fetchNewsDetail(id: number) {
  const resp = await client.get(`/news/${id}`)
  return resp.data
}
