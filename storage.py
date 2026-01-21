"""Supabase Storage API for file operations."""

try:
    import json as _json
except ImportError:
    import ujson as _json

from utils import generate_boundary, build_multipart_body


class StorageClient:
    """Storage client for managing buckets."""

    def __init__(self, client):
        """Initialize storage client.

        Args:
            client: SupabaseClient instance
        """
        self.client = client

    def from_(self, bucket_name):
        """Access a storage bucket.

        Args:
            bucket_name: Name of the bucket

        Returns:
            StorageBucket: Bucket instance for operations
        """
        return StorageBucket(self.client, bucket_name)


class StorageBucket:
    """Storage bucket for file operations."""

    def __init__(self, client, bucket_name):
        """Initialize storage bucket.

        Args:
            client: SupabaseClient instance
            bucket_name: Name of the bucket
        """
        self.client = client
        self.bucket_name = bucket_name

    def upload(self, path, data, content_type=None):
        """Upload a file to the bucket.

        Args:
            path: Path/filename in the bucket (e.g., "folder/file.jpg")
            data: File content (bytes)
            content_type: Optional MIME type (auto-detected if not provided)

        Returns:
            dict: {"data": {...}, "status_code": 200} on success
                  {"error": {...}, "status_code": 4xx} on error
        """
        # Generate multipart boundary
        boundary = generate_boundary()

        # Build multipart body
        body = build_multipart_body(boundary, path, data, content_type)

        # Build path
        api_path = f"/storage/v1/object/{self.bucket_name}/{path}"

        # Build headers
        headers = self.client._get_auth_headers()
        headers.update({
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        })

        # Make request
        try:
            response = self.client.http_client.request(
                method="POST",
                path=api_path,
                headers=headers,
                body=body
            )

            return self._parse_response(response)

        except Exception as e:
            return {
                "error": str(e),
                "status_code": 500
            }

    def download(self, path):
        """Download a file from the bucket.

        Args:
            path: Path/filename in the bucket

        Returns:
            dict: {"data": bytes, "status_code": 200} on success
                  {"error": {...}, "status_code": 4xx} on error
        """
        # Build path
        api_path = f"/storage/v1/object/{self.bucket_name}/{path}"

        # Build headers
        headers = self.client._get_auth_headers()

        # Make request
        try:
            response = self.client.http_client.request(
                method="GET",
                path=api_path,
                headers=headers
            )

            status_code = response["status_code"]

            if 200 <= status_code < 300:
                # Return raw bytes for successful download
                return {
                    "data": response["body"],
                    "status_code": status_code
                }
            else:
                # Try to parse error as JSON
                try:
                    error = _json.loads(response["body"].decode('utf-8'))
                except:
                    error = response["body"].decode('utf-8') if response["body"] else "Unknown error"

                return {
                    "error": error,
                    "status_code": status_code
                }

        except Exception as e:
            return {
                "error": str(e),
                "status_code": 500
            }

    def list(self, path="", limit=100):
        """List files in a bucket path.

        Args:
            path: Optional folder path to list (default "" for root)
            limit: Maximum number of files to return (default 100)

        Returns:
            dict: {"data": [...], "status_code": 200} on success
                  {"error": {...}, "status_code": 4xx} on error
        """
        # Build path
        api_path = f"/storage/v1/object/list/{self.bucket_name}"

        # Build headers
        headers = self.client._get_auth_headers()
        headers.update({
            "Content-Type": "application/json"
        })

        # Build body
        body = _json.dumps({
            "prefix": path,
            "limit": limit
        })

        # Make request
        try:
            response = self.client.http_client.request(
                method="POST",
                path=api_path,
                headers=headers,
                body=body
            )

            return self._parse_response(response)

        except Exception as e:
            return {
                "error": str(e),
                "status_code": 500
            }

    def delete(self, paths):
        """Delete file(s) from the bucket.

        Args:
            paths: Single path string or list of paths to delete

        Returns:
            dict: {"data": {...}, "status_code": 200} on success
                  {"error": {...}, "status_code": 4xx} on error
        """
        # Ensure paths is a list
        if isinstance(paths, str):
            paths = [paths]

        # Build path
        api_path = f"/storage/v1/object/{self.bucket_name}"

        # Build headers
        headers = self.client._get_auth_headers()
        headers.update({
            "Content-Type": "application/json"
        })

        # Build body
        body = _json.dumps({
            "prefixes": paths
        })

        # Make request
        try:
            response = self.client.http_client.request(
                method="DELETE",
                path=api_path,
                headers=headers,
                body=body
            )

            return self._parse_response(response)

        except Exception as e:
            return {
                "error": str(e),
                "status_code": 500
            }

    def _parse_response(self, response):
        """Parse HTTP response into standard format.

        Args:
            response: HTTP response dict

        Returns:
            dict: Standardized response
        """
        status_code = response["status_code"]
        response_body = response["body"]

        # Try to parse JSON response
        try:
            if response_body:
                data = _json.loads(response_body.decode('utf-8'))
            else:
                data = None
        except (ValueError, UnicodeDecodeError):
            # If JSON parsing fails, return raw body
            data = response_body.decode('utf-8') if response_body else None

        # Return success or error based on status code
        if 200 <= status_code < 300:
            return {
                "data": data,
                "status_code": status_code
            }
        else:
            return {
                "error": data,
                "status_code": status_code
            }
