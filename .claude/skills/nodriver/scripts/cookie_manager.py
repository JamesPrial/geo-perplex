"""
Cookie management system for nodriver browser instances.

This module provides a complete cookie management solution with:
- JSON-based persistence across browser restarts
- Automatic expiry checking and cleanup
- Domain-specific filtering and organization
- Session vs persistent cookie handling
- Cookie jar management for multiple domains
- Direct integration with nodriver browser instances
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class Cookie:
    """
    Represents a single HTTP cookie with validation and expiry checking.

    A cookie can be either session-based (deleted on browser close) or
    persistent (stored and retrieved across sessions).
    """

    def __init__(
        self,
        name: str,
        value: str,
        domain: str,
        path: str = "/",
        expires: Optional[int] = None,
        secure: bool = False,
        http_only: bool = False,
        same_site: str = "Lax",
    ) -> None:
        """
        Initialize a cookie.

        Args:
            name: Cookie name
            value: Cookie value
            domain: Domain for which cookie is valid
            path: Path for which cookie is valid (default: "/")
            expires: Unix timestamp of expiration (None for session cookies)
            secure: Only send over HTTPS
            http_only: Not accessible from JavaScript
            same_site: SameSite attribute ("Strict", "Lax", "None")
        """
        self.name = name
        self.value = value
        self.domain = self._normalize_domain(domain)
        self.path = path
        self.expires = expires
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        """Normalize domain by removing leading dot if present."""
        return domain.lstrip(".")

    @property
    def is_session_cookie(self) -> bool:
        """Return True if this is a session cookie (no expiry)."""
        return self.expires is None

    @property
    def is_persistent_cookie(self) -> bool:
        """Return True if this is a persistent cookie (has expiry)."""
        return self.expires is not None

    def is_expired(self) -> bool:
        """Check if cookie has expired based on current time."""
        if self.is_session_cookie:
            return False
        return time.time() > self.expires

    def time_until_expiry(self) -> Optional[int]:
        """Return seconds until cookie expires, or None if session cookie."""
        if self.is_session_cookie:
            return None
        remaining = self.expires - time.time()
        return max(0, int(remaining))

    def to_dict(self) -> Dict[str, Any]:
        """Convert cookie to dictionary for JSON serialization."""
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
        """Create a cookie from a dictionary."""
        return cls(
            name=data["name"],
            value=data["value"],
            domain=data["domain"],
            path=data.get("path", "/"),
            expires=data.get("expires"),
            secure=data.get("secure", False),
            http_only=data.get("httpOnly", False),
            same_site=data.get("sameSite", "Lax"),
        )

    def matches_domain(self, domain: str) -> bool:
        """Check if cookie applies to the given domain."""
        normalized = self._normalize_domain(domain)
        return normalized.endswith(self.domain) or normalized == self.domain

    def __repr__(self) -> str:
        """String representation for debugging."""
        expiry_info = (
            f"expires in {self.time_until_expiry()}s"
            if self.is_persistent_cookie
            else "session"
        )
        return f"Cookie({self.name}={self.value[:20]}..., {self.domain}, {expiry_info})"


class CookieJar:
    """
    Container for managing multiple cookies across different domains.

    Handles cookie storage, retrieval, filtering, and cleanup with
    support for both session and persistent cookies.
    """

    def __init__(self) -> None:
        """Initialize an empty cookie jar."""
        self.cookies: List[Cookie] = []

    def add(self, cookie: Cookie) -> None:
        """
        Add a cookie to the jar, replacing any existing cookie with same name/domain.

        Args:
            cookie: Cookie instance to add
        """
        # Remove any existing cookie with same name and domain
        self.cookies = [
            c for c in self.cookies
            if not (c.name == cookie.name and c.domain == cookie.domain)
        ]
        self.cookies.append(cookie)

    def get(self, name: str, domain: str) -> Optional[Cookie]:
        """
        Retrieve a specific cookie by name and domain.

        Args:
            name: Cookie name
            domain: Domain to search in

        Returns:
            Cookie if found and not expired, None otherwise
        """
        for cookie in self.cookies:
            if cookie.name == name and cookie.matches_domain(domain):
                if not cookie.is_expired():
                    return cookie
                else:
                    self.remove(name, domain)
                    return None
        return None

    def get_for_domain(self, domain: str, path: str = "/") -> List[Cookie]:
        """
        Get all valid cookies for a specific domain and path.

        Args:
            domain: Domain to retrieve cookies for
            path: Optional path filter (cookies with matching or parent paths)

        Returns:
            List of valid, non-expired cookies
        """
        valid_cookies = []

        for cookie in self.cookies:
            # Check if cookie is expired
            if cookie.is_expired():
                continue

            # Check domain match
            if not cookie.matches_domain(domain):
                continue

            # Check path match (cookie path must be prefix of request path)
            if not path.startswith(cookie.path):
                continue

            valid_cookies.append(cookie)

        return sorted(valid_cookies, key=lambda c: len(c.path), reverse=True)

    def remove(self, name: str, domain: str) -> bool:
        """
        Remove a cookie by name and domain.

        Args:
            name: Cookie name
            domain: Cookie domain

        Returns:
            True if cookie was removed, False if not found
        """
        original_length = len(self.cookies)
        self.cookies = [
            c for c in self.cookies
            if not (c.name == name and c.matches_domain(domain))
        ]
        return len(self.cookies) < original_length

    def clear(self) -> None:
        """Remove all cookies from the jar."""
        self.cookies.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired persistent cookies.

        Returns:
            Number of cookies removed
        """
        original_length = len(self.cookies)
        self.cookies = [c for c in self.cookies if not c.is_expired()]
        return original_length - len(self.cookies)

    def get_domains(self) -> List[str]:
        """Get list of unique domains in the jar."""
        return sorted(set(c.domain for c in self.cookies))

    def get_all(self) -> List[Cookie]:
        """Get all cookies in the jar (including expired)."""
        return self.cookies.copy()

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Convert jar to dictionary organized by domain.

        Returns:
            Dictionary mapping domain to list of cookies
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        for cookie in self.cookies:
            if cookie.domain not in result:
                result[cookie.domain] = []
            result[cookie.domain].append(cookie.to_dict())
        return result

    def from_dict(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Load cookies from dictionary format.

        Args:
            data: Dictionary mapping domain to list of cookie dicts
        """
        self.clear()
        for domain, cookies_list in data.items():
            for cookie_dict in cookies_list:
                cookie = Cookie.from_dict(cookie_dict)
                self.add(cookie)


class CookieManager:
    """
    Persistent cookie management system for nodriver browser instances.

    Manages saving/loading cookies from disk, validates expiry times,
    and integrates with nodriver browser automation.
    """

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize cookie manager with a storage path.

        Args:
            storage_path: Path to directory where cookies will be stored
        """
        self.storage_path = Path(storage_path)
        self.jar = CookieJar()
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_cookie_file(self, name: str) -> Path:
        """Get the file path for a named cookie file."""
        # Sanitize name to be filesystem-safe
        safe_name = "".join(c if c.isalnum() else "_" for c in name)
        return self.storage_path / f"{safe_name}_cookies.json"

    def save(self, name: str = "default") -> None:
        """
        Save cookies to JSON file.

        Args:
            name: Name for this cookie set (used in filename)
        """
        file_path = self._get_cookie_file(name)

        # Only save non-session cookies
        persistent_cookies = [c for c in self.jar.get_all() if c.is_persistent_cookie]
        persistent_jar = CookieJar()
        for cookie in persistent_cookies:
            persistent_jar.add(cookie)

        data = {
            "saved_at": datetime.now().isoformat(),
            "cookies": persistent_jar.to_dict(),
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, name: str = "default") -> bool:
        """
        Load cookies from JSON file.

        Args:
            name: Name for this cookie set (used in filename)

        Returns:
            True if file exists and was loaded, False otherwise
        """
        file_path = self._get_cookie_file(name)

        if not file_path.exists():
            return False

        with open(file_path, "r") as f:
            data = json.load(f)

        self.jar.from_dict(data.get("cookies", {}))
        return True

    def add_cookie(
        self,
        name: str,
        value: str,
        domain: str,
        path: str = "/",
        expires: Optional[int] = None,
        secure: bool = False,
        http_only: bool = False,
        same_site: str = "Lax",
    ) -> Cookie:
        """
        Add a cookie to the manager.

        Args:
            name: Cookie name
            value: Cookie value
            domain: Domain for cookie
            path: Path for cookie
            expires: Unix timestamp for expiration (None for session)
            secure: Secure flag
            http_only: HttpOnly flag
            same_site: SameSite attribute

        Returns:
            The created Cookie instance
        """
        cookie = Cookie(
            name=name,
            value=value,
            domain=domain,
            path=path,
            expires=expires,
            secure=secure,
            http_only=http_only,
            same_site=same_site,
        )
        self.jar.add(cookie)
        return cookie

    def get_cookie(self, name: str, domain: str) -> Optional[Cookie]:
        """
        Get a specific cookie.

        Args:
            name: Cookie name
            domain: Cookie domain

        Returns:
            Cookie if found and not expired, None otherwise
        """
        return self.jar.get(name, domain)

    def get_cookies_for_domain(self, domain: str) -> List[Cookie]:
        """
        Get all valid cookies for a domain.

        Args:
            domain: Domain to retrieve cookies for

        Returns:
            List of valid cookies
        """
        return self.jar.get_for_domain(domain)

    def delete_cookie(self, name: str, domain: str) -> bool:
        """
        Delete a specific cookie.

        Args:
            name: Cookie name
            domain: Cookie domain

        Returns:
            True if deleted, False if not found
        """
        return self.jar.remove(name, domain)

    def delete_domain_cookies(self, domain: str) -> int:
        """
        Delete all cookies for a domain.

        Args:
            domain: Domain to clear cookies for

        Returns:
            Number of cookies removed
        """
        original_count = len(self.jar.cookies)
        self.jar.cookies = [c for c in self.jar.cookies if not c.matches_domain(domain)]
        return original_count - len(self.jar.cookies)

    def clear_all(self) -> None:
        """Clear all cookies from memory."""
        self.jar.clear()

    def cleanup_expired(self) -> int:
        """
        Remove expired cookies.

        Returns:
            Number of cookies removed
        """
        return self.jar.cleanup_expired()

    def apply_to_browser(self, browser: Any, domain: str = "") -> None:
        """
        Apply cookies to a nodriver browser instance.

        Cookies are set via CDP protocol. Domain-specific cookies are
        filtered if a domain is provided.

        Args:
            browser: nodriver browser instance
            domain: Optional domain to filter cookies (empty = all)
        """
        if domain:
            cookies = self.get_cookies_for_domain(domain)
        else:
            cookies = [c for c in self.jar.get_all() if not c.is_expired()]

        for cookie in cookies:
            try:
                browser.cdp_client.execute(
                    "Network.setCookie",
                    {
                        "name": cookie.name,
                        "value": cookie.value,
                        "domain": cookie.domain,
                        "path": cookie.path,
                        "expires": cookie.expires,
                        "secure": cookie.secure,
                        "httpOnly": cookie.http_only,
                        "sameSite": cookie.same_site,
                    },
                )
            except Exception as e:
                print(f"Failed to set cookie {cookie.name}: {e}")

    def extract_from_browser(self, browser: Any) -> int:
        """
        Extract all cookies from a nodriver browser instance.

        Uses CDP protocol to retrieve cookies currently in the browser.

        Args:
            browser: nodriver browser instance

        Returns:
            Number of cookies extracted
        """
        try:
            result = browser.cdp_client.execute("Network.getAllCookies", {})
            cookies_data = result.get("cookies", [])

            initial_count = len(self.jar.cookies)

            for cookie_dict in cookies_data:
                cookie = Cookie.from_dict(cookie_dict)
                self.jar.add(cookie)

            return len(self.jar.cookies) - initial_count
        except Exception as e:
            print(f"Failed to extract cookies from browser: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored cookies.

        Returns:
            Dictionary with session/persistent count, expiry info, etc.
        """
        all_cookies = self.jar.get_all()

        session_cookies = [c for c in all_cookies if c.is_session_cookie]
        persistent_cookies = [c for c in all_cookies if c.is_persistent_cookie]
        expired_cookies = [c for c in persistent_cookies if c.is_expired()]

        domains = self.jar.get_domains()

        return {
            "total_cookies": len(all_cookies),
            "session_cookies": len(session_cookies),
            "persistent_cookies": len(persistent_cookies),
            "expired_cookies": len(expired_cookies),
            "valid_cookies": len(all_cookies) - len(expired_cookies),
            "unique_domains": len(domains),
            "domains": domains,
        }

    def export_json(self, file_path: Path) -> None:
        """
        Export all cookies to JSON file.

        Args:
            file_path: Path to export file
        """
        data = {
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "cookies": self.jar.to_dict(),
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_json(self, file_path: Path) -> bool:
        """
        Import cookies from JSON file.

        Args:
            file_path: Path to import file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            self.jar.from_dict(data.get("cookies", {}))
            return True
        except Exception as e:
            print(f"Failed to import cookies: {e}")
            return False


# Convenience function for quick usage
def create_manager(storage_dir: str = ".cookies") -> CookieManager:
    """
    Create a cookie manager with default settings.

    Args:
        storage_dir: Directory for storing cookies (default: .cookies)

    Returns:
        Initialized CookieManager instance

    Example:
        manager = create_manager()
        manager.add_cookie("sessionid", "abc123", "example.com")
        manager.save()
    """
    return CookieManager(Path(storage_dir))
