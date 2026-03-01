export interface NewsListQuery {
  page: number
  page_size: number
  status?: string
  category?: string
  source_id?: number
  keyword?: string
  date_from?: string
  date_to?: string
  is_similar?: boolean
  is_important?: boolean
}

export const queryKeys = {
  auth: {
    token: ['auth', 'token'] as const,
  },
  news: {
    list: (query: NewsListQuery) => ['news', 'list', query] as const,
    detail: (id: number) => ['news', 'detail', id] as const,
  },
  briefings: {
    list: ['briefings', 'list'] as const,
    detail: (id: number) => ['briefings', 'detail', id] as const,
  },
  rssSources: {
    list: ['rss-sources', 'list'] as const,
  },
  llmConfigs: {
    all: ['llm-configs', 'all'] as const,
    cooldown: ['llm-configs', 'cooldown'] as const,
  },
  taskConfigs: {
    all: ['task-configs', 'all'] as const,
  },
  processingConfigs: {
    all: ['processing-configs', 'all'] as const,
  },
  importanceExamples: {
    all: (category?: string) => ['importance-examples', 'all', category ?? 'all'] as const,
  },
}
