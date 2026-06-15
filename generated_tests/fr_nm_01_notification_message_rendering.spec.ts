import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-NM-01 Notification Message Rendering', async ({ page, context }) => {
  await page.goto('/notification_message_rendered', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Notification Message/i })).toBeVisible();
  await expect(page.locator('#flash')).toBeVisible();
  await page.getByRole('link', { name: /Click here to load a new message/i }).click();
  await expect(page.locator('#flash')).toBeVisible();
});
