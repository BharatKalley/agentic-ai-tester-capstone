import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-UP-01 File Uploader Rendering', async ({ page, context }) => {
  await page.goto('/upload', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /File Uploader/i })).toBeVisible();
  await expect(page.locator('input[type=file]')).toBeVisible();
  await expect(page.locator('#file-submit')).toBeVisible();
});
