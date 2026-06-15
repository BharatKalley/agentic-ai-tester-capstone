import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-WIN-01 /windows shall display text "Opening a new window" and a link "Click Here".', async ({ page, context }) => {
  await page.goto('/windows', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Opening a new window/i })).toBeVisible();
  const popupPromise = page.waitForEvent('popup');
  await page.getByRole('link', { name: /Click Here/i }).click();
  const popup = await popupPromise;
  await expect(popup.locator('body')).toContainText('New Window');
});
