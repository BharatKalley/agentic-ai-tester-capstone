import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  page.setDefaultTimeout(15000);
});

test('FR-FA-02 Successful Login with Valid Credentials', async ({ page, context }) => {
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: /Login Page/i })).toBeVisible();
  await expect(page.locator('#username')).toBeVisible();
  await expect(page.locator('#password')).toBeVisible();
  await page.locator('#username').fill('tomsmith');
  await page.locator('#password').fill('SuperSecretPassword!');
  await page.getByRole('button', { name: /login/i }).click();
  await expect(page).toHaveURL(/secure/);
  await expect(page.locator('#flash')).toContainText(/logged into a secure area/i);
});
