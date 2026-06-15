import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-UP-02 Upload Action', async ({ page, context }) => {
  await page.goto('/upload', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /File Uploader/i })).toBeVisible();
  await expect(page.locator('input[type=file]')).toBeVisible();
  await expect(page.locator('#file-submit')).toBeVisible();
  await page.locator('input[type=file]').setInputFiles({ name: 'sample.txt', mimeType: 'text/plain', buffer: Buffer.from('capstone upload') });
  await page.locator('#file-submit').click();
  await expect(page.getByRole('heading', { name: /File Uploaded/i })).toBeVisible();
  await expect(page.locator('#uploaded-files')).toContainText('sample.txt');
});
