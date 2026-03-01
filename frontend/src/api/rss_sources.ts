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

export interface PipelineEvent {
  step: 'fetch' | 'process' | 'similarity' | 'importance' | 'done'
  status: 'running' | 'success' | 'error' | 'info'
  message: string
  detail?: string
}

export async function runSourcePipeline(
  sourceId: number,
  onEvent: (event: PipelineEvent) => void,
): Promise<void> {
  const token = localStorage.getItem('token')
  const resp = await fetch(`/api/v1/rss-sources/${sourceId}/run`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`)
  }

  const reader = resp.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()! // keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6)) as PipelineEvent
          onEvent(event)
        } catch {
          // skip malformed lines
        }
      }
    }
  }

  // Process any remaining buffer
  if (buffer.startsWith('data: ')) {
    try {
      const event = JSON.parse(buffer.slice(6)) as PipelineEvent
      onEvent(event)
    } catch {
      // skip
    }
  }
}
