const TIMEZONE = 'Asia/Shanghai'

export function todayInChina(): string {
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

export function formatDateTime(isoStr: string | null): string {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString('zh-CN', { timeZone: TIMEZONE })
}

export function formatDate(isoStr: string | null): string {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString('zh-CN', { timeZone: TIMEZONE })
}
