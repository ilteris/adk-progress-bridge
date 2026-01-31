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

test('websocket stop flow', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Enable WebSockets
  await page.locator('#useWS').check();
  
  // Set duration to 10 seconds to allow time to stop
  await page.locator('#duration').fill('10');
  
  // Start the task
  await page.getByRole('button', { name: 'Start Task' }).click();
  
  // Verify running state
  await expect(page.locator('.badge')).toContainText('WS');
  const stopBtn = page.getByRole('button', { name: 'Stop Task' });
  await expect(stopBtn).toBeVisible();
  
  // Stop the task
  await stopBtn.click();
  
  // Verify cancelled state
  await expect(page.locator('.badge')).toContainText('Cancelled');
  await expect(page.locator('.progress-bar')).toHaveCSS('background-color', 'rgb(108, 117, 125)'); // #6c757d
});

test('websocket dynamic tool fetching', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Initially on SSE (REST fetch)
  const toolSelect = page.locator('#toolSelect');
  // Real backend now has 9 tools (added dynamic_echo_tool and multi_input_task)
  await expect(toolSelect.locator('option')).toHaveCount(9);
  
  // Toggle to WS
  await page.locator('#useWS').check();
  
  // Should still have options (re-fetched via WS)
  await expect(toolSelect.locator('option')).toHaveCount(9);
  await expect(toolSelect).toContainText('Long Audit');
});

test('websocket parameter flow', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Enable WebSockets
  await page.locator('#useWS').check();
  
  // Select Dynamic Echo Tool
  await page.locator('#toolSelect').selectOption('dynamic_echo_tool');
  
  // Fill custom message and repeat
  const msgInput = page.locator('#echoMessage');
  const repeatInput = page.locator('#echoRepeat');
  
  await msgInput.fill('E2E Test Message');
  await repeatInput.fill('2');
  
  // Start task
  await page.getByRole('button', { name: 'Start Task' }).click();
  
  // Wait for progress
  await expect(page.getByText('Echoing 1/2')).toBeVisible();
  await expect(page.getByText('Message: E2E Test Message')).toBeVisible();
  
  // Wait for completion
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 10000 });
  await expect(page.locator('pre')).toContainText('"echoed": "E2E Test Message"');
  await expect(page.locator('pre')).toContainText('"count": 2');
});

test('websocket multi-input flow', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Enable WebSockets
  await page.locator('#useWS').check();
  
  // Select Multi Input Task
  await page.locator('#toolSelect').selectOption('multi_input_task');
  
  // Start task
  await page.getByRole('button', { name: 'Start Task' }).click();
  
  // Wait for first input request (Name)
  await expect(page.locator('strong', { hasText: 'What is your name?' })).toBeVisible({ timeout: 15000 });
  const inputField = page.locator('input[placeholder="Type your response..."]');
  await inputField.fill('Adele');
  await page.getByRole('button', { name: 'Send Response' }).click();
  
  // Wait for second input request (Color)
  await expect(page.locator('strong', { hasText: 'what is your favorite color?' })).toBeVisible({ timeout: 15000 });
  await inputField.fill('Blue');
  await page.getByRole('button', { name: 'Send Response' }).click();
  
  // Wait for completion
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('.badge')).toContainText('Done');
  await expect(page.locator('pre')).toContainText('"user_name": "Adele"');
  await expect(page.locator('pre')).toContainText('"favorite_color": "Blue"');
});