import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-DL 01: The page shall present a list of files as links under the heading "File Downloader"', async ({ page, context }) => {
  await page.goto('/download', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /File Downloader/i })).toBeVisible();
  await expect(page.locator('a').first()).toBeVisible();
});
