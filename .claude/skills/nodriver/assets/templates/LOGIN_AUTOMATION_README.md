# Login Automation Template - Complete Documentation

Comprehensive login automation framework for nodriver browser automation with support for multiple authentication strategies.

## Overview

The login automation template provides production-ready code for handling authentication flows in web automation scripts. It's designed to be:

- **Flexible**: Supports form-based, OAuth, custom JavaScript, and API-based authentication
- **Robust**: Handles 2FA, session persistence, error recovery
- **Adaptable**: Works with different authentication systems through configuration
- **Maintainable**: Clean, well-documented code following Python best practices

## Key Features

### 1. Multiple Login Strategies

```python
LoginStrategy.FORM_BASED              # Traditional username/password
LoginStrategy.OAUTH_SIMULATION        # OAuth 2.0 flows
LoginStrategy.CUSTOM_JAVASCRIPT       # Custom authentication logic
LoginStrategy.API_BASED               # API endpoint-based login
```

### 2. Cookie-Based Session Persistence

Sessions are automatically saved to disk after successful login:

```python
manager = LoginManager(config, tab=tab)
await manager.login()  # Session saved to ~/.sessions/

# Next time, restore without logging in:
manager.try_restore_session("user@example.com")
```

### 3. Two-Factor Authentication

Wait for users to complete 2FA manually in the browser:

```python
config = LoginConfig(
    ...
    two_factor_config=TwoFactorConfig(
        enabled=True,
        method=TwoFactorMethod.SMS,
        timeout=120,  # Wait up to 2 minutes
    ),
)
await manager.login()  # Script pauses for user input
```

### 4. Remember Me Functionality

Auto-enable "Remember Me" for faster logins:

```python
config = LoginConfig(
    ...
    remember_me_config=RememberMeConfig(
        enabled=True,
        selector="input[name='remember_me']",
        duration_days=30,
    ),
)
```

### 5. Session Validation and Refresh

Check session validity and refresh when needed:

```python
if await manager.validate_and_refresh_session():
    print("Session is active")
else:
    print("Session expired or invalid")
```

### 6. Account Switching

Seamlessly switch between multiple accounts:

```python
await manager.switch_account("other@example.com", "password")
current_user = manager.get_session_info()['username']
```

### 7. Logout Handling

Properly logout and clear session:

```python
await manager.logout()
assert manager.current_session is None
```

### 8. Common Form Patterns

Pre-configured helpers for common authentication patterns:

```python
form_config = create_simple_form_config(
    username_selector="input[name='email']",
    password_selector="input[name='password']",
    submit_selector="button[type='submit']",
    success_indicator="div.dashboard",
)
```

## File Structure

```
login_automation.py
├── Enums
│   ├── LoginStrategy (FORM_BASED, OAUTH_SIMULATION, CUSTOM_JAVASCRIPT, API_BASED)
│   ├── TwoFactorMethod (SMS, EMAIL, AUTHENTICATOR, etc.)
│
├── Data Classes
│   ├── FormField
│   ├── LoginFormConfig
│   ├── OAuthConfig
│   ├── TwoFactorConfig
│   ├── SessionConfig
│   ├── RememberMeConfig
│   ├── LoginConfig
│   └── LoginSession
│
├── Core Classes
│   ├── SessionStorage (Persistent session management)
│   └── LoginManager (Main login orchestration)
│
└── Helper Functions
    ├── create_simple_form_config()
    └── create_oauth_config()
```

## Quick Start

### 1. Install Dependencies

```bash
pip install nodriver
```

### 2. Import Template

```python
from login_automation import (
    LoginManager,
    LoginConfig,
    create_simple_form_config,
)
```

### 3. Configure Login

```python
form_config = create_simple_form_config(
    username_selector="input[name='email']",
    password_selector="input[name='password']",
    submit_selector="button[type='submit']",
)

config = LoginConfig(
    username="user@example.com",
    password="secure_password",
    login_url="https://example.com/login",
    form_config=form_config,
)
```

### 4. Execute Login

```python
manager = LoginManager(config, tab=my_tab)
if await manager.login():
    print("Logged in successfully!")
    session_info = manager.get_session_info()
```

## Documentation Files

### `login_automation.py` (Main Template)
- Complete implementation
- Full API with docstrings
- Ready to use

**Size**: ~850 lines
**Key Classes**: LoginManager, LoginSession, SessionStorage
**Helper Functions**: create_simple_form_config(), create_oauth_config()

### `login_automation_examples.py` (10 Real-World Examples)
- Simple email/password login
- Advanced form login with 2FA
- Multi-step authentication
- OAuth 2.0 simulation
- API-based login
- Session restoration
- Account switching
- 2FA with timeout handling
- Callbacks and hooks
- Comprehensive login with all features

**Use This**: To see working examples for your use case

### `LOGIN_AUTOMATION_GUIDE.md` (Detailed Guide)
- Comprehensive explanations
- All login strategies with examples
- Session management details
- Callback usage
- Best practices and patterns
- Real-world examples (Gmail-like, LinkedIn-like, OAuth providers)
- Error handling and troubleshooting
- Security considerations
- Extension points

