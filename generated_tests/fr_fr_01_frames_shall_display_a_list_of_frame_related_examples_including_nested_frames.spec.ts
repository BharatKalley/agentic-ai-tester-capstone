import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-FR-01 /frames shall display a list of frame-related examples, including "Nested Frames"', async ({ page, context }) => {
  await page.goto('/frames', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Frames/i })).toBeVisible();
  await expect(page.getByRole('link', { name: /Nested Frames/i })).toBeVisible();
  await expect(page.getByRole('link', { name: /iFrame/i })).toBeVisible();
});
