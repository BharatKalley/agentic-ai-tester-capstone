import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-IS-01 The page shall implement infinite scrolling such that scrolling down loads additional', async ({ page, context }) => {
  await page.goto('/infinite_scroll', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Infinite Scroll/i })).toBeVisible();
  const before = await page.locator('.jscroll-added').count();
  await page.mouse.wheel(0, 3000);
  await expect.poll(async () => page.locator('.jscroll-added').count()).toBeGreaterThanOrEqual(before);
});
