import { describe, expect, it } from 'vitest'
import { formatDate, formatDateTime, formatMonthDayTime, todayInChina } from './date'

describe('date utils', () => {
  it('returns empty string for null input', () => {
    expect(formatDate(null)).toBe('')
    expect(formatDateTime(null)).toBe('')
    expect(formatMonthDayTime(null)).toBe('')
  })

  it('formats china date string as yyyy-mm-dd', () => {
    expect(todayInChina()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('formats month/day and hour/minute', () => {
    expect(formatMonthDayTime('2026-03-01T10:35:00Z')).toMatch(/^\d{2}\/\d{2} \d{2}:\d{2}$/)
  })
})
