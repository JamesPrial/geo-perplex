"""
Configuration settings for GEO-Perplex automation tool
Centralizes all constants, timeouts, and selectors for easy maintenance
"""

# Browser Configuration
BROWSER_CONFIG = {
    'headless': False,  # Must be False - Perplexity blocks headless browsers
    'args': ['--no-sandbox', '--disable-setuid-sandbox'],
}

# Human-like behavior settings
HUMAN_BEHAVIOR = {
    'typing_speed': {
        'char_min': 0.05,  # Minimum delay between characters (seconds)
        'char_max': 0.15,  # Maximum delay between characters (seconds)
        'space_min': 0.1,  # Minimum delay for space characters (seconds)
        'space_max': 0.2,  # Maximum delay for space characters (seconds)
    },
    'delays': {
        'short_min': 0.3,    # Short pause minimum (seconds)
        'short_max': 0.7,    # Short pause maximum (seconds)
        'medium_min': 0.5,   # Medium pause minimum (seconds)
        'medium_max': 1.5,   # Medium pause maximum (seconds)
        'long_min': 1.0,     # Long pause minimum (seconds)
        'long_max': 2.5,     # Long pause maximum (seconds)
    },
}

# Timeouts
TIMEOUTS = {
    'page_load': 10,           # Page load timeout (seconds)
    'element_select': 5,       # Default element selection timeout (seconds)
    'search_initiation': 10,   # Wait for search to start (seconds)
    'content_stability': 30,   # Wait for content to stabilize (seconds)
    'auth_verification': 5,    # Authentication verification timeout (seconds)
}

# Content stability detection
STABILITY_CONFIG = {
    'check_interval': 0.5,     # How often to check for stability (seconds)
    'stable_threshold': 3,     # Number of consecutive stable checks required
    'min_content_length': 50,  # Minimum content length for valid answer (characters)
}

# Element selectors
SELECTORS = {
    'search_input': [
        '[contenteditable="true"]',
        'textarea[placeholder*="Ask"]',
        '[role="textbox"]',
        'div[contenteditable="true"]',
        'textarea',
    ],
    'search_button': [
        'button[type="submit"]',
        'button[aria-label*="search" i]',
        'button[aria-label*="submit" i]',
        'button[title*="search" i]',
        'button svg',
        'button[class*="search" i]',
    ],
    'auth_indicators': [
        '[data-testid="sidebar-new-thread"]',  # New Thread button
        '[data-testid="sidebar-home"]',         # Home navigation
        '[aria-label="New Thread"]',            # New Thread button by aria-label
        '[aria-label="Account"]',               # Account button
    ],
    'loading_indicators': [
        '[class*="thinking" i]',
        '[class*="loading" i]',
        '[class*="generating" i]',
        '[class*="spinner" i]',
        '[class*="animate" i]',
        '[data-testid*="answer"]',
        'main [class*="response" i]',
    ],
    'sources': '[data-testid*="source"] a, footer a[href*="http"]',
}

# Text extraction markers
EXTRACTION_MARKERS = {
    'start': ['1 step completed', 'answer images', 'images '],
    'end': ['ask a follow-up', 'ask follow-up'],
    'ui_elements': ['Home Discover', 'Spaces Finance', 'Upgrade Install', 'Answer Images'],
    'skip_patterns': ['Home', 'Discover', 'Spaces', 'Finance', 'Install',
                      'Upgrade', 'Account', 'Ask a follow-up', 'Thinking...'],
}

# Required cookies for authentication
REQUIRED_COOKIES = [
    'pplx.session-id',
    '__Secure-next-auth.session-token',
]

# Cookie defaults
COOKIE_DEFAULTS = {
    'domain': '.perplexity.ai',
    'path': '/',
    'secure': False,
    'httpOnly': False,
    'sameSite': 'Lax',
}

# Retry configuration
RETRY_CONFIG = {
    'max_attempts': 3,
    'base_delay': 1.0,      # Base delay between retries (seconds)
    'exponential': True,    # Use exponential backoff
    'backoff_factor': 2.0,  # Multiply delay by this factor each retry
}

# Screenshot settings
SCREENSHOT_CONFIG = {
    'directory': 'screenshots',
    'full_page': True,
    'format': 'png',
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
}

# Database settings
DATABASE_CONFIG = {
    'path': 'search_results.db',
    'timeout': 10.0,
}

# User agent strings for randomization
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Viewport sizes for randomization
VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1280, 'height': 720},
]
