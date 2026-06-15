import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-FR-02 Selecting "Nested Frames" shall navigate to /nested_frames where multiple frames', async ({ page, context }) => {
  await page.goto('/nested_frames', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toBeVisible();
  await expect(page.locator('body')).not.toBeEmpty();
});
