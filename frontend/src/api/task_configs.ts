import client from './client'
import type { TaskConfig } from '../types'

export async function fetchTaskConfigs(): Promise<TaskConfig[]> {
  const resp = await client.get<TaskConfig[]>('/task-configs')
  return resp.data
}

export async function createTaskConfig(data: Partial<TaskConfig>): Promise<TaskConfig> {
  const resp = await client.post<TaskConfig>('/task-configs', data)
  return resp.data
}

export async function updateTaskConfig(id: number, data: Partial<TaskConfig>): Promise<TaskConfig> {
  const resp = await client.put<TaskConfig>(`/task-configs/${id}`, data)
  return resp.data
}

export async function deleteTaskConfig(id: number): Promise<void> {
  await client.delete(`/task-configs/${id}`)
}
