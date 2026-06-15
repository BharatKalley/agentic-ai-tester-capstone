import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './generated_tests',
  timeout: 30000,
  retries: 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['json', { outputFile: 'reports/playwright-report.json' }]],
  use: {
    baseURL: 'https://the-internet.herokuapp.com',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }]
});
