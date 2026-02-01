import { test, expect } from '@playwright/test';

test('full audit flow', async ({ page }) => {
  // Navigate to the app
  await page.goto('http://localhost:5173');

  // Verify initial state
  await expect(page.locator('h4')).toHaveText('Task Monitor');
  const startBtn = page.getByRole('button', { name: 'Start Task' });
  await expect(startBtn).toBeEnabled();

  // Set duration to 2 seconds for faster test
  const durationInput = page.locator('#duration');
  await durationInput.fill('2');

  // Start the audit
  await startBtn.click();

  // Verify running state
  const stopBtn = page.getByRole('button', { name: 'Stop Task' });
  await expect(stopBtn).toBeVisible();
  await expect(page.getByTestId('status-badge')).toContainText('Live');

  // Wait for completion (look for the "Done" badge or the result alert)
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId('status-badge')).toContainText('Done');

  // Verify final result
  await expect(page.locator('pre')).toContainText('"status": "complete"');
  await expect(startBtn).toBeEnabled();
});