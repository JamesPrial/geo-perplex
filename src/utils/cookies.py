"""
Cookie management utilities for GEO-Perplex
Handles cookie loading, validation, expiry checking, and CDP format conversion
"""

import json
import os
import time
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import nodriver as uc

from src.config import REQUIRED_COOKIES, COOKIE_DEFAULTS

logger = logging.getLogger(__name__)


@dataclass
class Cookie:
    """
    Represents a single HTTP cookie with validation and expiry checking.

    Attributes:
        name: Cookie name
        value: Cookie value
        domain: Domain for which cookie is valid
        path: Path for which cookie is valid (default: "/")
        expires: Unix timestamp of expiration (None for session cookies)
        secure: Only send over HTTPS
        http_only: Not accessible from JavaScript (httpOnly attribute)
        same_site: SameSite attribute ("Strict", "Lax", "None")
    """
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: Optional[float] = None
    secure: bool = False
    http_only: bool = False
    same_site: str = "Lax"

    def __post_init__(self) -> None:
        """Validate and normalize cookie data"""
        if not self.name:
            raise ValueError('Cookie name cannot be empty')
        if not self.value:
            raise ValueError('Cookie value cannot be empty')
        if not self.domain:
            raise ValueError('Cookie domain cannot be empty')

        # Normalize domain (remove leading dot)
        self.domain = self._normalize_domain(self.domain)

        # Validate same_site
        if self.same_site not in ['Strict', 'Lax', 'None', 'strict', 'lax', 'none']:
            logger.warning(f'Invalid sameSite value "{self.same_site}", defaulting to "Lax"')
            self.same_site = 'Lax'

        # Validate expires if present
        if self.expires is not None:
            if self.expires < 0:
                raise ValueError('Cookie expires must be non-negative')

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        """Normalize domain - preserve leading dot for cookie domains"""
        if not domain or domain == ".":
            raise ValueError('Domain cannot be empty')
        return domain  # Don't strip the leading dot!

    @property
    def is_session_cookie(self) -> bool:
        """Return True if this is a session cookie (no expiry)"""
        return self.expires is None

    @property
    def is_persistent_cookie(self) -> bool:
        """Return True if this is a persistent cookie (has expiry)"""
        return self.expires is not None

    def is_expired(self) -> bool:
        """Check if cookie has expired based on current time"""
        if self.is_session_cookie:
            return False
        return time.time() > self.expires

    def time_until_expiry(self) -> Optional[int]:
        """Return seconds until cookie expires, or None if session cookie"""
        if self.is_session_cookie:
            return None
        remaining = self.expires - time.time()
        return max(0, int(remaining))

    def to_dict(self) -> Dict[str, Any]:
        """Convert cookie to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "path": self.path,
            "expires": self.expires,
            "secure": self.secure,
            "httpOnly": self.http_only,
            "sameSite": self.same_site,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cookie":
        """
        Create a Cookie from a dictionary with validation.

        Args:
            data: Dictionary with cookie data

        Returns:
            Cookie instance

        Raises:
            ValueError: If required fields (name, value) are missing or empty

        Example:
            >>> cookie_data = {'name': 'session', 'value': 'abc123', 'domain': '.example.com'}
            >>> cookie = Cookie.from_dict(cookie_data)
        """
        # Validate required fields before construction
        name = data.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"Cookie missing or invalid 'name' field. "
                f"Got: {repr(name)} in data: {data}"
            )

        value = data.get("value")
        if not value or not isinstance(value, str):
            # Note: Empty string value might be valid for deletion cookies,
            # but None or missing is not acceptable
            raise ValueError(
                f"Cookie missing or invalid 'value' field. "
                f"Got: {repr(value)} in data: {data}"
            )

        # Proceed with construction using validated values
        return cls(
            name=name,  # No default, validated above
            value=value,  # No default, validated above
            domain=data.get("domain", COOKIE_DEFAULTS['domain']),
            path=data.get("path", COOKIE_DEFAULTS['path']),
            expires=data.get("expires") or data.get("expirationDate"),
            secure=data.get("secure", COOKIE_DEFAULTS['secure']),
            http_only=data.get("httpOnly", COOKIE_DEFAULTS['httpOnly']),
            same_site=data.get("sameSite", COOKIE_DEFAULTS['sameSite']),
        )

    def to_cdp_format(self) -> Dict[str, Any]:
        """
        Convert cookie to CDP (Chrome DevTools Protocol) format for nodriver

        Returns:
            Dictionary with CDP-compatible parameters for page.send(uc.cdp.network.set_cookie(...))
        """
        cdp_cookie = {
            'name': self.name,
            'value': self.value,
            'domain': self.domain,
            'path': self.path,
            'secure': self.secure,
            'http_only': self.http_only,
        }

        # Add same_site if present
        if self.same_site:
            cdp_cookie['same_site'] = uc.cdp.network.CookieSameSite(self.same_site)

        # Add expires if present (must be positive)
        if self.expires and self.expires > 0:
            cdp_cookie['expires'] = uc.cdp.network.TimeSinceEpoch(self.expires)

        return cdp_cookie

    def matches_domain(self, domain: str) -> bool:
        """Check if cookie applies to the given domain"""
        normalized = self._normalize_domain(domain)
        return normalized.endswith(self.domain) or normalized == self.domain

    def __repr__(self) -> str:
        """String representation for debugging"""
        expiry_info = (
            f"expires in {self.time_until_expiry()}s"
            if self.is_persistent_cookie
            else "session"
        )
        value_preview = self.value[:20] + "..." if len(self.value) > 20 else self.value
        return f"Cookie({self.name}={value_preview}, {self.domain}, {expiry_info})"


class CookieManager:
    """
    Manages cookies with validation, expiry checking, and persistence

    Provides methods to:
    - Load cookies from JSON files
    - Save cookies to JSON files
    - Filter expired cookies
    - Get critical authentication cookies
    - Validate required cookies are present
    """

    def __init__(self, cookies: Optional[List[Cookie]] = None) -> None:
        """
        Initialize cookie manager

        Args:
            cookies: Optional initial list of Cookie objects
        """
        self.cookies: List[Cookie] = cookies or []

    def load_from_file(self, file_path: Optional[str] = None) -> int:
        """
        Load cookies from auth.json file

        Args:
            file_path: Path to the auth.json file (defaults to root auth.json)

        Returns:
            Number of cookies loaded

        Raises:
            FileNotFoundError: If the auth.json file is not found
            ValueError: If the cookie format is invalid
            json.JSONDecodeError: If the JSON is malformed
        """
        cookie_path = file_path or os.path.join(os.getcwd(), 'auth.json')

        try:
            with open(cookie_path, 'r', encoding='utf-8-sig') as f:
                cookie_data = f.read()
                cookies_json = json.loads(cookie_data)

            if not isinstance(cookies_json, list) or len(cookies_json) == 0:
                raise ValueError('Invalid cookie format: expected non-empty array')

            # Convert to Cookie objects
            self.cookies = []
            for cookie_dict in cookies_json:
                try:
                    cookie = Cookie.from_dict(cookie_dict)
                    self.cookies.append(cookie)
                except Exception as e:
                    logger.warning(f'Skipping invalid cookie: {e}')
                    continue

            logger.info(f"Loaded {len(self.cookies)} cookies from {cookie_path}")
            print(f"✓ Loaded {len(self.cookies)} cookies from {cookie_path}")
            return len(self.cookies)

        except UnicodeDecodeError:
            raise ValueError(
                f"Cookie file appears to be binary or not UTF-8 encoded: {cookie_path}\n"
                "Please ensure the file is a valid JSON text file."
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Cookie file not found: {cookie_path}\n"
                "Please run the cookie extraction script first or check the file path."
            )

    def save_to_file(self, file_path: str) -> None:
        """
        Save cookies to JSON file

        Args:
            file_path: Path to save cookies to
        """
        # Only save non-expired persistent cookies
        valid_cookies = [c for c in self.cookies if not c.is_expired()]

        data = {
            "saved_at": datetime.now().isoformat(),
            "cookies": [c.to_dict() for c in valid_cookies],
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(valid_cookies)} cookies to {file_path}")

    def filter_expired(self) -> int:
        """
        Remove all expired cookies

        Returns:
            Number of cookies removed
        """
        original_count = len(self.cookies)
        self.cookies = [c for c in self.cookies if not c.is_expired()]
        removed = original_count - len(self.cookies)

        if removed > 0:
            logger.info(f"Removed {removed} expired cookies")

        return removed

    def get_critical_cookies(self) -> List[Cookie]:
        """
        Get only the required authentication cookies

        Returns:
            List of Cookie objects that are in REQUIRED_COOKIES list
        """
        return [c for c in self.cookies if c.name in REQUIRED_COOKIES]

    def validate(self) -> bool:
        """
        Validate that all required cookies are present and not expired

        Returns:
            True if all required cookies are present and valid, False otherwise
        """
        # Filter expired first
        self.filter_expired()

        cookie_names = [c.name for c in self.cookies]
        has_all_required = all(name in cookie_names for name in REQUIRED_COOKIES)

        if not has_all_required:
            missing = [name for name in REQUIRED_COOKIES if name not in cookie_names]
            logger.warning(f'Missing required authentication cookies: {missing}')
            logger.info(f'Required: {REQUIRED_COOKIES}')
            logger.info(f'Found: {cookie_names}')
            print(f"⚠ Warning: Missing required authentication cookies: {', '.join(missing)}")
            print(f"  Required: {', '.join(REQUIRED_COOKIES)}")
            print(f"  Found: {', '.join(cookie_names)}")
            return False

        logger.info(f'All {len(REQUIRED_COOKIES)} required authentication cookies present')
        print(f"✓ All required authentication cookies present")
        return True

    def get_all(self) -> List[Cookie]:
        """Get all cookies"""
        return self.cookies.copy()

    def get_for_domain(self, domain: str) -> List[Cookie]:
        """
        Get all valid cookies for a specific domain

        Args:
            domain: Domain to filter cookies for

        Returns:
            List of valid, non-expired cookies for the domain
        """
        return [c for c in self.cookies if c.matches_domain(domain) and not c.is_expired()]

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert all cookies to list of dictionaries (for backward compatibility)

        Returns:
            List of cookie dictionaries in original format
        """
        return [c.to_dict() for c in self.cookies]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored cookies

        Returns:
            Dictionary with session/persistent count, expiry info, etc.
        """
        session_cookies = [c for c in self.cookies if c.is_session_cookie]
        persistent_cookies = [c for c in self.cookies if c.is_persistent_cookie]
        expired_cookies = [c for c in persistent_cookies if c.is_expired()]

        return {
            "total_cookies": len(self.cookies),
            "session_cookies": len(session_cookies),
            "persistent_cookies": len(persistent_cookies),
            "expired_cookies": len(expired_cookies),
            "valid_cookies": len(self.cookies) - len(expired_cookies),
            "critical_cookies": len(self.get_critical_cookies()),
        }


# Backward compatibility functions

def load_cookies(auth_file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load cookies from auth.json file (backward compatible function)

    Args:
        auth_file_path: Path to the auth.json file (defaults to root auth.json)

    Returns:
        List of cookie dictionaries ready for Nodriver

    Raises:
        FileNotFoundError: If the auth.json file is not found
        ValueError: If the cookie format is invalid
        json.JSONDecodeError: If the JSON is malformed
    """
    cookie_path = auth_file_path or os.path.join(os.getcwd(), 'auth.json')

    try:
        with open(cookie_path, 'r', encoding='utf-8-sig') as f:
            cookie_data = f.read()
            cookies_json = json.loads(cookie_data)

        if not isinstance(cookies_json, list) or len(cookies_json) == 0:
            raise ValueError('Invalid cookie format: expected non-empty array')

        # Return raw dictionaries without validation
        print(f"✓ Loaded {len(cookies_json)} cookies from {cookie_path}")
        return cookies_json

    except UnicodeDecodeError:
        raise ValueError(
            f"Cookie file appears to be binary or not UTF-8 encoded: {cookie_path}\n"
            "Please ensure the file is a valid JSON text file."
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Cookie file not found: {cookie_path}\n"
            "Please run the cookie extraction script first or check the file path."
        )


