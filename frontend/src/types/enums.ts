export const NEWS_CATEGORIES = [
  '金融业网络安全事件',
  '重大网络安全事件',
  '重大数据泄露事件',
  '重大漏洞风险提示',
  '其他',
] as const

export type NewsCategory = typeof NEWS_CATEGORIES[number]

export const PROCESS_STATUSES = [
  'pending',
  'processing',
  'processed',
  'similarity_checked',
  'completed',
  'failed',
] as const

export const CATEGORY_COLORS: Record<string, string> = {
  '金融业网络安全事件': '#1890ff',
  '重大网络安全事件': '#f5222d',
  '重大数据泄露事件': '#fa8c16',
  '重大漏洞风险提示': '#faad14',
  '其他': '#8c8c8c',
}

export const STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  processed: '已处理',
  similarity_checked: '已查重',
  completed: '已完成',
  failed: '失败',
}

export const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  pending: 'default',
  processing: 'info',
  processed: 'info',
  similarity_checked: 'warning',
  completed: 'success',
  failed: 'error',
}

export const REPROCESS_TARGETS = [
  { label: '从头处理 (pending)', value: 'pending' },
  { label: '从查重开始 (processed)', value: 'processed' },
  { label: '从重要性开始 (similarity_checked)', value: 'similarity_checked' },
] as const