**Use This**: For in-depth learning and customization

### `LOGIN_AUTOMATION_QUICK_REF.md` (Quick Reference)
- One-page lookup guide
- Common patterns
- Common selectors
- Method signatures
- Error solutions
- Quick examples

**Use This**: As a reference while coding

### `LOGIN_AUTOMATION_README.md` (This File)
- Overview and summary
- Getting started
- Key features
- File descriptions

**Use This**: To understand the template

## Common Use Cases

### Use Case 1: Simple Login and Scrape

```python
async def login_and_scrape(url, username, password):
    form_config = create_simple_form_config(
        username_selector="input[name='email']",
        password_selector="input[name='password']",
        submit_selector="button[type='submit']",
    )

    config = LoginConfig(
        username=username,
        password=password,
        login_url=f"{url}/login",
        form_config=form_config,
    )

    manager = LoginManager(config, tab=my_tab)
    if not await manager.login():
        return None

    # Now logged in, scrape content
    await my_tab.navigate(f"{url}/dashboard")
    content = await my_tab.get_content()
    return content
```

### Use Case 2: Multi-Account Testing

```python
async def test_multiple_accounts():
    accounts = [
        ("user1@example.com", "pass1"),
        ("user2@example.com", "pass2"),
    ]

    results = {}

    for username, password in accounts:
        config = LoginConfig(username=username, password=password, ...)
        manager = LoginManager(config, tab=tab)

        if manager.try_restore_session(username) or await manager.login():
            results[username] = "success"
        else:
            results[username] = "failed"

        await manager.logout()

    return results
```

### Use Case 3: Long-Running Session with Refresh

```python
async def maintain_session(duration_hours):
    config = LoginConfig(...)
    manager = LoginManager(config, tab=tab)

    # Login
    await manager.login()

    # Keep session alive
    end_time = time.time() + (duration_hours * 3600)
    while time.time() < end_time:
        # Refresh every hour
        await manager.validate_and_refresh_session()

        # Do work
        await perform_action()

        await asyncio.sleep(3600)  # Check every hour
```

### Use Case 4: OAuth Integration Testing

```python
async def test_oauth_flow():
    oauth_config = OAuthConfig(
        auth_endpoint="https://oauth.provider.com/authorize",
        client_id="test_client_id",
        redirect_uri="http://localhost:3000/callback",
    )

    config = LoginConfig(
        username="test@example.com",
        password="test_token",
        login_url="https://app.example.com/login/oauth",
        strategy=LoginStrategy.OAUTH_SIMULATION,
        oauth_config=oauth_config,
    )

    manager = LoginManager(config, tab=tab)
    if await manager.login():
        print("OAuth flow successful")
```

## Architecture

### Component Diagram

```
LoginManager
├── config: LoginConfig
│   ├── form_config: LoginFormConfig
│   ├── oauth_config: OAuthConfig
│   ├── two_factor_config: TwoFactorConfig
│   ├── session_config: SessionConfig
│   └── remember_me_config: RememberMeConfig
├── tab: Browser Tab (nodriver)
├── current_session: LoginSession
└── session_storage: SessionStorage
    └── sessions/{username}_session.json
```

### Login Flow

```
start
  ↓
navigate to login URL
  ↓
select strategy (form/oauth/custom/api)
  ↓
execute strategy-specific login
  ↓
handle 2FA if enabled
  ↓
handle remember me if enabled
  ↓
validate session
  ↓
create & save session
  ↓
success
```

### Session Flow

```
save (after login)
  ↓
session_storage.save_session()
  ↓
~/.sessions/{username}_session.json
  ↓
restore (next time)
  ↓
try_restore_session()
  ↓
session valid?
  ├─ yes → use restored session
  └─ no → perform fresh login
```

## API Highlights

### LoginManager

```python
# Core methods
await manager.login() -> bool
await manager.logout() -> bool
await manager.switch_account(username: str, password: str) -> bool

# Session operations
manager.try_restore_session(username: str) -> bool
await manager.validate_and_refresh_session() -> bool
manager.get_session_info() -> Dict
manager.list_available_accounts() -> List[str]
```

### LoginConfig

```python
LoginConfig(
    username: str,
    password: str,
    login_url: str,
    strategy: LoginStrategy = FORM_BASED,
    form_config: Optional[LoginFormConfig] = None,
    oauth_config: Optional[OAuthConfig] = None,
    custom_javascript: Optional[str] = None,
    session_config: SessionConfig = SessionConfig(),
    two_factor_config: TwoFactorConfig = TwoFactorConfig(),
    remember_me_config: RememberMeConfig = RememberMeConfig(),
    timeout: int = 30,
)
```

## Best Practices

### 1. Always Verify Selectors First

```python
# In browser DevTools console:
document.querySelector("input[name='email']")  // Should not be null
document.querySelector("input[name='password']")
document.querySelector("button[type='submit']")
```

### 2. Use Environment Variables for Credentials

