import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-EA-03 Re-enable Ad', async ({ page, context }) => {
  await page.goto('/entry_ad', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Entry Ad/i })).toBeVisible();
  const modal = page.locator('.modal');
  await expect(modal).toBeVisible();
  await page.getByText('Close').click();
  await expect(modal).toBeHidden();
});
