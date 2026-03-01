import client from './client'
import type { Briefing, BriefingListItem, BriefingItem } from '../types'

export async function fetchBriefings(): Promise<BriefingListItem[]> {
  const resp = await client.get<BriefingListItem[]>('/briefings')
  return resp.data
}

export async function fetchBriefing(id: number): Promise<Briefing> {
  const resp = await client.get<Briefing>(`/briefings/${id}`)
  return resp.data
}

export async function createBriefing(data: { title: string; date: string; news_ids: number[] }): Promise<Briefing> {
  const resp = await client.post<Briefing>('/briefings', data)
  return resp.data
}

export async function updateBriefing(id: number, data: { title?: string; status?: string }): Promise<Briefing> {
  const resp = await client.put<Briefing>(`/briefings/${id}`, data)
  return resp.data
}

export async function deleteBriefing(id: number): Promise<void> {
  await client.delete(`/briefings/${id}`)
}

export async function updateBriefingItem(id: number, data: Partial<BriefingItem>): Promise<BriefingItem> {
  const resp = await client.put<BriefingItem>(`/briefing-items/${id}`, data)
  return resp.data
}

export async function deleteBriefingItem(id: number): Promise<void> {
  await client.delete(`/briefing-items/${id}`)
}

export async function reorderBriefingItems(briefingId: number, itemIds: number[]): Promise<void> {
  await client.post(`/briefing-items/reorder/${briefingId}`, { item_ids: itemIds })
}

export async function fetchLatestBriefing(): Promise<Briefing | null> {
  const resp = await client.get('/briefings/latest')
  return resp.data
}
