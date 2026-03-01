import client from './client'
import type { ImportanceExample } from '../types'

export async function fetchImportanceExamples(category?: string): Promise<ImportanceExample[]> {
  const params = category ? { category } : {}
  const resp = await client.get<ImportanceExample[]>('/importance-examples', { params })
  return resp.data
}

export async function createImportanceExample(data: Partial<ImportanceExample>): Promise<ImportanceExample> {
  const resp = await client.post<ImportanceExample>('/importance-examples', data)
  return resp.data
}

export async function bulkImportExamples(items: Partial<ImportanceExample>[]): Promise<ImportanceExample[]> {
  const resp = await client.post<ImportanceExample[]>('/importance-examples/bulk-import', items)
  return resp.data
}

export async function updateImportanceExample(id: number, data: Partial<ImportanceExample>): Promise<ImportanceExample> {
  const resp = await client.put<ImportanceExample>(`/importance-examples/${id}`, data)
  return resp.data
}

export async function deleteImportanceExample(id: number): Promise<void> {
  await client.delete(`/importance-examples/${id}`)
}
