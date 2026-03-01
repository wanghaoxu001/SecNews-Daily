import { describe, expect, it } from 'vitest'
import { formatDate, formatDateTime, todayInChina } from './date'

describe('date utils', () => {
  it('returns empty string for null input', () => {
    expect(formatDate(null)).toBe('')
    expect(formatDateTime(null)).toBe('')
  })

  it('formats china date string as yyyy-mm-dd', () => {
    expect(todayInChina()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})
