# GEO Perplex

A tool for researching Generative Engine Optimization (GEO) using Perplexity.ai and Playwright.

## What is GEO?

Generative Engine Optimization (GEO) is an emerging field, analogous to SEO. Where SEO focuses on a product's placement on search engines like Google, GEO is concerned with the likelihood an LLM suggests your product.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Install Playwright browsers:
```bash
npx playwright install chromium
```

3. Run the setup script to log into Perplexity and save your session:
```bash
npm run setup
```

This will:
- Open a browser window
- Navigate to Perplexity.ai
- Wait for you to log in
- Save your authentication cookies to `auth.json`

## Usage

Once you've run the setup script, your authentication state is saved in `auth.json`. You can use this in your Playwright scripts to run automated searches without logging in each time.

Example:
```javascript
const { chromium } = require('playwright');

async function runSearch() {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    storageState: 'auth.json' // Load saved auth
  });
  const page = await context.newPage();

  // Your Perplexity automation here
  await page.goto('https://www.perplexity.ai');

  await browser.close();
}
```

## Security

The `auth.json` file contains your authentication cookies and is ignored by git. Do not commit this file to version control.
