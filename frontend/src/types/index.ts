export interface News {
  id: number
  title: string
  url: string
  summary: string | null
  content: string | null
  author: string | null
  published_at: string | null
  source_id: number | null
  source_name: string | null
  title_zh: string | null
  summary_zh: string | null
  category: string | null
  process_status: string
  process_error: string | null
  crawl_error_code: string | null
  crawl_error_detail: string | null
  crawl_attempts: number | null
  crawl_last_duration_ms: number | null
  crawl_last_attempt_at: string | null
  is_similar: boolean
  similar_to_id: number | null
  similarity_details: Record<string, unknown> | null
  is_important: boolean | null
  importance_reason: string | null
  created_at: string
  updated_at: string
}

export interface NewsListResponse {
  items: News[]
  total: number
  page: number
  page_size: number
}

export interface BriefingItem {
  id: number
  briefing_id: number
  news_id: number | null
  title: string
  summary: string | null
  category: string | null
  sort_order: number
  created_at: string
  updated_at: string
}

export interface Briefing {
  id: number
  title: string
  date: string
  status: string
  items: BriefingItem[]
  created_at: string
  updated_at: string
}

export interface BriefingListItem {
  id: number
  title: string
  date: string
  status: string
  item_count: number
  created_at: string
}

export interface RssSource {
  id: number
  name: string
  url: string
  enabled: boolean
  description: string | null
  domain: string | null
  probe_status: string | null
  probe_last_run_at: string | null
  probe_last_error: string | null
  effective_wait_for_chain: string[] | null
  effective_timeouts_ms: number[] | null
  created_at: string
  updated_at: string
}

export interface LlmConfig {
  id: number
  task_type: string
  base_url: string | null
  api_key: string | null
  model: string | null
  temperature: number | null
  max_tokens: number | null
  created_at: string
  updated_at: string
}

export interface TaskConfig {
  id: number
  name: string
  cron_expression: string
  enabled: boolean
  description: string | null
  created_at: string
  updated_at: string
}

export interface ProcessingConfig {
  id: number
  key: string
  value: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface ImportanceExample {
  id: number
  title: string
  summary: string | null
  category: string
  is_important: boolean
  reason: string | null
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface TaggingTaskListItem {
  id: number
  original_file_name: string
  status: string
  total_count: number
  current_index: number
  labeled_count: number
  imported_at: string | null
  created_at: string
  updated_at: string
}

export interface TaggingTaskItem {
  id: number
  task_id: number
  row_index: number
  title: string
  summary: string | null
  category: string
  reason: string | null
  is_important: boolean | null
  created_at: string
  updated_at: string
}

export interface TaggingTaskDetailResponse {
  task: TaggingTaskListItem
  current_item: TaggingTaskItem | null
  items: TaggingTaskItem[]
}

export interface UpdateTaggingTaskItemResponse {
  task: TaggingTaskListItem
  item: TaggingTaskItem
}

export interface ImportTaggingTaskResponse {
  task: TaggingTaskListItem
  imported_count: number
  skipped_count: number
}
