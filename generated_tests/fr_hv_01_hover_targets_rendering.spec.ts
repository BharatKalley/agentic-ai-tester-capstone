import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-HV-01 Hover Targets Rendering', async ({ page, context }) => {
  await page.goto('/hovers', { waitUntil: 'domcontentloaded' });
  const figures = page.locator('.figure');
  await expect(figures).toHaveCount(3);
  await figures.first().hover();
  await expect(page.getByText(/name: user1/i)).toBeVisible();
  await expect(page.getByRole('link', { name: /View profile/i }).first()).toBeVisible();
});
