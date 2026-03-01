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
