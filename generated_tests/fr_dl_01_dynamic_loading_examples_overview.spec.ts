import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-DL-01 Dynamic Loading Examples Overview', async ({ page, context }) => {
  await page.goto('/dynamic_loading', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Dynamically Loaded Page Elements/i })).toBeVisible();
  await expect(page.getByRole('link', { name: /Example 1/i })).toBeVisible();
  await expect(page.getByRole('link', { name: /Example 2/i })).toBeVisible();
});
