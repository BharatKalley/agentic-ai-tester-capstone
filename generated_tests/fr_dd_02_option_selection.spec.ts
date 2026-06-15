import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-DD-02 Option Selection', async ({ page, context }) => {
  await page.goto('/dropdown', { waitUntil: 'domcontentloaded' });
  const dropdown = page.locator('#dropdown');
  await expect(dropdown).toBeVisible();
  await expect(dropdown).toContainText('Option 1');
  await expect(dropdown).toContainText('Option 2');
  await dropdown.selectOption({ label: 'Option 1' });
  await expect(dropdown).toHaveValue('1');
});
