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

export function formatMonthDayTime(isoStr: string | null): string {
  if (!isoStr) return ''

  const date = new Date(isoStr)
  if (Number.isNaN(date.getTime())) return ''

  const parts = new Intl.DateTimeFormat('zh-CN', {
    timeZone: TIMEZONE,
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(date)

  const month = parts.find(p => p.type === 'month')?.value ?? ''
  const day = parts.find(p => p.type === 'day')?.value ?? ''
  const hour = parts.find(p => p.type === 'hour')?.value ?? ''
  const minute = parts.find(p => p.type === 'minute')?.value ?? ''

  if (!month || !day || !hour || !minute) return ''
  return `${month}/${day} ${hour}:${minute}`
}
