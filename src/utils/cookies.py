import json
import os
from typing import List, Dict, Any, Optional


def load_cookies(auth_file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load cookies from auth.json file.

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
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookie_data = f.read()
            cookies = json.loads(cookie_data)

        if not isinstance(cookies, list) or len(cookies) == 0:
            raise ValueError('Invalid cookie format: expected non-empty array')

        print(f"✓ Loaded {len(cookies)} cookies from {cookie_path}")
        return cookies

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Cookie file not found: {cookie_path}\n"
            "Please run the cookie extraction script first or check the file path."
        )


def validate_auth_cookies(cookies: List[Dict[str, Any]]) -> bool:
    """
    Validate that required Perplexity authentication cookies are present.

    Args:
        cookies: List of cookie dictionaries to validate

    Returns:
        True if essential authentication cookies are present, False otherwise
    """
    required_cookies = [
        'pplx.session-id',
        '__Secure-next-auth.session-token'
    ]

    cookie_names = [cookie.get('name') for cookie in cookies]
    has_required = all(name in cookie_names for name in required_cookies)

    if not has_required:
        print('⚠ Warning: Missing required authentication cookies')
        print('Required:', required_cookies)
        print('Found:', cookie_names)
        return False

    print('✓ All required authentication cookies present')
    return True
