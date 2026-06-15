import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-HS-01 The page shall show a horizontal slider control and an associated value indicator t', async ({ page, context }) => {
  await page.goto('/horizontal_slider', { waitUntil: 'domcontentloaded' });
  const slider = page.locator('input[type=range]');
  await expect(slider).toBeVisible();
  await slider.focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('#range')).not.toHaveText('0');
});
