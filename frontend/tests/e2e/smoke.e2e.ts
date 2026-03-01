import { test, expect } from '@playwright/test'

test('login page should render redesigned layout', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByText('SecNews Daily')).toBeVisible()
  await expect(page.getByText('登录控制台')).toBeVisible()
  await expect(page.getByRole('button', { name: '登录' })).toBeVisible()
})

test('today page should render refresh and filter panel', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'mock-token')
  })

  await page.route('**/api/v1/news**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
      }),
    })
  })

  await page.goto('/today')
  await expect(page.getByRole('button', { name: '刷新数据' })).toBeVisible()
  await expect(page.getByText('分类筛选')).toBeVisible()
  await expect(page.getByText('状态筛选')).toBeVisible()
  await expect(page.getByText('暂无新闻')).toBeVisible()
})
