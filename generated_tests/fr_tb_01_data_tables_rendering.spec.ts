import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-TB-01 Data Tables Rendering', async ({ page, context }) => {
  await page.goto('/tables', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Data Tables/i })).toBeVisible();
  await expect(page.locator('table')).toHaveCount(2);
  await expect(page.locator('table').first()).toContainText('Last Name');
  await expect(page.locator('table').first()).toContainText('edit');
  await expect(page.locator('table').first()).toContainText('delete');
});
