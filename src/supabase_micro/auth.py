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
    - Token refresh (manual and automatic)
    - Auto-refresh helpers
    - User operations (get, update)
    - Password reset

    Does not support:
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

        # Update session with new tokens and wrap in standard format
        if result["status_code"] == 200:
            data = result["data"]
            self._set_session(
                data.get("access_token"),
                data.get("refresh_token"),
                data.get("user")
            )
            # Wrap in standard format for consistency
            result["data"] = {"session": self._session}

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

        # Wrap user in standard format and update cached user
        if result["status_code"] == 200:
            user_data = result.get("data", {})
            # If data is the user object directly (not wrapped), wrap it
            if "id" in user_data and "user" not in user_data:
                result["data"] = {"user": user_data}
                user_data = result["data"]

            # Update cached user in session
            if self._session and "user" in user_data:
                self._session["user"] = user_data["user"]

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

    # ========================================================================
    # Async variants — mirror the sync methods above using uasyncio.
    # ========================================================================

    async def sign_up_async(self, email, password, options=None):
        """Async variant of sign_up(). Creates a new user account without blocking.

        Mirrors sign_up() but uses _request_async() instead of _request().
        Any logic change in sign_up() must be replicated here.
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

        result = await self._request_async("POST", "/signup", body)

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

    async def sign_in_with_password_async(self, email, password):
        """Async variant of sign_in_with_password(). Signs in without blocking.

        Mirrors sign_in_with_password() but uses _request_async() instead of _request().
        Any logic change in sign_in_with_password() must be replicated here.
        """
        body = {
            "email": email,
            "password": password,
            "grant_type": "password"
        }

        result = await self._request_async("POST", "/token?grant_type=password", body)

        # Store session on successful login
        if result["status_code"] == 200:
            data = result["data"]
            self._set_session(
                data.get("access_token"),
                data.get("refresh_token"),
                data.get("user")
            )

        return result

    async def sign_out_async(self):
        """Async variant of sign_out(). Signs out without blocking.

        Mirrors sign_out() but uses _request_async() instead of _request().
        Any logic change in sign_out() must be replicated here.
        """
        # Call logout endpoint if we have a session
        if self._session and self._session.get("access_token"):
            result = await self._request_async("POST", "/logout")
        else:
            result = {"data": None, "status_code": 204}

        # Always clear local session
        self._clear_session()

        return result

    async def get_user_async(self):
        """Async variant of get_user(). Fetches current user without blocking.

        Mirrors get_user() but uses _request_async() instead of _request().
        Any logic change in get_user() must be replicated here.
        """
        # Return cached user from session if available
        if self._session and self._session.get("user"):
            return {
                "data": {"user": self._session["user"]},
                "status_code": 200
            }

        # If we have a token but no user, fetch from API
        if self._session and self._session.get("access_token"):
            return await self._request_async("GET", "/user")

        # No session
        return {
            "error": {"message": "No active session"},
            "status_code": 401
        }

    async def refresh_session_async(self, refresh_token=None):
        """Async variant of refresh_session(). Refreshes access token without blocking.

        Mirrors refresh_session() but uses _request_async() instead of _request().
        Any logic change in refresh_session() must be replicated here.
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

        result = await self._request_async("POST", "/token?grant_type=refresh_token", body)

        # Update session with new tokens and wrap in standard format
        if result["status_code"] == 200:
            data = result["data"]
            self._set_session(
                data.get("access_token"),
                data.get("refresh_token"),
                data.get("user")
            )
            # Wrap in standard format for consistency
            result["data"] = {"session": self._session}

        return result

    async def update_user_async(self, attributes):
        """Async variant of update_user(). Updates user attributes without blocking.

        Mirrors update_user() but uses _request_async() instead of _request().
        Any logic change in update_user() must be replicated here.
        """
        if not self._session or not self._session.get("access_token"):
            return {
                "error": {"message": "No active session"},
                "status_code": 401
            }

        result = await self._request_async("PUT", "/user", attributes)

        # Wrap user in standard format and update cached user
        if result["status_code"] == 200:
            user_data = result.get("data", {})
            # If data is the user object directly (not wrapped), wrap it
            if "id" in user_data and "user" not in user_data:
                result["data"] = {"user": user_data}
                user_data = result["data"]

            # Update cached user in session
            if self._session and "user" in user_data:
                self._session["user"] = user_data["user"]

        return result

    async def reset_password_for_email_async(self, email, options=None):
        """Async variant of reset_password_for_email(). Sends password reset without blocking.

        Mirrors reset_password_for_email() but uses _request_async() instead of _request().
        Any logic change in reset_password_for_email() must be replicated here.
        """
        body = {"email": email}

        if options and "redirect_to" in options:
            body["options"] = {"redirect_to": options["redirect_to"]}

        return await self._request_async("POST", "/recover", body)

    async def refresh_if_needed_async(self, threshold_seconds=300):
        """Async variant of refresh_if_needed(). Auto-refreshes session without blocking.

        Mirrors refresh_if_needed() but uses async helpers.
        Any logic change in refresh_if_needed() must be replicated here.
        """
        check = self.should_refresh_token(threshold_seconds)
        should_refresh = check["data"]["should_refresh"]

        if not should_refresh:
            return {
                "data": {"refreshed": False, "session": self._session},
                "status_code": 200
            }

        # Attempt refresh
        result = await self.refresh_session_async()
        if result["status_code"] == 200:
            return {
                "data": {"refreshed": True, "session": self._session},
                "status_code": 200
            }
        else:
            # Return the error from refresh_session
            return result

    # Internal helpers

    def _build_auth_request(self, method, path, body=None):
        """Build auth request components. Shared by _request() and _request_async().

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/signup")
            body: Optional request body dict

        Returns:
            tuple: (method, full_path, headers, body_bytes)
        """
        # Build full path for auth API
        full_path = f"/auth/v1{path}"

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

        return method, full_path, headers, json.dumps(body) if body else None

    def _parse_auth_response(self, body_bytes, status_code):
        """Parse auth response. Shared by _request() and _request_async().

        Args:
            body_bytes: Raw response body bytes
            status_code: HTTP status code

        Returns:
            {"data": {...}, "status_code": 2xx}
            or {"error": {...}, "status_code": 4xx}
        """
        # Parse JSON response
        try:
            if body_bytes:
                data = json.loads(body_bytes.decode('utf-8'))
            else:
                data = {}
        except:
            # If JSON parsing fails, return error
            data = {"message": "Failed to parse response"}

        if 200 <= status_code < 300:
            return {"data": data, "status_code": status_code}
        else:
            # Error response
            return {"error": data, "status_code": status_code}

    def _request(self, method, path, body=None):
        """
        Make authenticated request to GoTrue API.

        MIRROR: Async variant _request_async() in this module.
        Any logic change here must be replicated in _request_async().

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/signup")
            body: Optional request body dict

        Returns:
            {"data": {...}, "status_code": 2xx}
            or {"error": {...}, "status_code": 4xx}
        """
        method, full_path, headers, req_body = self._build_auth_request(method, path, body)

        # Make request
        try:
            result = self._client.http_client.request(
                method=method,
                path=full_path,
                headers=headers,
                body=req_body
            )

            return self._parse_auth_response(
                result.get("body", b""),
                result.get("status_code", 500)
            )

        except Exception as e:
            return {
                "error": {"message": str(e)},
                "status_code": 500
            }

    async def _request_async(self, method, path, body=None):
        """Async variant of _request(). Makes authenticated request without blocking.

        Mirrors _request() but uses http_client.request_async() instead of request().
        Any logic change in _request() must be replicated here.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/signup")
            body: Optional request body dict

        Returns:
            {"data": {...}, "status_code": 2xx}
            or {"error": {...}, "status_code": 4xx}
        """
        method, full_path, headers, req_body = self._build_auth_request(method, path, body)

        # Make request
        try:
            result = await self._client.http_client.request_async(
                method=method,
                path=full_path,
                headers=headers,
                body=req_body
            )

            return self._parse_auth_response(
                result.get("body", b""),
                result.get("status_code", 500)
            )

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

    def should_refresh_token(self, threshold_seconds=300):
        """
        Check if access token should be refreshed.

        Checks if the current token expires within the threshold time.
        Useful for proactively refreshing tokens before they expire.

        Args:
            threshold_seconds: Refresh if expires in less than this (default: 300 = 5 min)

        Returns:
            {"data": {"should_refresh": bool, "expires_in": int}, "status_code": 200}
            or {"data": {"should_refresh": False}, "status_code": 200} if no session

        Example:
            check = client.auth.should_refresh_token()
            if check["data"]["should_refresh"]:
                print(f"Token expires in {check['data']['expires_in']} seconds")
                client.auth.refresh_session()
        """
        if not self._session or not self._session.get("expires_at"):
            return {
                "data": {"should_refresh": False},
                "status_code": 200
            }

        from .utils import get_current_timestamp
        current_time = get_current_timestamp()
        expires_at = self._session["expires_at"]
        expires_in = expires_at - current_time

        return {
            "data": {
                "should_refresh": expires_in < threshold_seconds,
                "expires_in": max(0, expires_in)
            },
            "status_code": 200
        }

    def refresh_if_needed(self, threshold_seconds=300):
        """
        Automatically refresh session if token expires soon.

        Checks if refresh is needed and performs it if necessary.
        Safe to call frequently - only refreshes when needed.

        Args:
            threshold_seconds: Refresh threshold in seconds (default: 300 = 5 min)

        Returns:
            {"data": {"refreshed": bool, "session": {...}}, "status_code": 200}
            or {"error": {...}, "status_code": 4xx} if refresh fails

        Example:
            # In a loop, check and refresh periodically
            while True:
                result = client.auth.refresh_if_needed()
                if result["data"]["refreshed"]:
                    print("Token was refreshed")

                # Do work...
                time.sleep(60)
        """
        check = self.should_refresh_token(threshold_seconds)
        should_refresh = check["data"]["should_refresh"]

        if not should_refresh:
            return {
                "data": {"refreshed": False, "session": self._session},
                "status_code": 200
            }

        # Attempt refresh
        result = self.refresh_session()
        if result["status_code"] == 200:
            return {
                "data": {"refreshed": True, "session": self._session},
                "status_code": 200
            }
        else:
            # Return the error from refresh_session
            return result
