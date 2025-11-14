"""
Configuration settings for GEO-Perplex automation tool
Centralizes all constants, timeouts, and selectors for easy maintenance
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class BrowserConfig:
    """Browser configuration with validation"""
    headless: bool = False  # Must be False - Perplexity blocks headless browsers
    args: List[str] = field(default_factory=lambda: ['--no-sandbox', '--disable-setuid-sandbox'])

    def __post_init__(self) -> None:
        """Validate configuration"""
        if self.headless:
            raise ValueError('Headless mode not supported - Perplexity blocks headless browsers')
        if not isinstance(self.args, list):
            raise ValueError('Browser args must be a list')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return asdict(self)


@dataclass
class TypingSpeedConfig:
    """Typing speed configuration for human-like behavior"""
    char_min: float = 0.05  # Minimum delay between characters (seconds)
    char_max: float = 0.15  # Maximum delay between characters (seconds)
    space_min: float = 0.1  # Minimum delay for space characters (seconds)
    space_max: float = 0.2  # Maximum delay for space characters (seconds)

    def __post_init__(self) -> None:
        """Validate typing speed ranges"""
        if self.char_min < 0 or self.char_max < 0:
            raise ValueError('Typing delays must be positive')
        if self.char_min > self.char_max:
            raise ValueError('char_min must be <= char_max')
        if self.space_min > self.space_max:
            raise ValueError('space_min must be <= space_max')


@dataclass
class DelayConfig:
    """Configuration for human-like delay patterns.

    Variance values control the spread of delay distributions:
    - Exponential distribution: variance affects tail length (longer variance = more outliers)
    - Gaussian distribution: variance is standard deviation

    Values chosen based on human reaction time research:
    - short (0.3): Quick reflexes, minimal variation
    - medium (0.5): Normal reactions, moderate variation
    - long (0.7): Deliberate actions, high variation
    """
    short_min: float = 0.3           # Short pause minimum (seconds)
    short_max: float = 0.7           # Short pause maximum (seconds)
    short_variance: float = 0.3      # Low variance for quick reactions

    medium_min: float = 0.5          # Medium pause minimum (seconds)
    medium_max: float = 1.5          # Medium pause maximum (seconds)
    medium_variance: float = 0.5     # Moderate variance for normal actions

    long_min: float = 1.0            # Long pause minimum (seconds)
    long_max: float = 2.5            # Long pause maximum (seconds)
    long_variance: float = 0.7       # High variance for deliberate actions

    def __post_init__(self) -> None:
        """Validate delay ranges"""
        if any(d < 0 for d in [self.short_min, self.short_max, self.medium_min,
                                self.medium_max, self.long_min, self.long_max]):
            raise ValueError('Delays must be positive')
        if any(v < 0 for v in [self.short_variance, self.medium_variance, self.long_variance]):
            raise ValueError('Variance values must be positive')
        if self.short_min > self.short_max:
            raise ValueError('short_min must be <= short_max')
        if self.medium_min > self.medium_max:
            raise ValueError('medium_min must be <= medium_max')
        if self.long_min > self.long_max:
            raise ValueError('long_min must be <= long_max')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            'short_min': self.short_min,
            'short_max': self.short_max,
            'short_variance': self.short_variance,
            'medium_min': self.medium_min,
            'medium_max': self.medium_max,
            'medium_variance': self.medium_variance,
            'long_min': self.long_min,
            'long_max': self.long_max,
            'long_variance': self.long_variance,
        }


@dataclass
class HumanBehaviorConfig:
    """Human-like behavior settings"""
    typing_speed: TypingSpeedConfig = field(default_factory=TypingSpeedConfig)
    delays: DelayConfig = field(default_factory=DelayConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return {
            'typing_speed': asdict(self.typing_speed),
            'delays': asdict(self.delays),
        }


@dataclass
class TimeoutConfig:
    """Timeout configuration with validation"""
    page_load: float = 10           # Page load timeout (seconds)
    element_select: float = 5       # Default element selection timeout (seconds)
    search_initiation: float = 10   # Wait for search to start (seconds)
    content_stability: float = 30   # Wait for content to stabilize (seconds)
    auth_verification: float = 5    # Authentication verification timeout (seconds)
    new_chat_navigation: float = 10 # Wait for new chat page to load (seconds)

    def __post_init__(self) -> None:
        """Validate timeouts are positive"""
        for field_name, value in asdict(self).items():
            if value <= 0:
                raise ValueError(f'Timeout {field_name} must be positive, got {value}')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return asdict(self)


@dataclass
class StabilityConfig:
    """Content stability detection configuration"""
    check_interval: float = 0.5     # How often to check for stability (seconds)
    stable_threshold: int = 3       # Number of consecutive stable checks required
    min_content_length: int = 50    # Minimum content length for valid answer (characters)

    def __post_init__(self) -> None:
        """Validate stability configuration"""
        if self.check_interval <= 0:
            raise ValueError('check_interval must be positive')
        if self.stable_threshold < 1:
            raise ValueError('stable_threshold must be at least 1')
        if self.min_content_length < 0:
            raise ValueError('min_content_length must be non-negative')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return asdict(self)


# Create instances for use throughout the application
_browser_config = BrowserConfig()
_human_behavior_config = HumanBehaviorConfig()
_timeout_config = TimeoutConfig()
_stability_config = StabilityConfig()

# Backward compatibility: expose as dictionaries
BROWSER_CONFIG = _browser_config.to_dict()
HUMAN_BEHAVIOR = _human_behavior_config.to_dict()
TIMEOUTS = _timeout_config.to_dict()
STABILITY_CONFIG = _stability_config.to_dict()

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
    'navigation_buttons': [
        'button[data-testid="sidebar-new-thread"]',  # New chat button (+ icon)
        'button[aria-label="New Thread"]',            # New chat by aria-label
        '[data-testid="sidebar-new-thread"]',         # Fallback without button tag
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
    'sources': {
        # Collapsible sources button selectors (button that says "X sources")
        'collapse_button': [
            'sources',              # Text-based search (most reliable) - use with page.find(text, best_match=True)
            'button:has-text("source")',  # CSS with text match
            '[class*="cursor-pointer"][class*="rounded-full"]',  # Class-based (from investigation)
        ],
        # Source link selectors after expansion
        'tier1_primary': 'a[href^="http"]',  # All HTTP/HTTPS links (works after expansion)
        'tier2_citations': '[class*="citation"] a, footer [class*="citation"] a',
        'tier3_references': 'main article a[href^="http"], [class*="reference"] a',
        'exclude_patterns': [
            'perplexity.ai',      # Internal links
            '/login',             # Auth links
            '/upgrade',           # Marketing links
            '/settings',          # Settings links
            '/pricing',           # Pricing links
            '/search',            # Search page links
            '/spaces',            # Spaces links
            '/home',              # Home page links
            '/discover',          # Discover page links
        ]
    },
}

# Text extraction markers
EXTRACTION_MARKERS = {
    'start': ['1 step completed', 'answer images', 'images '],
    'end': ['ask a follow-up', 'ask follow-up'],
    'ui_elements': ['Home Discover', 'Spaces Finance', 'Upgrade Install', 'Answer Images'],
    'skip_patterns': ['Home', 'Discover', 'Spaces', 'Finance', 'Install',
                      'Upgrade', 'Account', 'Ask a follow-up', 'Thinking...'],
}

# Source extraction configuration
# Controls how sources are extracted, validated, and deduplicated from search results
SOURCES_CONFIG = {
    'max_sources': 20,              # Increased from hard-coded 10
    'min_text_length': 3,           # Minimum text length for valid source
    'deduplicate': True,            # Remove duplicate URLs
    'extract_domain': True,         # Add domain field to metadata
    'extract_metadata': True,       # Extract additional metadata (title, snippet)
    'validate_external_only': True, # Only include external sources (not perplexity.ai)
    'tier_fallback_threshold': 3,   # Min sources before trying next tier
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

# Prompts file configuration
PROMPTS_FILE_CONFIG = {
    'max_prompts': 1000,  # Maximum number of prompts per file
    'required_fields': ['query'],  # Fields that must always be present
    'optional_fields': ['model', 'no_screenshot'],  # Fields that are optional
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

# Model selection configuration
# Discovered via UI inspection: Model selector is a button with circuit icon
# Located in the right side of search box (2nd button from left after globe/sources icon)
MODEL_SELECTOR = {
    # Textarea selector to find the search container
    'search_input': 'textarea',

    # Patterns to find the model selector button
    # Button is inside search container, right side, with circuit icon
    'selector_patterns': [
        'button[aria-label*="model" i]',
        'button[aria-label*="select" i]',
        'button[title*="model" i]',
        '[data-testid*="model"]',
        '[data-testid*="select"]',
    ],

    # After clicking, modal/dropdown appears with model options
    'options_container': [
        '[role="dialog"]',
        '[role="menu"]',
        '[role="listbox"]',
        '[class*="modal"]',
        '[class*="dropdown"]',
        '[class*="popup"]',
    ],

    # Model option items inside the container
    'option_item': [
        '[role="menuitem"]',
        '[role="option"]',
        'button',
        'div[role="button"]',
        'div[class*="option"]',
    ],

    'timeout': 5.0
}

# Model name mapping for user-friendly model selection
# Maps user-friendly CLI names to possible text variations in Perplexity's UI
# Values are lists to support multiple text variations
MODEL_MAPPING = {
    'gpt-4': ['GPT-4', 'GPT 4', 'gpt-4', 'GPT4'],
    'gpt-4-turbo': ['GPT-4 Turbo', 'GPT 4 Turbo', 'GPT-4 turbo'],
    'claude': ['Claude', 'claude'],
    'claude-3': ['Claude 3', 'Claude-3', 'Claude 3 Opus', 'Claude 3 Sonnet'],
    'claude-opus': ['Claude 3 Opus', 'Claude Opus', 'Opus'],
    'claude-sonnet': ['Claude 3 Sonnet', 'Claude Sonnet', 'Sonnet'],
    'sonar': ['Sonar', 'sonar'],
    'sonar-pro': ['Sonar Pro', 'Sonar-Pro'],
    'gemini': ['Gemini', 'gemini', 'Gemini Pro'],
    'default': ['Default', 'default'],
}

# New Chat Button Configuration
# Discovered selectors for the "New Thread" button (+ icon in sidebar)
# Used to navigate to a fresh chat page before starting a new search
NEW_CHAT_CONFIG = {
    'enabled': True,  # Global enable/disable for new chat navigation
    'selectors': [
        'button[data-testid="sidebar-new-thread"]',  # Primary selector with data-testid
        'button[aria-label="New Thread"]',            # Accessible button by aria-label
        '[data-testid="sidebar-new-thread"]',         # Fallback without button tag
        '[aria-label="New Thread"]',                  # Generic fallback by aria-label
    ],
    'timeout': 5.0,  # Timeout for finding the new chat button (seconds)
    'verify_navigation': True,  # Verify new chat page loaded successfully
    'verification_selectors': [
        '[contenteditable="true"]',      # Empty search box indicator
        'textarea[placeholder*="Ask"]',  # Search textarea with "Ask" placeholder
    ],
    'verification_poll_interval': 0.5,  # How often to poll for old content removal (seconds)
}

# Shutdown handling configuration
SHUTDOWN_CONFIG = {
    'cleanup_timeout': 5.0,  # Timeout per cleanup operation (seconds)
    'browser_cleanup_timeout': 5.0,  # Specific timeout for browser cleanup (seconds)
    'browser_kill_timeout': 3.0,  # Timeout for graceful browser termination (seconds)
    'enable_orphan_cleanup': True,  # Enable cleanup of orphaned browsers on startup
    'orphan_cleanup_patterns': ['chrome', 'chromium'],  # Browser process names to detect
}
