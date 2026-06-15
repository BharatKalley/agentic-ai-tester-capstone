import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-JA-02 Basic Alert Trigger', async ({ page, context }) => {
  await page.goto('/javascript_alerts', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /JavaScript Alerts/i })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Click for JS Alert' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Click for JS Confirm' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Click for JS Prompt' })).toBeVisible();
  page.once('dialog', async dialog => { expect(dialog.type()).toBe('alert'); await dialog.accept(); });
  await page.getByRole('button', { name: 'Click for JS Alert' }).click();
  await expect(page.locator('#result')).toContainText(/successfully/i);
});
