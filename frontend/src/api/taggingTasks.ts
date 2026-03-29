import client from './client'
import type {
  ImportTaggingTaskResponse,
  TaggingTaskDetailResponse,
  TaggingTaskListItem,
  UpdateTaggingTaskItemResponse,
} from '../types'

export async function createTaggingTask(file: File): Promise<TaggingTaskDetailResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const resp = await client.post<TaggingTaskDetailResponse>('/tagging-tasks', formData)
  return resp.data
}

export async function fetchTaggingTask(taskId: number): Promise<TaggingTaskDetailResponse> {
  const resp = await client.get<TaggingTaskDetailResponse>(`/tagging-tasks/${taskId}`)
  return resp.data
}

export async function updateTaggingTaskCursor(taskId: number, currentIndex: number): Promise<TaggingTaskDetailResponse> {
  const resp = await client.patch<TaggingTaskDetailResponse>(`/tagging-tasks/${taskId}/cursor`, {
    current_index: currentIndex,
  })
  return resp.data
}

export async function updateTaggingTaskItem(
  taskId: number,
  itemId: number,
  isImportant: boolean | null,
): Promise<UpdateTaggingTaskItemResponse> {
  const resp = await client.patch<UpdateTaggingTaskItemResponse>(`/tagging-tasks/${taskId}/items/${itemId}`, {
    is_important: isImportant,
  })
  return resp.data
}

export async function completeTaggingTask(taskId: number): Promise<TaggingTaskDetailResponse> {
  const resp = await client.post<TaggingTaskDetailResponse>(`/tagging-tasks/${taskId}/complete`)
  return resp.data
}

export async function importTaggingTask(taskId: number): Promise<ImportTaggingTaskResponse> {
  const resp = await client.post<ImportTaggingTaskResponse>(`/tagging-tasks/${taskId}/import`)
  return resp.data
}

export async function fetchTaggingTasks(): Promise<TaggingTaskListItem[]> {
  const resp = await client.get<TaggingTaskListItem[]>('/tagging-tasks')
  return resp.data
}
