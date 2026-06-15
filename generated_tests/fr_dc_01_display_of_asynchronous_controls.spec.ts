import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-DC-01 Display of Asynchronous Controls', async ({ page, context }) => {
  await page.goto('/dynamic_controls', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Dynamic Controls/i })).toBeVisible();
  await expect(page.locator('#checkbox')).toBeVisible();
  await expect(page.getByRole('button', { name: /Remove/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /Enable/i })).toBeVisible();
});
