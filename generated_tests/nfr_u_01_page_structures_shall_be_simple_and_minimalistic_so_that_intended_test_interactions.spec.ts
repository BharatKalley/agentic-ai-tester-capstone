import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('NFR-U-01 Page structures shall be simple and minimalistic so that intended test interactions', async ({ page, context }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toBeVisible();
  await expect(page.locator('body')).not.toBeEmpty();
});
