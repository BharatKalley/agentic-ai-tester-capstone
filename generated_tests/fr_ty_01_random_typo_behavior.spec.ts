import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-TY-01 Random Typo Behavior', async ({ page, context }) => {
  await page.goto('/typos', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Typos/i })).toBeVisible();
  await expect(page.locator('body')).toContainText(/typo/i);
});
