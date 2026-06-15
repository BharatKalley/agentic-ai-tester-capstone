import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-ARE-01 Add Element Button', async ({ page, context }) => {
  await page.goto('/add_remove_elements/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Add.Remove Elements/i })).toBeVisible();
  await page.getByRole('button', { name: /Add Element/i }).click();
  const del = page.getByRole('button', { name: /Delete/i });
  await expect(del).toHaveCount(1);
  await del.click();
  await expect(page.getByRole('button', { name: /Delete/i })).toHaveCount(0);
});
