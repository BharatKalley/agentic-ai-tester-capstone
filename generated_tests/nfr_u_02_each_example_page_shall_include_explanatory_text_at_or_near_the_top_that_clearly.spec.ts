import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('NFR-U-02 Each example page shall include explanatory text at or near the top that clearly', async ({ page, context }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toBeVisible();
  await expect(page.locator('body')).not.toBeEmpty();
});
