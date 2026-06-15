import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-GL-01 The page shall display heading "Geolocation" and a button labeled "Where am I?"', async ({ page, context }) => {
  await page.goto('/geolocation', { waitUntil: 'domcontentloaded' });
  await context.grantPermissions(['geolocation']);
  await context.setGeolocation({ latitude: 17.3850, longitude: 78.4867 });
  await expect(page.getByRole('heading', { name: /Geolocation/i })).toBeVisible();
  await page.getByRole('button', { name: /Where am I/i }).click();
  await expect(page.locator('#lat-value')).toBeVisible();
  await expect(page.locator('#long-value')).toBeVisible();
});
