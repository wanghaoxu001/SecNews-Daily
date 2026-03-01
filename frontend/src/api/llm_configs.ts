import client from './client'
import type { LlmConfig } from '../types'

export interface LlmTestResult {
  success: boolean
  message: string
  latency_ms: number
}

export async function fetchLlmConfigs(): Promise<LlmConfig[]> {
  const resp = await client.get<LlmConfig[]>('/llm-configs')
  return resp.data
}

export async function ensureLlmDefaults(): Promise<LlmConfig[]> {
  const resp = await client.post<LlmConfig[]>('/llm-configs/ensure-defaults')
  return resp.data
}

export async function createLlmConfig(data: Partial<LlmConfig>): Promise<LlmConfig> {
  const resp = await client.post<LlmConfig>('/llm-configs', data)
  return resp.data
}

export async function updateLlmConfig(id: number, data: Partial<LlmConfig>): Promise<LlmConfig> {
  const resp = await client.put<LlmConfig>(`/llm-configs/${id}`, data)
  return resp.data
}

export async function deleteLlmConfig(id: number): Promise<void> {
  await client.delete(`/llm-configs/${id}`)
}

export async function testLlmConfig(taskType: string): Promise<LlmTestResult> {
  const resp = await client.post<LlmTestResult>(`/llm-configs/test/${taskType}`)
  return resp.data
}
