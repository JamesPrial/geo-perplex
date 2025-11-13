# Source Extraction Investigation Scripts

This directory contains investigation scripts to determine how to properly extract source citations from Perplexity.ai search results.

## Problem Statement

The current source extraction in `src/search/extractor.py` is not working. The code attempts to extract sources using the selector `[data-testid*="source"] a`, but this may not be finding the correct elements.

## Investigation Approach

These scripts use the nodriver skill to explore Perplexity's UI in multiple ways:

1. **DOM Structure Investigation** - What selectors and attributes exist?
2. **Timing Analysis** - When do sources appear during the search lifecycle?
3. **Data Source Exploration** - Where is source data stored (DOM, React props, API responses)?

## Scripts

### 1. `investigate_sources.py` - DOM Structure Explorer

**Purpose**: Inspect all possible source-related elements in the DOM after a search completes.

**What it does**:
- Performs an automated search
- Tests 15+ different CSS selectors for sources
- Lists ALL links on the page with their attributes
- Uses JavaScript to find elements with "source", "citation", or "reference" keywords
- Keeps browser open for manual DevTools inspection

**Usage**:
```bash
python scripts/investigate_sources.py
```

**Expected Output**:
- List of selectors that found elements (✓) vs. didn't find elements (✗)
- Sample data from found elements (href, text, attributes)
- All links with their full attribute sets
- Elements containing source-related keywords

**What to look for**:
- Which selectors successfully find source elements?
- What attributes do source links have (data-testid, class, aria-label)?
- Are sources in a specific container element?
- Do sources have numbered citations (e.g., [1], [2])?

---

### 2. `investigate_source_timing.py` - Timing Monitor

**Purpose**: Determine WHEN sources appear during the search process.

**What it does**:
- Performs an automated search
- Monitors the page every 1 second for 30 seconds
- Tests multiple selectors at each interval
- Reports when each selector first found sources

**Usage**:
```bash
python scripts/investigate_source_timing.py
```

**Expected Output**:
- Timeline showing at what second each selector found elements
- First appearance time for each selector
- Recommendation for fastest/most reliable selector

**What to look for**:
- Do sources appear immediately or after a delay?
- Is there a specific timing we should wait for?
- Do different selectors become available at different times?
- Is our current wait logic sufficient?

---

### 3. `investigate_source_data.py` - Data Source Explorer

**Purpose**: Find WHERE source data is stored beyond just the DOM.

**What it does**:
- Explores React component props/state for source data
- Searches window object for API response data
- Checks data-* attributes on all elements
- Looks inside Shadow DOM
- Monitors network requests during search

**Usage**:
```bash
python scripts/investigate_source_data.py
```

**Expected Output**:
- React component data containing source information
- Window object properties with source/citation data
- Elements with relevant data-* attributes
- Shadow DOM elements with links
- API requests that might return source data

**What to look for**:
- Is source data available in JavaScript before it's rendered?
- Could we extract sources from API responses instead of DOM?
- Are sources in Shadow DOM (not accessible via normal selectors)?
- What data-* attributes identify source elements?

---

## Investigation Workflow

### Step 1: Run All Scripts

Run all three scripts and save their output:

```bash
python scripts/investigate_sources.py > sources_dom.txt
python scripts/investigate_source_timing.py > sources_timing.txt
python scripts/investigate_source_data.py > sources_data.txt
```

### Step 2: Manual Inspection

While scripts are running (they keep browser open):

1. **Open DevTools (F12)**
2. **Use Elements tab** to inspect source elements visually
3. **Look for**:
   - Citation numbers (e.g., [1], [2])
   - "Sources" section/footer
   - Link elements with source URLs
   - Containers around source groups

4. **In Console tab**, run:
   ```javascript
   // Find all external links
   $$('a[href^="http"]').map(a => ({
     text: a.textContent,
     href: a.href,
     parent: a.parentElement.tagName,
     testid: a.dataset.testid,
     classes: a.className
   }))
   ```

5. **In Network tab**:
   - Filter for "Fetch/XHR"
   - Look for API responses containing source URLs
   - Check response bodies for source data structure

### Step 3: Analyze Findings

Compare outputs from all three scripts:

1. **Which selectors work?**
   - Did any selectors consistently find sources?
   - What's the most reliable selector?

2. **What's the timing?**
   - When do sources appear?
   - Should we increase wait time?
   - Is content stability detection sufficient?

3. **Where's the data?**
   - Are sources in plain DOM, React state, or API responses?
   - Could we intercept API calls instead of scraping DOM?
   - Are there hidden data attributes we can use?

### Step 4: Document Findings

Create a summary document with:

1. **Correct selector(s)** for source extraction
2. **Timing requirements** (how long to wait)
3. **Extraction strategy** (DOM scraping vs. API interception)
4. **Example source elements** (HTML structure)
5. **Edge cases** to handle

## Common Findings (Template)

Fill this out after investigation:

```markdown
## Investigation Results

**Date**: [Date]
**Perplexity URL**: https://www.perplexity.ai
**Test Query**: "What is quantum computing?"

### Working Selectors

1. Selector: `[selector here]`
   - Found: [X] elements
   - First appeared: [X] seconds after search
   - Reliability: [High/Medium/Low]
   - Example HTML:
     ```html
     [paste example element]
     ```

### Timing

- Sources first appeared: [X] seconds after search submission
- Content stability achieved: [X] seconds
- Recommendation: Wait at least [X] seconds

### Data Structure

- Sources stored in: [DOM / React props / API response / Other]
- Container element: `[selector]`
- Individual source selector: `[selector]`
- Attributes present:
  - data-testid: [value]
  - class: [value]
  - aria-label: [value]

### Recommended Implementation

```python
# Pseudo-code for new extraction approach
# [Write recommended code here]
```

### Edge Cases

- [ ] No sources available (how to detect?)
- [ ] Sources load after long delay
- [ ] Multiple source formats (numbered vs. footer)
- [ ] Sources in expandable sections

```

## Troubleshooting

### Script won't run
- Ensure `auth.json` exists with valid cookies
- Check that browser can open (not on headless server)
- Verify Python dependencies installed

### No sources found
- Perplexity may have changed their UI
- Try different queries (some results have more sources)
- Check manually that sources appear when you search normally

### Browser crashes
- Reduce monitoring duration in timing script
- Close other applications to free memory
- Check Chrome is installed correctly

## Next Steps

After investigation is complete:

1. Update `src/config.py` with new selectors
2. Modify `src/search/extractor.py` extraction logic
3. Update timing/wait logic if needed
4. Add new extraction strategy if DOM scraping isn't viable
5. Test with multiple queries to verify reliability
