import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-FM-01 The page shall show a floating menu that remains visible while the user scrolls', async ({ page, context }) => {
  await page.goto('/floating_menu', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Floating Menu/i })).toBeVisible();
  await expect(page.locator('#menu')).toBeVisible();
  await page.mouse.wheel(0, 1500);
  await expect(page.locator('#menu')).toBeVisible();
});
