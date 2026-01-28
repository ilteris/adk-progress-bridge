import { test, expect } from '@playwright/test';

test('websocket audit flow', async ({ page }) => {
  // Navigate to the app
  await page.goto('http://localhost:5173');

  // Verify initial state
  await expect(page.locator('h4')).toHaveText('Task Monitor');
  
  // Enable WebSockets
  const wsToggle = page.locator('#useWS');
  await wsToggle.check();
  
  const startBtn = page.getByRole('button', { name: 'Start Task' });
  await expect(startBtn).toBeEnabled();

  // Set duration to 2 seconds
  const durationInput = page.locator('#duration');
  await durationInput.fill('2');

  // Start the task
  await startBtn.click();

  // Verify running state and WS badge
  await expect(page.locator('.badge')).toContainText('WS');
  const stopBtn = page.getByRole('button', { name: 'Stop Task' });
  await expect(stopBtn).toBeVisible();

  // Wait for completion
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('.badge')).toContainText('Done');

  // Verify final result
  await expect(page.locator('pre')).toContainText('"status": "complete"');
});

test('websocket interactive flow', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Enable WebSockets
  await page.locator('#useWS').check();
  
  // Select Interactive Task
  await page.locator('#toolSelect').selectOption('interactive_task');
  
  // Start task
  await page.getByRole('button', { name: 'Start Task' }).click();
  
  // Wait for input request
  await expect(page.getByText('Agent Input Request')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('.badge')).toContainText('Awaiting Input');
  
  // Provide input "yes"
  const inputField = page.locator('input[placeholder="Type your response..."]');
  await inputField.fill('yes');
  await page.getByRole('button', { name: 'Send Response' }).click();
  
  // Wait for completion
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('.badge')).toContainText('Done');
  await expect(page.locator('pre')).toContainText('"status": "complete"');
  await expect(page.locator('pre')).toContainText('user approval');
});
