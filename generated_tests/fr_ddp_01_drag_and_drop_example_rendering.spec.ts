import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-DDP-01 Drag and Drop Example Rendering', async ({ page, context }) => {
  await page.goto('/drag_and_drop', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Drag and Drop/i })).toBeVisible();
  await expect(page.locator('#column-a')).toBeVisible();
  await expect(page.locator('#column-b')).toBeVisible();
});
