import { test, expect } from '@playwright/test'

test('login page should render', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByText('SecNews Daily')).toBeVisible()
  await expect(page.getByRole('button', { name: '登录' })).toBeVisible()
})
