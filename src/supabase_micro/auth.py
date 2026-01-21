"""
Authentication client for Supabase GoTrue API.

Provides email/password authentication, session management, and user operations
for MicroPython IoT devices. Uses zero external dependencies.
"""

try:
    import ujson as json
except ImportError:
    import json

import binascii
import time


class AuthClient:
    """
    Client for Supabase authentication operations.

    Supports:
    - Email/password signup and signin
    - Session management (in-memory only)
    - Token refresh
    - User operations (get, update)
    - Password reset

    Does not support:
    - Auto-refresh (manual refresh only)
    - Session persistence to disk
    - OAuth providers
    - MFA/OTP
    """

    def __init__(self, client):
        """
        Initialize auth client.

        Args:
            client: Parent SupabaseClient instance
        """
        self._client = client
        self._session = None
        self._auth_url = f"{client.url}/auth/v1"

    def sign_up(self, email, password, options=None):
        """
        Create a new user account.

        Args:
            email: User's email address
            password: User's password
            options: Optional dict with:
                - data: User metadata dict
                - redirect_to: URL to redirect after email confirmation

        Returns:
            {"data": {"user": {...}, "session": {...}}, "status_code": 200}
            or {"error": {...}, "status_code": 4xx}
        """
        body = {
            "email": email,
            "password": password
        }

        if options:
            if "data" in options:
                body["data"] = options["data"]
            if "redirect_to" in options:
                body["options"] = {"redirect_to": options["redirect_to"]}

        result = self._request("POST", "/signup", body)

        # If signup successful and session returned, store it
        if result["status_code"] == 200 and "session" in result.get("data", {}):
            session = result["data"]["session"]
            if session.get("access_token"):
                self._set_session(
                    session["access_token"],
                    session.get("refresh_token"),
                    result["data"].get("user")
                )

        return result

    def sign_in_with_password(self, email, password):
        """
        Sign in with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            {"data": {"user": {...}, "session": {...}}, "status_code": 200}
            or {"error": {...}, "status_code": 4xx}
        """
        body = {
            "email": email,
            "password": password,
            "grant_type": "password"
        }

        result = self._request("POST", "/token?grant_type=password", body)

        # Store session on successful login
        if result["status_code"] == 200:
            data = result["data"]
            self._set_session(
                data.get("access_token"),
                data.get("refresh_token"),
                data.get("user")
            )

        return result

    def sign_out(self):
        """
        Sign out current user and clear session.

        Returns:
            {"data": None, "status_code": 204}
            or {"error": {...}, "status_code": 4xx}
        """
        # Call logout endpoint if we have a session
        if self._session and self._session.get("access_token"):
            result = self._request("POST", "/logout")
        else:
            result = {"data": None, "status_code": 204}

        # Always clear local session
        self._clear_session()

        return result

    def get_session(self):
        """
        Get current session.

        Returns:
            {"data": {"session": {...}}, "status_code": 200}
            or {"data": {"session": None}, "status_code": 200} if no session
        """
        return {
            "data": {"session": self._session},
            "status_code": 200
        }

    def get_user(self):
        """
        Get current user from session or fetch from API.

        Returns:
            {"data": {"user": {...}}, "status_code": 200}
            or {"error": {...}, "status_code": 4xx}
        """
        # Return cached user from session if available
        if self._session and self._session.get("user"):
            return {
                "data": {"user": self._session["user"]},
                "status_code": 200
            }

        # If we have a token but no user, fetch from API
        if self._session and self._session.get("access_token"):
            return self._request("GET", "/user")

        # No session
        return {
            "error": {"message": "No active session"},
            "status_code": 401
        }

    def refresh_session(self, refresh_token=None):
        """
        Refresh the access token using a refresh token.

        Args:
            refresh_token: Refresh token (uses current session token if not provided)

        Returns:
            {"data": {"session": {...}}, "status_code": 200}
            or {"error": {...}, "status_code": 4xx}
        """
        # Get refresh token from parameter or current session
        token = refresh_token
        if not token and self._session:
            token = self._session.get("refresh_token")

        if not token:
            return {
                "error": {"message": "No refresh token available"},
                "status_code": 400
            }

        body = {
            "refresh_token": token,
            "grant_type": "refresh_token"
        }

        result = self._request("POST", "/token?grant_type=refresh_token", body)

        # Update session with new tokens
        if result["status_code"] == 200:
            data = result["data"]
            self._set_session(
                data.get("access_token"),
                data.get("refresh_token"),
                data.get("user")
            )

        return result

    def update_user(self, attributes):
        """
        Update current user's attributes.

        Args:
            attributes: Dict with fields to update:
                - email: New email address
                - password: New password
                - data: User metadata dict

        Returns:
            {"data": {"user": {...}}, "status_code": 200}
            or {"error": {...}, "status_code": 4xx}
        """
        if not self._session or not self._session.get("access_token"):
            return {
                "error": {"message": "No active session"},
                "status_code": 401
            }

        result = self._request("PUT", "/user", attributes)

        # Update cached user in session
        if result["status_code"] == 200 and "user" in result.get("data", {}):
            if self._session:
                self._session["user"] = result["data"]["user"]

        return result

    def reset_password_for_email(self, email, options=None):
        """
        Send password reset email.

        Args:
            email: User's email address
            options: Optional dict with:
                - redirect_to: URL to redirect after password reset

        Returns:
            {"data": {}, "status_code": 200}
            or {"error": {...}, "status_code": 4xx}
        """
        body = {"email": email}

        if options and "redirect_to" in options:
            body["options"] = {"redirect_to": options["redirect_to"]}

        return self._request("POST", "/recover", body)

    # Internal helpers

    def _request(self, method, path, body=None):
        """
        Make authenticated request to GoTrue API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/signup")
            body: Optional request body dict

        Returns:
            {"data": {...}, "status_code": 2xx}
            or {"error": {...}, "status_code": 4xx}
        """
        url = f"{self._auth_url}{path}"

        # Build headers
        headers = {
            "apiKey": self._client.key,
            "Content-Type": "application/json"
        }

        # Add auth token if available
        if self._session and self._session.get("access_token"):
            headers["Authorization"] = f"Bearer {self._session['access_token']}"
        else:
            headers["Authorization"] = f"Bearer {self._client.key}"

        # Make request
        try:
            result = self._client.http_client.request(
                method=method,
                url=url,
                headers=headers,
                body=json.dumps(body) if body else None
            )

            # Parse response
            status_code = result.get("status_code", 500)
            response_body = result.get("body", {})

            if 200 <= status_code < 300:
                return {"data": response_body, "status_code": status_code}
            else:
                # Error response
                error = response_body if isinstance(response_body, dict) else {"message": str(response_body)}
                return {"error": error, "status_code": status_code}

        except Exception as e:
            return {
                "error": {"message": str(e)},
                "status_code": 500
            }

    def _set_session(self, access_token, refresh_token, user=None):
        """
        Store session in memory.

        Args:
            access_token: JWT access token
            refresh_token: Refresh token
            user: Optional user dict
        """
        # Decode JWT to get expiration time
        expires_at = None
        if access_token:
            payload = self._decode_jwt_payload(access_token)
            if payload and "exp" in payload:
                expires_at = payload["exp"]

            # Extract user from JWT if not provided
            if not user and payload:
                user = {
                    "id": payload.get("sub"),
                    "email": payload.get("email"),
                    "user_metadata": payload.get("user_metadata", {})
                }

        self._session = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "user": user
        }

    def _clear_session(self):
        """Clear session from memory."""
        self._session = None

    def _decode_jwt_payload(self, token):
        """
        Decode JWT payload without signature verification.

        SECURITY NOTE: This does not verify the JWT signature.
        Assumes HTTPS transport and server-side validation.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dict or None on error
        """
        try:
            # Split token into parts
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Get payload (second part)
            payload_b64 = parts[1]

            # Add padding if needed (base64url requires multiple of 4)
            padding = 4 - (len(payload_b64) % 4)
            if padding != 4:
                payload_b64 += "=" * padding

            # Decode base64 (handle base64url: replace - with + and _ with /)
            payload_b64 = payload_b64.replace("-", "+").replace("_", "/")
            payload_bytes = binascii.a2b_base64(payload_b64)

            # Parse JSON
            payload = json.loads(payload_bytes)
            return payload

        except Exception:
            return None
