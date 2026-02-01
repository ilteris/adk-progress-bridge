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
  await expect(page.getByTestId('status-badge')).toContainText('WS');
  const stopBtn = page.getByRole('button', { name: 'Stop Task' });
  await expect(stopBtn).toBeVisible();

  // Wait for completion
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId('status-badge')).toContainText('Done');

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
  await expect(page.getByTestId('status-badge')).toContainText('Awaiting Input');
  
  // Provide input "yes"
  const inputField = page.locator('input[placeholder="Type your response..."]');
  await inputField.fill('yes');
  await page.getByRole('button', { name: 'Send Response' }).click();
  
  // Wait for completion
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId('status-badge')).toContainText('Done');
  await expect(page.locator('pre')).toContainText('"status": "complete"');
  await expect(page.locator('pre')).toContainText('user approval');
});

test('websocket stop flow', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Enable WebSockets
  await page.locator('#useWS').check();
  
  // Set duration to 10 seconds to allow time to stop
  await page.locator('#duration').fill('10');
  
  // Start the task
  await page.getByRole('button', { name: 'Start Task' }).click();
  
  // Verify running state
  await expect(page.getByTestId('status-badge')).toContainText('WS');
  const stopBtn = page.getByRole('button', { name: 'Stop Task' });
  await expect(stopBtn).toBeVisible();
  
  // Stop the task
  await stopBtn.click();
  
  // Verify cancelled state
  await expect(page.getByTestId('status-badge')).toContainText('Cancelled');
  await expect(page.locator('.progress-bar')).toHaveCSS('background-color', 'rgb(108, 117, 125)'); // #6c757d
});

test('websocket dynamic tool fetching', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Initially on SSE (REST fetch)
  const toolSelect = page.locator('#toolSelect');
  // Real backend has 6 tools
  await expect(toolSelect.locator('option')).toHaveCount(7);
  
  // Toggle to WS
  await page.locator('#useWS').check();
  
  // Should still have options (re-fetched via WS)
  await expect(toolSelect.locator('option')).toHaveCount(7);
  await expect(toolSelect).toContainText('Long Audit');
});

test('websocket clear console flow', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Enable WebSockets
  await page.locator('#useWS').check();
  
  // Start a task to generate some logs
  await page.locator('#duration').fill('1');
  await page.getByRole('button', { name: 'Start Task' }).click();
  
  // Wait for completion
  await expect(page.getByTestId('status-badge')).toContainText('Done', { timeout: 15000 });
  
  // Verify logs exist
  const consoleDiv = page.locator('.bg-dark.text-light');
  const logEntries = consoleDiv.locator('div');
  const logCount = await logEntries.count();
  expect(logCount).toBeGreaterThan(1);
  
  // Click Clear
  await page.getByRole('button', { name: 'Clear' }).click();
  
  // Verify logs are cleared (back to "No logs yet...")
  await expect(logEntries).toHaveCount(1);
  await expect(consoleDiv).toContainText('No logs yet...');
});
