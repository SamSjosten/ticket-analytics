"""
Auth0 authentication configuration.
"""
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
# Try to find .env automatically first, then fall back to explicit path
dotenv_path = find_dotenv()
if not dotenv_path:
    dotenv_path = Path(__file__).parent.parent / '.env'

load_dotenv(dotenv_path=dotenv_path, override=True)


class Auth0Config:
    """Auth0 authentication configuration."""

    # Auth0 connection settings
    DOMAIN = os.getenv('AUTH0_DOMAIN', '')
    CLIENT_ID = os.getenv('AUTH0_CLIENT_ID', '')
    CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET', '')
    CALLBACK_URL = os.getenv('AUTH0_CALLBACK_URL', 'http://localhost:8501')

    # Auth0 URLs (constructed from domain)
    @classmethod
    def get_authorize_url(cls) -> str:
        """Get Auth0 authorization endpoint."""
        return f"https://{cls.DOMAIN}/authorize"

    @classmethod
    def get_token_url(cls) -> str:
        """Get Auth0 token endpoint."""
        return f"https://{cls.DOMAIN}/oauth/token"

    @classmethod
    def get_userinfo_url(cls) -> str:
        """Get Auth0 userinfo endpoint."""
        return f"https://{cls.DOMAIN}/userinfo"

    @classmethod
    def get_logout_url(cls) -> str:
        """Get Auth0 logout endpoint."""
        return f"https://{cls.DOMAIN}/v2/logout"

    # OAuth settings
    SCOPE = os.getenv('AUTH0_SCOPE', 'openid profile email')
    AUDIENCE = os.getenv('AUTH0_AUDIENCE', '')  # Optional API identifier

    # Session settings
    SESSION_LIFETIME = int(os.getenv('AUTH0_SESSION_LIFETIME', '3600'))  # 1 hour default

    # Users table configuration
    USERS_TABLE = os.getenv('AUTH0_USERS_TABLE', 'users')

    @classmethod
    def validate_config(cls) -> tuple[bool, str]:
        """
        Validate Auth0 configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cls.DOMAIN:
            return False, "AUTH0_DOMAIN is not configured"

        if not cls.CLIENT_ID:
            return False, "AUTH0_CLIENT_ID is not configured"

        if not cls.CLIENT_SECRET:
            return False, "AUTH0_CLIENT_SECRET is not configured"

        if not cls.CALLBACK_URL:
            return False, "AUTH0_CALLBACK_URL is not configured"

        return True, "Configuration is valid"
