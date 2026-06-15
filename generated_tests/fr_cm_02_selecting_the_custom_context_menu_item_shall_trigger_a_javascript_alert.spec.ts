import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-CM-02 Selecting the custom context menu item shall trigger a JavaScript alert', async ({ page, context }) => {
  await page.goto('/context_menu', { waitUntil: 'domcontentloaded' });
  const box = page.locator('#hot-spot');
  await expect(box).toBeVisible();
  page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });
  await box.click({ button: 'right' });
});
