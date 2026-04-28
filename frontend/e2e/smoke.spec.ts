import { test, expect } from '@playwright/test';

test('homepage loads with title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Hybrid Trading/);
});

test('navigation has all sidebar links', async ({ page }) => {
  await page.goto('/');
  const links = ['Overview', 'Live Status', 'Market', 'Risk', 'Reports', 'Wiki'];
  for (const label of links) {
    await expect(page.getByRole('link', { name: label })).toBeVisible();
  }
});

test('graduation page shows metrics', async ({ page }) => {
  await page.goto('/graduation');
  await expect(page.getByText('Paper Graduation')).toBeVisible();
  await expect(page.getByText('Days Traded')).toBeVisible();
});
