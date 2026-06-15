import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-JE-01 The page shall contain a JavaScript error triggered on the onload event', async ({ page, context }) => {
  await page.goto('/javascript_error', { waitUntil: 'domcontentloaded' });
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.reload({ waitUntil: 'domcontentloaded' });
  expect(errors.length).toBeGreaterThan(0);
});
