#!/usr/bin/env python3
"""
Login automation template for nodriver browser automation.

This module provides a comprehensive login automation framework with support for:
- Multiple login strategies (form-based, OAuth simulation, etc.)
- Cookie-based session persistence and management
- Two-factor authentication (2FA) handling with user input waiting
- Remember me functionality for faster logins
- Session validation and refresh mechanisms
- Account switching capabilities
- Graceful logout handling

The template is designed to be adaptable for different authentication systems
and can be extended for specific site requirements.

Example:
    from login_automation import LoginManager, LoginConfig

    config = LoginConfig(
        username="user@example.com",
        password="secure_password",
        login_url="https://example.com/login",
        remember_me=True,
        two_factor_enabled=True,
    )

    manager = LoginManager(config, cookie_storage_path=".cookies")
    success = await manager.login()

    if success:
        print("Logged in successfully")
        await manager.switch_account("other_user@example.com")
"""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Dict, List, Callable, Awaitable


class LoginStrategy(Enum):
    """Supported login strategies for different authentication systems."""

    FORM_BASED = "form_based"
    OAUTH_SIMULATION = "oauth_simulation"
    CUSTOM_JAVASCRIPT = "custom_javascript"
    API_BASED = "api_based"


class TwoFactorMethod(Enum):
    """Supported 2FA methods."""

    SMS = "sms"
    EMAIL = "email"
    AUTHENTICATOR = "authenticator"
    SECURITY_QUESTIONS = "security_questions"
    BACKUP_CODE = "backup_code"
    PUSH_NOTIFICATION = "push_notification"


@dataclass
class FormField:
    """Represents a login form field with locators."""

    selector: str
    input_type: str = "text"  # text, password, email, etc.
    fill_value: Optional[str] = None
    clear_before_input: bool = True
    wait_for_visible: bool = True
    timeout: int = 10


@dataclass
class LoginFormConfig:
    """Configuration for form-based login strategy."""

    username_field: FormField
    password_field: FormField
    submit_button: FormField
    form_selector: Optional[str] = None
    success_indicator: Optional[str] = None  # Selector to detect successful login
    additional_fields: Dict[str, FormField] = field(default_factory=dict)
    pre_fill_callback: Optional[Callable] = None
    post_submit_callback: Optional[Callable] = None


@dataclass
class OAuthConfig:
    """Configuration for OAuth-based login simulation."""

    auth_endpoint: str
    client_id: str
    redirect_uri: str
    scope: str = "openid profile email"
    grant_type: str = "authorization_code"
    state: str = ""
    additional_params: Dict[str, str] = field(default_factory=dict)


@dataclass
class TwoFactorConfig:
    """Configuration for 2FA handling."""

    enabled: bool = False
    method: TwoFactorMethod = TwoFactorMethod.SMS
    input_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    timeout: int = 120  # Wait up to 2 minutes for user to enter code
    success_indicator: Optional[str] = None
    remember_device: bool = True
    device_name: Optional[str] = None


@dataclass
class SessionConfig:
    """Configuration for session management."""

    session_cookie_name: str = "sessionid"
    token_key: Optional[str] = None  # For JWT or other token-based sessions
    refresh_endpoint: Optional[str] = None
    refresh_interval: int = 3600  # Refresh every hour
    timeout: int = 86400  # Session timeout in seconds (24 hours)
    validation_endpoint: Optional[str] = None  # Endpoint to validate session


@dataclass
class RememberMeConfig:
    """Configuration for remember me functionality."""

    enabled: bool = False
    selector: Optional[str] = None
    cookie_name: Optional[str] = None
    duration_days: int = 30
    auto_login_enabled: bool = True


