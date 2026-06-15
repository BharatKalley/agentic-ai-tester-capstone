import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-AB-01 The page shall describe A/B testing or split testing as a way to test different', async ({ page, context }) => {
  await page.goto('/abtest', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toContainText(/A.B Test|No A.B Test/i);
});