def validate_auth_cookies(cookies: List[Dict[str, Any]]) -> bool:
    """
    Validate that required Perplexity authentication cookies are present (backward compatible)

    Args:
        cookies: List of cookie dictionaries to validate

    Returns:
        True if essential authentication cookies are present, False otherwise
    """
    # Extract cookie names from raw dictionaries (handle malformed data gracefully)
    cookie_names = []
    for cookie_dict in cookies:
        if isinstance(cookie_dict, dict):
            name = cookie_dict.get('name')
            if isinstance(name, str):  # Only add valid string names
                cookie_names.append(name)
        # Skip non-dict items and items with non-string names

    # Check if all required cookies are present
    has_all_required = all(name in cookie_names for name in REQUIRED_COOKIES)

    if not has_all_required:
        missing = [name for name in REQUIRED_COOKIES if name not in cookie_names]
        logger.warning(f'Missing required authentication cookies: {missing}')
        logger.info(f'Required: {REQUIRED_COOKIES}')
        logger.info(f'Found: {cookie_names}')
        print(f"⚠ Warning: Missing required authentication cookies")
        print(f"  Required: {', '.join(REQUIRED_COOKIES)}")
        print(f"  Found: {', '.join(str(n) for n in cookie_names)}")
        return False

    logger.info(f'All {len(REQUIRED_COOKIES)} required authentication cookies present')
    print(f"✓ All required authentication cookies present")
    return True