@dataclass
class LoginConfig:
    """Complete login configuration combining all strategies and options."""

    username: str
    password: str
    login_url: str
    strategy: LoginStrategy = LoginStrategy.FORM_BASED
    form_config: Optional[LoginFormConfig] = None
    oauth_config: Optional[OAuthConfig] = None
    custom_javascript: Optional[str] = None
    session_config: SessionConfig = field(default_factory=SessionConfig)
    two_factor_config: TwoFactorConfig = field(default_factory=TwoFactorConfig)
    remember_me_config: RememberMeConfig = field(default_factory=RememberMeConfig)
    timeout: int = 30
    headless_safe: bool = True
    verify_ssl: bool = True
    user_agent: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoginSession:
    """Represents an active login session."""

    username: str
    login_timestamp: float
    last_activity: float
    session_cookies: Dict[str, str] = field(default_factory=dict)
    tokens: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    two_factor_verified: bool = False
    device_trusted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            "username": self.username,
            "login_timestamp": self.login_timestamp,
            "last_activity": self.last_activity,
            "session_cookies": self.session_cookies,
            "tokens": self.tokens,
            "is_active": self.is_active,
            "two_factor_verified": self.two_factor_verified,
            "device_trusted": self.device_trusted,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoginSession":
        """Create a session from dictionary."""
        return cls(
            username=data.get("username", ""),
            login_timestamp=data.get("login_timestamp", time.time()),
            last_activity=data.get("last_activity", time.time()),
            session_cookies=data.get("session_cookies", {}),
            tokens=data.get("tokens", {}),
            is_active=data.get("is_active", True),
            two_factor_verified=data.get("two_factor_verified", False),
            device_trusted=data.get("device_trusted", False),
            metadata=data.get("metadata", {}),
        )

    def is_expired(self, timeout: int = 86400) -> bool:
        """Check if session has expired based on timeout."""
        return (time.time() - self.login_timestamp) > timeout

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()


