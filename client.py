"""Main Supabase client for MicroPython."""

from http import HTTPClient
from utils import parse_url
from postgrest import PostgrestQueryBuilder
from storage import StorageClient


class SupabaseClient:
    """Minimal Supabase client for MicroPython.

    Provides access to PostgREST (database) and Storage APIs.
    """

    def __init__(self, url, key):
        """Initialize Supabase client.

        Args:
            url: Supabase project URL (e.g., "https://xxx.supabase.co")
            key: Supabase API key (anon or service key)

        Raises:
            Exception: If url or key is missing
        """
        if not url:
            raise Exception("supabase_url is required")
        if not key:
            raise Exception("supabase_key is required")

        self.url = url.rstrip("/")
        self.key = key

        # Parse URL components
        parsed = parse_url(self.url)
        self.host = parsed["host"]
        self.port = parsed["port"]
        self.use_ssl = parsed["scheme"] == "https"

        # Create HTTP client
        self.http_client = HTTPClient(
            host=self.host,
            port=self.port,
            use_ssl=self.use_ssl
        )

        # Initialize storage client
        self.storage = StorageClient(self)

    def table(self, table_name):
        """Access a table for PostgREST operations.

        Args:
            table_name: Name of the table

        Returns:
            PostgrestQueryBuilder: Query builder instance
        """
        return PostgrestQueryBuilder(self, table_name)

    def _get_auth_headers(self):
        """Get authentication headers for API requests.

        Returns:
            dict: Headers with API key and authorization
        """
        return {
            "apiKey": self.key,
            "Authorization": f"Bearer {self.key}"
        }
