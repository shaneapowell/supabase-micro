"""Minimal MicroPython Supabase client library.

A dependency-free Supabase client for MicroPython that supports
PostgREST (database operations) and Storage (file operations).

Example usage:
    from supabase_micro import create_client

    client = create_client("https://xxx.supabase.co", "your-anon-key")

    # Query data
    result = client.table("countries").select("*").execute()
    print(result["data"])

    # Insert data
    result = client.table("countries").insert({"name": "Test"}).execute()

    # Update data
    result = client.table("countries").update({"name": "Updated"}).eq("id", 1).execute()

    # Delete data
    result = client.table("countries").delete().eq("id", 1).execute()
"""

from .client import SupabaseClient

__version__ = "0.1.0"
__all__ = ["create_client", "SupabaseClient"]


def create_client(url, key):
    """Create a Supabase client instance.

    Args:
        url: Supabase project URL (e.g., "https://xxx.supabase.co")
        key: Supabase API key (anon or service key)

    Returns:
        SupabaseClient: Initialized client instance

    Raises:
        Exception: If url or key is missing

    Example:
        >>> client = create_client("https://xxx.supabase.co", "your-key")
        >>> result = client.table("users").select("*").execute()
    """
    return SupabaseClient(url, key)
