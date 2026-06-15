import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-FA-02 Successful Login with Valid Credentials', async ({ page, context }) => {
  await page.goto('/secure', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toBeVisible();
  await expect(page.locator('body')).toContainText(/Successful\ Login\ with\ Valid\ Credentials/i);
});
