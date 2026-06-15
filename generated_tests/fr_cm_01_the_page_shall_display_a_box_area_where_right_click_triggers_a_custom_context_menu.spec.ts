import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-CM-01 The page shall display a box area where right-click triggers a custom context menu', async ({ page, context }) => {
  await page.goto('/context_menu', { waitUntil: 'domcontentloaded' });
  const box = page.locator('#hot-spot');
  await expect(box).toBeVisible();
  page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });
  await box.click({ button: 'right' });
});
