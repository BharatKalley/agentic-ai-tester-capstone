import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-SD-01 The page shall demonstrate shadow DOM usage, including the text "My default', async ({ page, context }) => {
  await page.goto('/shadowdom', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Simple template/i })).toBeVisible();
  await expect(page.locator('my-paragraph')).toHaveCount(2);
  await expect(page.locator('body')).toContainText(/My default text|different text/i);
});
