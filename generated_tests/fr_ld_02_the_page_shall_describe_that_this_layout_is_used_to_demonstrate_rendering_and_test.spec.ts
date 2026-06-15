import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-LD-02 The page shall describe that this layout is used to demonstrate rendering and test', async ({ page, context }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Welcome to the-internet/i })).toBeVisible();
  await expect(page.getByText('Available Examples')).toBeVisible();
  await expect(page.getByRole('link', { name: 'A/B Testing' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Add/Remove Elements' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Checkboxes' })).toBeVisible();
});
