import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-JQM-01 The page shall display a JQuery UI menu demonstrating nested menu items', async ({ page, context }) => {
  await page.goto('/jqueryui/menu', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /JQueryUI/i })).toBeVisible();
  await expect(page.locator('#menu')).toBeVisible();
  await expect(page.getByRole('link', { name: /Enabled/i })).toBeVisible();
});