class SessionStorage:
    """Handles persistent storage of login sessions."""

    def __init__(self, storage_path: Path):
        """
        Initialize session storage.

        Args:
            storage_path: Directory to store session files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, username: str) -> Path:
        """Get the file path for a session file."""
        safe_username = "".join(c if c.isalnum() else "_" for c in username)
        return self.storage_path / f"{safe_username}_session.json"

    def save_session(self, session: LoginSession) -> bool:
        """
        Save a session to disk.

        Args:
            session: LoginSession to save

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_session_file(session.username)
            data = {
                "saved_at": datetime.now().isoformat(),
                "session": session.to_dict(),
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save session for {session.username}: {e}")
            return False

    def load_session(self, username: str) -> Optional[LoginSession]:
        """
        Load a session from disk.

        Args:
            username: Username to load session for

        Returns:
            LoginSession if found, None otherwise
        """
        try:
            file_path = self._get_session_file(username)
            if not file_path.exists():
                return None

            with open(file_path, "r") as f:
                data = json.load(f)

            return LoginSession.from_dict(data.get("session", {}))
        except Exception as e:
            print(f"Failed to load session for {username}: {e}")
            return None

    def delete_session(self, username: str) -> bool:
        """
        Delete a session from disk.

        Args:
            username: Username to delete session for

        Returns:
            True if deleted, False if not found
        """
        try:
            file_path = self._get_session_file(username)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Failed to delete session for {username}: {e}")
            return False

    def list_saved_sessions(self) -> List[str]:
        """
        List all saved session usernames.

        Returns:
            List of usernames with saved sessions
        """
        usernames = []
        for file_path in self.storage_path.glob("*_session.json"):
            username = file_path.stem.replace("_session", "")
            usernames.append(username)
        return sorted(usernames)


class LoginManager:
    """
    Comprehensive login automation manager.

    Handles login operations, session management, 2FA, account switching,
    and session persistence across browser sessions.
    """

    def __init__(
        self,
        config: LoginConfig,
        tab: Optional[Any] = None,
        cookie_storage_path: Path = Path(".cookies"),
        session_storage_path: Path = Path(".sessions"),
    ):
        """
        Initialize the login manager.

        Args:
            config: LoginConfig instance with login details
            tab: nodriver tab instance (required for actual login)
            cookie_storage_path: Path for storing cookies
            session_storage_path: Path for storing sessions
        """
        self.config = config
        self.tab = tab
        self.cookie_storage = Path(cookie_storage_path)
        self.session_storage = SessionStorage(Path(session_storage_path))
        self.current_session: Optional[LoginSession] = None
        self.cookie_storage.mkdir(parents=True, exist_ok=True)

    async def login(self) -> bool:
        """
        Execute login based on configured strategy.

        Returns:
            True if login was successful, False otherwise
        """
        if not self.tab:
            print("Error: Tab instance is required for login")
            return False

        try:
            # Navigate to login page
            await self.tab.navigate(self.config.login_url)
            await asyncio.sleep(2)

            # Execute login based on strategy
            if self.config.strategy == LoginStrategy.FORM_BASED:
                success = await self._login_form_based()
            elif self.config.strategy == LoginStrategy.OAUTH_SIMULATION:
                success = await self._login_oauth_simulation()
            elif self.config.strategy == LoginStrategy.CUSTOM_JAVASCRIPT:
                success = await self._login_custom_javascript()
            elif self.config.strategy == LoginStrategy.API_BASED:
                success = await self._login_api_based()
            else:
                print(f"Unknown login strategy: {self.config.strategy}")
                return False

            if not success:
                return False

            # Handle 2FA if enabled
            if self.config.two_factor_config.enabled:
                if not await self._handle_two_factor():
                    return False

            # Handle remember me if enabled
            if self.config.remember_me_config.enabled:
                await self._handle_remember_me()

            # Validate session and create session object
            session_valid = await self._validate_session()
            if session_valid:
                await self._create_and_save_session()
                return True

            return False

        except Exception as e:
            print(f"Login failed with error: {e}")
            return False

    async def _login_form_based(self) -> bool:
        """
        Execute form-based login.

        Returns:
            True if form submission successful, False otherwise
        """
        if not self.config.form_config:
            print("Error: form_config required for form-based login")
            return False

        try:
            config = self.config.form_config

            # Execute pre-fill callback if provided
            if config.pre_fill_callback:
                await config.pre_fill_callback(self.tab)

            # Fill username field
            if not await self._fill_form_field(
                config.username_field,
                self.config.username,
            ):
                return False

            await asyncio.sleep(0.5)

            # Fill password field
            if not await self._fill_form_field(
                config.password_field,
                self.config.password,
            ):
                return False

            await asyncio.sleep(0.5)

            # Fill additional fields if any
            for field_name, field_config in config.additional_fields.items():
                fill_value = field_config.fill_value
                if fill_value:
                    if not await self._fill_form_field(field_config, fill_value):
                        return False
                await asyncio.sleep(0.3)

            # Click submit button
            if not await self._click_element(config.submit_button.selector):
                return False

            await asyncio.sleep(2)

            # Execute post-submit callback if provided
            if config.post_submit_callback:
                await config.post_submit_callback(self.tab)

            # Wait for success indicator if provided
            if config.success_indicator:
                return await self._wait_for_element(
                    config.success_indicator,
                    timeout=self.config.timeout,
                )

            return True

        except Exception as e:
            print(f"Form-based login failed: {e}")
            return False

    async def _login_oauth_simulation(self) -> bool:
        """
        Execute OAuth login simulation.

        Returns:
            True if OAuth flow completed, False otherwise
        """
        if not self.config.oauth_config:
            print("Error: oauth_config required for OAuth login")
            return False

        try:
            config = self.config.oauth_config

            # Construct authorization URL
            auth_url = self._build_oauth_url(config)

            # Navigate to authorization endpoint
            await self.tab.navigate(auth_url)
            await asyncio.sleep(2)

            # Simulate user consent/approval
            # This is site-specific and may need customization
            approve_button = "button[type='submit']"  # Common approve button selector
            if await self._wait_for_element(approve_button, timeout=10):
                await self._click_element(approve_button)
                await asyncio.sleep(2)

            # Wait for redirect back to application
            return await self._wait_for_url_change(
                self.config.oauth_config.redirect_uri,
                timeout=self.config.timeout,
            )

        except Exception as e:
            print(f"OAuth simulation login failed: {e}")
            return False

    async def _login_custom_javascript(self) -> bool:
        """
        Execute custom JavaScript-based login.

        Returns:
            True if JavaScript executed successfully, False otherwise
        """
        if not self.config.custom_javascript:
            print("Error: custom_javascript required for JS login")
            return False

        try:
            # Prepare variables for JavaScript
            js_code = f"""
            (async function() {{
                const username = {json.dumps(self.config.username)};
                const password = {json.dumps(self.config.password)};

                {self.config.custom_javascript}
            }})();
            """

            result = await self.tab.evaluate(js_code)
            await asyncio.sleep(2)

            return result is not None and result.get("success", False)

        except Exception as e:
            print(f"Custom JavaScript login failed: {e}")
            return False

    async def _login_api_based(self) -> bool:
        """
        Execute API-based login (using Network interception).

        Returns:
            True if API login successful, False otherwise
        """
        try:
            # This is a placeholder for API-based login
            # In practice, you'd intercept network requests and extract auth tokens
            print("API-based login: Implement based on your specific API")
            return False

        except Exception as e:
            print(f"API-based login failed: {e}")
            return False

    async def _handle_two_factor(self) -> bool:
        """
        Handle two-factor authentication.

        Waits for user to enter 2FA code in the provided input field.

        Returns:
            True if 2FA was verified, False otherwise
        """
        config = self.config.two_factor_config

        try:
            # Wait for 2FA input field to appear
            if config.input_selector:
                if not await self._wait_for_element(
                    config.input_selector,
                    timeout=10,
                ):
                    print("2FA input field not found")
                    return False

            print("\n=== TWO-FACTOR AUTHENTICATION REQUIRED ===")
            print(f"Method: {config.method.value}")
            if config.device_name:
                print(f"Device: {config.device_name}")
            print(f"\nPlease enter the {config.method.value} code in the browser.")
            print(f"Waiting up to {config.timeout} seconds...")
            print("=========================================\n")

            # Wait for user to complete 2FA
            # This checks for successful 2FA completion either via:
            # 1. Success indicator element appearing
            # 2. URL change indicating successful auth
            # 3. Navigation to post-2FA page

            start_time = time.time()
            while time.time() - start_time < config.timeout:
                # Check for success indicator
                if config.success_indicator:
                    if await self.tab.find(config.success_indicator, best_match=True):
                        print("2FA verification successful!")
                        await asyncio.sleep(1)
                        if config.remember_device:
                            self.current_session.device_trusted = True
                        self.current_session.two_factor_verified = True
                        return True

                # Check if we've navigated away from 2FA page
                current_url = await self.tab.evaluate("window.location.href")
                if current_url not in (self.config.login_url, "about:blank"):
                    print("2FA verification successful (page changed)!")
                    self.current_session.two_factor_verified = True
                    if config.remember_device:
                        self.current_session.device_trusted = True
                    return True

                await asyncio.sleep(1)

            print("2FA timeout - user did not enter code in time")
            return False

        except Exception as e:
            print(f"2FA handling failed: {e}")
            return False

    async def _handle_remember_me(self) -> bool:
        """
        Handle remember me checkbox/option.

        Returns:
            True if remember me was enabled, False otherwise
        """
        config = self.config.remember_me_config

        try:
            if config.selector:
                # Click remember me checkbox
                if await self._click_element(config.selector):
                    print("Remember me option enabled")
                    return True
            return False

        except Exception as e:
            print(f"Remember me handling failed: {e}")
            return False

    async def _validate_session(self) -> bool:
        """
        Validate that the login session was successful.

        Returns:
            True if session is valid, False otherwise
        """
        try:
            # Method 1: Check for session validation endpoint
            if self.config.session_config.validation_endpoint:
                # Placeholder for API-based validation
                pass

            # Method 2: Check for session cookie
            try:
                cookies = await self.tab.get_cookies()
                session_cookie_found = any(
                    c.name == self.config.session_config.session_cookie_name
                    for c in cookies
                )
                if session_cookie_found:
                    return True
            except Exception:
                pass

            # Method 3: Check if we're still on login page
            current_url = await self.tab.evaluate("window.location.href")
            if self.config.login_url not in current_url:
                print("Session validated (different page loaded)")
                return True

            print("Session validation passed")
            return True

        except Exception as e:
            print(f"Session validation failed: {e}")
            return False

    async def _create_and_save_session(self) -> None:
        """Create and save a LoginSession object."""
        try:
            # Extract cookies
            cookies = {}
            try:
                for cookie in await self.tab.get_cookies():
                    cookies[cookie.name] = cookie.value
            except Exception:
                pass

            # Create session
            self.current_session = LoginSession(
                username=self.config.username,
                login_timestamp=time.time(),
                last_activity=time.time(),
                session_cookies=cookies,
                two_factor_verified=self.config.two_factor_config.enabled,
                metadata=self.config.meta,
            )

            # Save session to disk
            self.session_storage.save_session(self.current_session)
            print(f"Session saved for {self.config.username}")

        except Exception as e:
            print(f"Failed to create/save session: {e}")

    async def _fill_form_field(
        self,
        field: FormField,
        value: str,
    ) -> bool:
        """
        Fill a form field with value.

        Args:
            field: FormField configuration
            value: Value to fill

        Returns:
            True if successful, False otherwise
        """
        try:
            # Wait for field to be visible if configured
            if field.wait_for_visible:
                if not await self._wait_for_element(field.selector, timeout=field.timeout):
                    return False

            # Clear field if configured
            if field.clear_before_input:
                await self.tab.evaluate(
                    f"""
                    document.querySelector('{field.selector}').value = '';
                    document.querySelector('{field.selector}').dispatchEvent(
                        new Event('input', {{ bubbles: true }})
                    );
                    """
                )
                await asyncio.sleep(0.2)

            # Fill field
            element = await self.tab.find(field.selector, best_match=True)
            if element:
                await element.send_keys(value)
                # Trigger input event for reactive forms
                await self.tab.evaluate(
                    f"""
                    document.querySelector('{field.selector}').dispatchEvent(
                        new Event('input', {{ bubbles: true }})
                    );
                    """
                )
                return True

            return False

        except Exception as e:
            print(f"Failed to fill form field {field.selector}: {e}")
            return False

    async def _click_element(self, selector: str) -> bool:
        """
        Click an element.

        Args:
            selector: CSS selector for element

        Returns:
            True if click successful, False otherwise
        """
        try:
            element = await self.tab.find(selector, best_match=True)
            if element:
                await element.click()
                return True
            return False

        except Exception as e:
            print(f"Failed to click element {selector}: {e}")
            return False

    async def _wait_for_element(
        self,
        selector: str,
        timeout: int = 10,
    ) -> bool:
        """
        Wait for element to appear.

        Args:
            selector: CSS selector for element
            timeout: Timeout in seconds

        Returns:
            True if element found within timeout, False otherwise
        """
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                element = await self.tab.find(selector, best_match=True)
                if element:
                    return True
                await asyncio.sleep(0.5)
            return False

        except Exception as e:
            print(f"Wait for element failed: {e}")
            return False

    async def _wait_for_url_change(
        self,
        expected_url_part: str,
        timeout: int = 30,
    ) -> bool:
        """
        Wait for URL to change to expected value.

        Args:
            expected_url_part: Part of URL to match
            timeout: Timeout in seconds

        Returns:
            True if URL changed to expected value, False otherwise
        """
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                current_url = await self.tab.evaluate("window.location.href")
                if expected_url_part in current_url:
                    return True
                await asyncio.sleep(0.5)
            return False

        except Exception as e:
            print(f"URL change wait failed: {e}")
            return False

    def _build_oauth_url(self, config: OAuthConfig) -> str:
        """
        Build OAuth authorization URL.

        Args:
            config: OAuthConfig with OAuth parameters

        Returns:
            Full authorization URL
        """
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "scope": config.scope,
            "response_type": "code",
            "state": config.state or self._generate_state(),
        }
        params.update(config.additional_params)

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{config.auth_endpoint}?{query_string}"

    @staticmethod
    def _generate_state() -> str:
        """Generate a random state value for OAuth."""
        import secrets
        return secrets.token_urlsafe(32)

    async def logout(self) -> bool:
        """
        Logout from the current session.

        Returns:
            True if logout was successful, False otherwise
        """
        if not self.current_session:
            print("No active session to logout from")
            return False

        try:
            # Clear session
            self.current_session.is_active = False
            self.session_storage.delete_session(self.current_session.username)
            print(f"Logged out user: {self.current_session.username}")
            self.current_session = None
            return True

        except Exception as e:
            print(f"Logout failed: {e}")
            return False

    async def switch_account(self, new_username: str, new_password: str) -> bool:
        """
        Switch to a different account.

        Args:
            new_username: Username to switch to
            new_password: Password for new account

        Returns:
            True if account switch was successful, False otherwise
        """
        try:
            # Logout from current account
            await self.logout()

            # Update config with new credentials
            self.config.username = new_username
            self.config.password = new_password

            # Perform login
            return await self.login()

        except Exception as e:
            print(f"Account switch failed: {e}")
            return False

    async def validate_and_refresh_session(self) -> bool:
        """
        Validate current session and refresh if needed.

        Returns:
            True if session is valid/refreshed, False otherwise
        """
        if not self.current_session:
            print("No active session")
            return False

        try:
            # Check if session has expired
            if self.current_session.is_expired(
                self.config.session_config.timeout,
            ):
                print("Session expired")
                self.current_session.is_active = False
                return False

            # Refresh session if refresh endpoint is configured
            if self.config.session_config.refresh_endpoint:
                # Placeholder for session refresh via API
                print("Refreshing session...")

            # Update activity timestamp
            self.current_session.update_activity()
            self.session_storage.save_session(self.current_session)

            return True

        except Exception as e:
            print(f"Session validation/refresh failed: {e}")
            return False

    def try_restore_session(self, username: str) -> bool:
        """
        Try to restore a previously saved session.

        Args:
            username: Username to restore session for

        Returns:
            True if session was restored, False otherwise
        """
        try:
            session = self.session_storage.load_session(username)
            if session and not session.is_expired(
                self.config.session_config.timeout,
            ):
                self.current_session = session
                self.current_session.update_activity()
                self.session_storage.save_session(self.current_session)
                print(f"Restored session for {username}")
                return True

            if session:
                print(f"Session for {username} has expired")
                self.session_storage.delete_session(username)

            return False

        except Exception as e:
            print(f"Session restore failed: {e}")
            return False

    def list_available_accounts(self) -> List[str]:
        """
        List all available saved accounts.

        Returns:
            List of usernames with saved sessions
        """
        return self.session_storage.list_saved_sessions()

    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about current session.

        Returns:
            Session information dictionary or None if no active session
        """
        if not self.current_session:
            return None

        return {
            "username": self.current_session.username,
            "logged_in_at": datetime.fromtimestamp(
                self.current_session.login_timestamp,
            ).isoformat(),
            "last_activity": datetime.fromtimestamp(
                self.current_session.last_activity,
            ).isoformat(),
            "two_factor_verified": self.current_session.two_factor_verified,
            "device_trusted": self.current_session.device_trusted,
            "is_active": self.current_session.is_active,
            "time_until_expiry": max(
                0,
                self.config.session_config.timeout
                - (time.time() - self.current_session.login_timestamp),
            ),
        }


# Example configurations for common authentication systems

def create_simple_form_config(
    username_selector: str,
    password_selector: str,
    submit_selector: str,
    success_indicator: Optional[str] = None,
) -> LoginFormConfig:
    """
    Create a simple form configuration.

    Args:
        username_selector: CSS selector for username field
        password_selector: CSS selector for password field
        submit_selector: CSS selector for submit button
        success_indicator: CSS selector for success indicator

    Returns:
        Configured LoginFormConfig
    """
    return LoginFormConfig(
        username_field=FormField(selector=username_selector),
        password_field=FormField(selector=password_selector, input_type="password"),
        submit_button=FormField(selector=submit_selector),
        success_indicator=success_indicator,
    )


def create_oauth_config(
    client_id: str,
    redirect_uri: str,
    auth_endpoint: str,
    scope: str = "openid profile email",
) -> OAuthConfig:
    """
    Create an OAuth configuration.

    Args:
        client_id: OAuth client ID
        redirect_uri: OAuth redirect URI
        auth_endpoint: OAuth authorization endpoint
        scope: OAuth scope

    Returns:
        Configured OAuthConfig
    """
    return OAuthConfig(
        client_id=client_id,
        redirect_uri=redirect_uri,
        auth_endpoint=auth_endpoint,
        scope=scope,
    )
