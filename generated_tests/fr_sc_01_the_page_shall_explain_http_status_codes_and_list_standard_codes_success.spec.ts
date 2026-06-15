import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-SC-01 The page shall explain HTTP status codes and list standard codes (Success,', async ({ page, context }) => {
  await page.goto('/status_codes', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Status Codes/i })).toBeVisible();
  await expect(page.getByRole('link', { name: '200' })).toBeVisible();
  await expect(page.getByRole('link', { name: '404' })).toBeVisible();
});
