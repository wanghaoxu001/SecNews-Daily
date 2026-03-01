import client from './client'
import type { NewsListResponse } from '../types'

export async function fetchNews(params: {
  page?: number
  page_size?: number
  status?: string
  category?: string
  source_id?: number
  keyword?: string
  date_from?: string
  date_to?: string
  is_similar?: boolean
  is_important?: boolean
}): Promise<NewsListResponse> {
  const resp = await client.get<NewsListResponse>('/news', { params })
  return resp.data
}

export async function fetchNewsDetail(id: number) {
  const resp = await client.get(`/news/${id}`)
  return resp.data
}

export async function batchReprocessNews(
  news_ids: number[],
  target_status: string,
): Promise<{ reset_count: number; pipeline_result: Record<string, unknown> | null }> {
  const resp = await client.post('/news/batch-reprocess', { news_ids, target_status })
  return resp.data
}

export async function batchDeleteNews(
  news_ids: number[],
): Promise<{ deleted_count: number }> {
  const resp = await client.post('/news/batch-delete', { news_ids })
  return resp.data
}
