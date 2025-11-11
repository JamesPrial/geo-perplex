const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

async function setup() {
  console.log('🚀 Starting Perplexity login setup...\n');

  // Launch browser in headful mode so user can interact
  const browser = await chromium.launch({
    headless: false,
    slowMo: 100 // Slight delay to make interactions visible
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });

  const page = await context.newPage();

  // Navigate to Perplexity
  console.log('📍 Navigating to Perplexity.ai...');
  await page.goto('https://www.perplexity.ai');

  // Wait a moment for the page to load
  await page.waitForTimeout(2000);

  console.log('\n✋ Please log into Perplexity in the browser window.');
  console.log('💡 Once you are logged in, press ENTER in this terminal to save your session...\n');

  // Wait for user to press Enter
  await waitForEnter();

  // Save the authentication state (cookies, localStorage, etc.)
  const authFile = path.join(__dirname, 'auth.json');
  await context.storageState({ path: authFile });

  console.log('\n✅ Authentication saved to auth.json');
  console.log('🎉 Setup complete! You can now use this auth in your scripts.\n');

  await browser.close();
}

function waitForEnter() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise((resolve) => {
    rl.question('', () => {
      rl.close();
      resolve();
    });
  });
}

// Run the setup
setup().catch(error => {
  console.error('❌ Error during setup:', error);
  process.exit(1);
});
