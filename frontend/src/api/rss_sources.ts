import client from './client'
import type { RssSource } from '../types'

export async function fetchRssSources(): Promise<RssSource[]> {
  const resp = await client.get<RssSource[]>('/rss-sources')
  return resp.data
}

export async function createRssSource(data: Partial<RssSource>): Promise<RssSource> {
  const resp = await client.post<RssSource>('/rss-sources', data)
  return resp.data
}

export async function updateRssSource(id: number, data: Partial<RssSource>): Promise<RssSource> {
  const resp = await client.put<RssSource>(`/rss-sources/${id}`, data)
  return resp.data
}

export async function deleteRssSource(id: number): Promise<void> {
  await client.delete(`/rss-sources/${id}`)
}
