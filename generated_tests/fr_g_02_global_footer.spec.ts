import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-G-02 Global Footer', async ({ page, context }) => {
  await page.goto('/checkboxes', { waitUntil: 'domcontentloaded' });
  const boxes = page.locator('input[type=checkbox]');
  await expect(boxes).toHaveCount(2);
});
