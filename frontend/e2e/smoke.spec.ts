import { test, expect } from '@playwright/test';

test('homepage loads with title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Hybrid Trading/);
});

test('navigation has all sidebar links', async ({ page }) => {
  await page.goto('/');
  const links = ['Overview', 'Live Status', 'Market', 'Risk', 'Reports', 'Wiki', 'Paper Graduation'];
  for (const label of links) {
    await expect(page.getByRole('link', { name: label })).toBeVisible();
  }
});

test('graduation page shows metrics', async ({ page }) => {
  await page.goto('/graduation');
  await expect(page.getByText('Paper Graduation')).toBeVisible();
  await expect(page.getByText('Days Traded')).toBeVisible();
  await expect(page.getByText('Gates')).toBeVisible();
});

test('live page has sub-strategy cards', async ({ page }) => {
  await page.goto('/live');
  await expect(page.getByText('Live Status')).toBeVisible();
  // Check for strategy card labels
  await expect(page.getByText('RegimeEnsemble')).toBeVisible();
});

test('risk page shows metrics', async ({ page }) => {
  await page.goto('/risk');
  await expect(page.getByText('Risk Monitor')).toBeVisible();
  await expect(page.getByText('VaR 95%')).toBeVisible();
  await expect(page.getByText('Max Drawdown')).toBeVisible();
});

test('reports page has stats and date filter', async ({ page }) => {
  await page.goto('/reports');
  await expect(page.getByText('Daily Reports')).toBeVisible();
  // Check date inputs exist
  await expect(page.locator('input[type="date"]').first).toBeVisible();
});

test('wiki page has search and categories', async ({ page }) => {
  await page.goto('/wiki');
  await expect(page.getByText('Trading Wiki')).toBeVisible();
  await expect(page.getByPlaceholder(/Search/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'All' })).toBeVisible();
});

test('wiki semantic search toggle works', async ({ page }) => {
  await page.goto('/wiki');
  await expect(page.getByRole('button', { name: 'Semantic' })).toBeVisible();
  await page.getByRole('button', { name: 'Semantic' }).click();
  await expect(page.getByText(/semantic search uses AI/i)).toBeVisible();
});

test('market page has symbol tabs', async ({ page }) => {
  await page.goto('/market');
  await expect(page.getByText('Market')).toBeVisible();
  await expect(page.getByRole('button', { name: /Bitcoin/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Ethereum/ })).toBeVisible();
});
