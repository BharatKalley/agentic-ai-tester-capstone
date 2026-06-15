import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-CB-02 Checkbox State Toggle', async ({ page, context }) => {
  await page.goto('/checkboxes', { waitUntil: 'domcontentloaded' });
  const boxes = page.locator('input[type=checkbox]');
  await expect(boxes).toHaveCount(2);
  const first = boxes.first();
  const before = await first.isChecked();
  await first.click();
  expect(await first.isChecked()).toBe(!before);
});
