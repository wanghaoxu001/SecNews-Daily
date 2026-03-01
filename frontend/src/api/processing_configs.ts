import client from './client'
import type { ProcessingConfig } from '../types'

export async function fetchProcessingConfigs(): Promise<ProcessingConfig[]> {
  const resp = await client.get<ProcessingConfig[]>('/processing-configs')
  return resp.data
}

export async function createProcessingConfig(data: Partial<ProcessingConfig>): Promise<ProcessingConfig> {
  const resp = await client.post<ProcessingConfig>('/processing-configs', data)
  return resp.data
}

export async function updateProcessingConfig(id: number, data: Partial<ProcessingConfig>): Promise<ProcessingConfig> {
  const resp = await client.put<ProcessingConfig>(`/processing-configs/${id}`, data)
  return resp.data
}

export async function deleteProcessingConfig(id: number): Promise<void> {
  await client.delete(`/processing-configs/${id}`)
}