```python
import os
username = os.getenv("LOGIN_USERNAME")
password = os.getenv("LOGIN_PASSWORD")
```

### 3. Specify Success Indicators

```python
form_config = LoginFormConfig(
    ...
    success_indicator="div.dashboard",  # Clear success marker
)
```

### 4. Handle Timeouts Gracefully

```python
try:
    if await manager.login():
        # Success
    else:
        # Login returned False
except asyncio.TimeoutError:
    # Timeout occurred
```

### 5. Restore Sessions When Possible

```python
if not manager.try_restore_session(username):
    await manager.login()  # Only login if session unavailable
```

### 6. Protect Session Files

```bash
chmod 600 ~/.sessions/*_session.json  # Owner read/write only
```

## Common Patterns

### Pattern 1: Try Restore, Then Login

```python
manager = LoginManager(config, tab=tab)
if not manager.try_restore_session(config.username):
    await manager.login()
```

### Pattern 2: With Error Handling

```python
try:
    manager = LoginManager(config, tab=tab)
    if await manager.login():
        return manager
except asyncio.TimeoutError:
    print("Login timed out")
except Exception as e:
    print(f"Login error: {e}")
return None
```

### Pattern 3: Account Iteration

```python
for username, password in accounts:
    config = LoginConfig(username=username, password=password, ...)
    manager = LoginManager(config, tab=tab)

    if manager.try_restore_session(username):
        # Use cached session
    else:
        # Fresh login
        if not await manager.login():
            continue

    # Do work as this user
    await do_something()

    # Switch to next account
    await manager.logout()
```

## Troubleshooting Guide

| Problem | Solution |
|---------|----------|
| **Login never completes** | Check success_indicator, verify selectors, increase timeout |
| **Selector not found** | Use DevTools inspector, test selector in console |
| **Session not saving** | Check file permissions, verify storage path exists |
| **2FA timeout** | Increase timeout value, verify input_selector |
| **OAuth redirect fails** | Check redirect_uri matches exactly, verify OAuth config |
| **Custom JS fails** | Test JavaScript code separately, verify syntax |
| **Session expired error** | Sessions expire by default after 24h, perform fresh login |

## Performance Metrics

- **Simple login**: ~3-5 seconds
- **Login + 2FA**: ~10-30 seconds (depends on user)
- **Session restore**: <1 second
- **Session validation**: ~1-2 seconds

## Security Notes

- Credentials are NEVER stored in session files
- Only session tokens/cookies are persisted
- Session files default to current user only (0600 permissions)
- SSL/HTTPS verification enabled by default
- 2FA provides additional security when enabled
- Session timeouts prevent hijacking

## Extending the Template

To add support for a new authentication system:

1. **Create new LoginStrategy enum value**
2. **Create configuration dataclass** (if needed)
3. **Implement `_login_*` method** in LoginManager
4. **Test with target service**
5. **Document in guide**

Example:

```python
class LoginStrategy(Enum):
    SAML = "saml"

class SamlConfig:
    idp_endpoint: str
    # ... fields ...

async def _login_saml(self) -> bool:
    # Implementation
    pass
```

## Related Resources

- `cookie_manager.py` - Cookie persistence and management
- `smart_click.py` - Reliable element clicking
- `element_waiter.py` - Wait for elements to appear
- `human_behavior.py` - Human-like interactions
- `network_monitor.py` - Network request interception

## Getting Help

### Selector Problems?
1. Open DevTools (F12)
2. Right-click element → Inspect
3. Copy selector from DevTools
4. Test in console: `document.querySelector(...)`

### Still Not Working?
1. Check login_automation_examples.py for similar pattern
2. Review LOGIN_AUTOMATION_GUIDE.md detailed section
3. Print debug info from callbacks
4. Verify credentials are correct

### Need to Customize?
See "Extending the Template" section above.

## Version Info

- **Template Version**: 1.0
- **Python**: 3.8+
- **Dependencies**: nodriver (async browser automation)
- **Status**: Production-ready

## License and Usage

This template is provided as-is for use in your automation scripts. Modify and extend as needed for your specific use cases.

### Important Notes

- Test thoroughly before production use
- Comply with website terms of service
- Respect rate limiting and robots.txt
- Use responsibly and ethically
- Protect user credentials and session data

## Quick Links

| Resource | Purpose |
|----------|---------|
| `login_automation.py` | Main implementation |
| `login_automation_examples.py` | Working examples |
| `LOGIN_AUTOMATION_GUIDE.md` | Detailed guide |
| `LOGIN_AUTOMATION_QUICK_REF.md` | Quick reference |

## Next Steps

1. **Read**: START with `LOGIN_AUTOMATION_QUICK_REF.md` for overview
2. **Learn**: Review `LOGIN_AUTOMATION_GUIDE.md` for your use case
3. **Code**: Copy example from `login_automation_examples.py`
4. **Customize**: Adjust selectors and configuration
5. **Test**: Verify with target website
6. **Deploy**: Use in your automation script

---

**Happy Automating!**

For detailed information about any component, see the corresponding documentation file or the docstrings in `login_automation.py`.
