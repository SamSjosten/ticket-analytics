"""
Auth0 authentication manager for Streamlit application.
"""
import logging
import secrets
import hashlib
import base64
import json
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from pathlib import Path

import streamlit as st
import requests

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.auth0_config import Auth0Config
from src.db_connector import SQLServerConnector

logger = logging.getLogger(__name__)


class Auth0Manager:
    """Manage Auth0 authentication flows and user sessions."""

    def __init__(self):
        """Initialize Auth0 manager."""
        self.config = Auth0Config
        # Use a temp file to persist OAuth state across redirects
        self.state_file = Path(tempfile.gettempdir()) / "streamlit_auth_states.json"

    def _load_states(self) -> dict:
        """Load OAuth states from temp file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load states: {e}")
        return {}

    def _save_states(self, states: dict):
        """Save OAuth states to temp file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(states, f)
        except Exception as e:
            logger.error(f"Failed to save states: {e}")

    def _cleanup_expired_states(self, states: dict) -> dict:
        """Remove expired states (older than 10 minutes)."""
        current_time = datetime.now()
        return {
            state: data for state, data in states.items()
            if (current_time - datetime.fromisoformat(data['timestamp'])).total_seconds() <= 600
        }

    def generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.

        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate cryptographically secure random verifier
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        code_verifier = code_verifier.rstrip('=')

        # Create SHA256 hash challenge
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.rstrip('=')

        return code_verifier, code_challenge

    def get_authorization_url(self) -> tuple[str, str, str]:
        """
        Generate Auth0 authorization URL with PKCE.

        Returns:
            Tuple of (auth_url, state, code_verifier)
        """
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Generate PKCE pair
        code_verifier, code_challenge = self.generate_pkce_pair()

        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.config.CLIENT_ID,
            'redirect_uri': self.config.CALLBACK_URL,
            'scope': self.config.SCOPE,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'prompt': 'login'  # Force login screen (allows switching accounts)
        }

        if self.config.AUDIENCE:
            params['audience'] = self.config.AUDIENCE

        auth_url = f"{self.config.get_authorize_url()}?{urlencode(params)}"

        return auth_url, state, code_verifier

    def exchange_code_for_token(self, code: str, code_verifier: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            code_verifier: PKCE code verifier

        Returns:
            Token response dict or None if failed
        """
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.config.CLIENT_ID,
            'client_secret': self.config.CLIENT_SECRET,
            'code': code,
            'redirect_uri': self.config.CALLBACK_URL,
            'code_verifier': code_verifier
        }

        try:
            response = requests.post(
                self.config.get_token_url(),
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            return None

    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Auth0.

        Args:
            access_token: Access token from Auth0

        Returns:
            User info dict or None if failed
        """
        try:
            response = requests.get(
                self.config.get_userinfo_url(),
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    def sync_user_to_database(self, user_info: Dict[str, Any]) -> bool:
        """
        Sync user information to SQL Server database.

        Args:
            user_info: User information from Auth0

        Returns:
            True if successful, False otherwise
        """
        try:
            # Log received user info for debugging
            logger.info(f"Syncing user to database. User info received: {user_info}")

            connector = SQLServerConnector()
            connector.connect()

            # Extract user data with proper defaults
            auth0_id = user_info.get('sub')  # Subject identifier

            # Email - try multiple fields
            email = user_info.get('email') or user_info.get('preferred_username') or ''

            # Name - try multiple fields with fallbacks
            name = (user_info.get('name') or
                   user_info.get('nickname') or
                   user_info.get('given_name') or
                   (email.split('@')[0] if email else 'Unknown User'))

            # Picture URL
            picture = user_info.get('picture') or ''

            # Email verification status
            email_verified = bool(user_info.get('email_verified', False))

            # Validate required fields
            if not auth0_id:
                logger.error("Cannot sync user: missing auth0_id (sub)")
                return False

            if not email:
                logger.warning(f"User {auth0_id} has no email address")
                email = f"{auth0_id}@unknown.auth0"

            # Check if user exists
            cursor = connector.connection.cursor()
            cursor.execute(
                f"SELECT user_id FROM {self.config.USERS_TABLE} WHERE auth0_id = ?",
                (auth0_id,)
            )
            existing_user = cursor.fetchone()

            if existing_user:
                # Update existing user - only update non-empty values
                update_sql = f"""
                    UPDATE {self.config.USERS_TABLE}
                    SET email = ?,
                        name = ?,
                        picture = ?,
                        email_verified = ?,
                        last_login = GETDATE()
                    WHERE auth0_id = ?
                """
                cursor.execute(update_sql, (email, name, picture, email_verified, auth0_id))
                logger.info(f"Updated user: {email} (name: {name})")
            else:
                # Insert new user
                insert_sql = f"""
                    INSERT INTO {self.config.USERS_TABLE}
                    (auth0_id, email, name, picture, email_verified, created_at, last_login, role)
                    VALUES (?, ?, ?, ?, ?, GETDATE(), GETDATE(), 'user')
                """
                cursor.execute(insert_sql, (auth0_id, email, name, picture, email_verified))
                logger.info(f"Created new user: {email} (name: {name})")

            connector.connection.commit()
            cursor.close()
            connector.disconnect()

            return True

        except Exception as e:
            logger.error(f"Failed to sync user to database: {e}")
            return False

    def get_user_from_database(self, auth0_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from database.

        Args:
            auth0_id: Auth0 user identifier

        Returns:
            User data dict or None if not found
        """
        try:
            connector = SQLServerConnector()
            connector.connect()

            cursor = connector.connection.cursor()
            cursor.execute(
                f"""SELECT user_id, auth0_id, email, name, picture,
                          email_verified, created_at, last_login, role, is_active
                   FROM {self.config.USERS_TABLE}
                   WHERE auth0_id = ?""",
                (auth0_id,)
            )

            row = cursor.fetchone()
            cursor.close()
            connector.disconnect()

            if row:
                return {
                    'user_id': row[0],
                    'auth0_id': row[1],
                    'email': row[2],
                    'name': row[3],
                    'picture': row[4],
                    'email_verified': row[5],
                    'created_at': row[6],
                    'last_login': row[7],
                    'role': row[8],
                    'is_active': row[9]
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get user from database: {e}")
            return None

    def initialize_session_state(self):
        """Initialize session state variables for authentication."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'access_token' not in st.session_state:
            st.session_state.access_token = None
        if 'token_expires_at' not in st.session_state:
            st.session_state.token_expires_at = None
        if 'auth_state' not in st.session_state:
            st.session_state.auth_state = None
        if 'code_verifier' not in st.session_state:
            st.session_state.code_verifier = None

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated and token is valid.

        Returns:
            True if authenticated with valid token, False otherwise
        """
        if not st.session_state.get('authenticated', False):
            return False

        # Check token expiration
        expires_at = st.session_state.get('token_expires_at')
        if expires_at and datetime.now() > expires_at:
            logger.info("Token expired, logging out")
            self.logout()
            return False

        # Check if user is active in database
        user_info = st.session_state.get('user_info')
        if user_info:
            db_user = self.get_user_from_database(user_info.get('sub'))
            if db_user and not db_user.get('is_active', True):
                logger.warning(f"User {user_info.get('email')} is inactive")
                self.logout()
                return False

        return True

    def login(self) -> str:
        """
        Initiate Auth0 login flow.

        Returns:
            Authorization URL to redirect to
        """
        auth_url, state, code_verifier = self.get_authorization_url()

        # Load existing states and clean up expired ones
        states = self._load_states()
        states = self._cleanup_expired_states(states)

        # Store new state with verifier
        states[state] = {
            'code_verifier': code_verifier,
            'timestamp': datetime.now().isoformat()
        }

        # Save to temp file (persists across redirects)
        self._save_states(states)

        return auth_url

    def handle_callback(self, code: str, state: str) -> tuple[bool, str]:
        """
        Handle OAuth callback and complete authentication.

        Args:
            code: Authorization code from callback
            state: State parameter from callback

        Returns:
            Tuple of (success, error_message)
        """
        # Load states from temp file
        states = self._load_states()

        if state not in states:
            error_msg = f"Invalid or expired state parameter"
            logger.error(error_msg)
            return False, error_msg

        verifier_data = states[state]
        code_verifier = verifier_data.get('code_verifier')

        # Check if verifier has expired (10 minutes)
        timestamp_str = verifier_data.get('timestamp')
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
            if (datetime.now() - timestamp).total_seconds() > 600:
                error_msg = "Authentication session expired. Please try logging in again."
                logger.error(error_msg)
                # Clean up expired verifier
                del states[state]
                self._save_states(states)
                return False, error_msg

        # Validate code_verifier exists
        if not code_verifier:
            error_msg = "Code verifier not found"
            logger.error(error_msg)
            return False, error_msg

        token_response = self.exchange_code_for_token(code, code_verifier)

        if not token_response:
            error_msg = "Failed to exchange authorization code for token. Check Auth0 configuration."
            logger.error(error_msg)
            return False, error_msg

        # Get user info
        access_token = token_response.get('access_token')
        if not access_token:
            error_msg = "No access token in response"
            logger.error(error_msg)
            return False, error_msg

        user_info = self.get_user_info(access_token)

        if not user_info:
            error_msg = "Failed to retrieve user info from Auth0"
            logger.error(error_msg)
            return False, error_msg

        # Sync user to database
        try:
            self.sync_user_to_database(user_info)
        except Exception as e:
            logger.warning(f"Failed to sync user to database: {e}")
            # Continue with authentication even if DB sync fails

        # Store in session state
        st.session_state.authenticated = True
        st.session_state.user_info = user_info
        st.session_state.access_token = access_token

        # Calculate token expiration
        expires_in = token_response.get('expires_in', self.config.SESSION_LIFETIME)
        st.session_state.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Clear temporary auth data - remove the used verifier from file
        if state in states:
            del states[state]
            self._save_states(states)

        logger.info(f"User authenticated: {user_info.get('email')}")
        return True, "Authentication successful"

    def logout(self):
        """Logout user and clear session state."""
        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.access_token = None
        st.session_state.token_expires_at = None
        st.session_state.auth_state = None
        st.session_state.code_verifier = None

        logger.info("User logged out")

    def get_logout_url(self) -> str:
        """
        Get Auth0 logout URL.

        Returns:
            Logout URL with return_to parameter
        """
        params = {
            'client_id': self.config.CLIENT_ID,
            'returnTo': self.config.CALLBACK_URL
        }
        return f"{self.config.get_logout_url()}?{urlencode(params)}"

    def check_user_role(self, required_role: str) -> bool:
        """
        Check if current user has required role.

        Args:
            required_role: Role name to check

        Returns:
            True if user has role, False otherwise
        """
        if not self.is_authenticated():
            return False

        user_info = st.session_state.get('user_info')
        if not user_info:
            return False

        # Get user from database to check role
        db_user = self.get_user_from_database(user_info.get('sub'))
        if not db_user:
            return False

        user_role = db_user.get('role', 'user')

        # Simple role hierarchy (can be made more sophisticated)
        role_hierarchy = {
            'admin': ['admin', 'analyst', 'user'],
            'analyst': ['analyst', 'user'],
            'user': ['user']
        }

        allowed_roles = role_hierarchy.get(user_role, ['user'])
        return required_role in allowed_roles
