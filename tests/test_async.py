"""Async unit tests for supabase_micro.

Tests run on CPython using standard asyncio. HTTP I/O is mocked at the
http_client.request_async level, so uasyncio is never actually invoked.
"""

import sys
import os
import json
import asyncio
import unittest
from unittest.mock import Mock, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from supabase_micro.client import SupabaseClient
from supabase_micro.postgrest import PostgrestQueryBuilder
from supabase_micro.auth import AuthClient
from supabase_micro.storage import StorageBucket


def _run(coro):
    """Run an async coroutine in a fresh event loop."""
    return asyncio.run(coro)


class TestPostgrestAsync(unittest.TestCase):

    def setUp(self):
        self.mock_client = Mock(spec=SupabaseClient)
        self.mock_client.key = "test-key"
        self.mock_client._get_auth_headers = Mock(return_value={
            "apiKey": "test-key",
            "Authorization": "Bearer test-key"
        })
        self.mock_client.http_client = Mock()

    def test_execute_async_success(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps([{"id": 1, "name": "Test"}]).encode('utf-8')
        })

        query = PostgrestQueryBuilder(self.mock_client, "test_table")
        query.select("*").limit(5)
        result = _run(query.execute_async())

        self.assertEqual(result["status_code"], 200)
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["name"], "Test")
        self.mock_client.http_client.request_async.assert_called_once()

    def test_execute_async_error(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 400,
            "body": json.dumps({"message": "Bad request"}).encode('utf-8')
        })

        query = PostgrestQueryBuilder(self.mock_client, "test_table")
        query.select("*")
        result = _run(query.execute_async())

        self.assertEqual(result["status_code"], 400)
        self.assertIn("error", result)
        self.assertEqual(result["error"]["message"], "Bad request")

    def test_execute_async_no_method(self):
        query = PostgrestQueryBuilder(self.mock_client, "test_table")
        result = _run(query.execute_async())

        self.assertEqual(result["status_code"], 400)
        self.assertIn("error", result)
        self.mock_client.http_client.request_async.assert_not_called()

    def test_execute_async_insert(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 201,
            "body": json.dumps([{"id": 42, "name": "New"}]).encode('utf-8')
        })

        query = PostgrestQueryBuilder(self.mock_client, "test_table")
        query.insert({"name": "New"})
        result = _run(query.execute_async())

        self.assertEqual(result["status_code"], 201)
        self.assertEqual(result["data"][0]["id"], 42)
        call_kwargs = self.mock_client.http_client.request_async.call_args[1]
        self.assertEqual(call_kwargs["method"], "POST")

    def test_execute_async_update(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps([{"id": 1, "name": "Updated"}]).encode('utf-8')
        })

        query = PostgrestQueryBuilder(self.mock_client, "test_table")
        query.update({"name": "Updated"}).eq("id", 1)
        result = _run(query.execute_async())

        self.assertEqual(result["status_code"], 200)
        call_kwargs = self.mock_client.http_client.request_async.call_args[1]
        self.assertEqual(call_kwargs["method"], "PATCH")

    def test_execute_async_delete(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps([]).encode('utf-8')
        })

        query = PostgrestQueryBuilder(self.mock_client, "test_table")
        query.delete().eq("id", 1)
        result = _run(query.execute_async())

        self.assertEqual(result["status_code"], 200)
        call_kwargs = self.mock_client.http_client.request_async.call_args[1]
        self.assertEqual(call_kwargs["method"], "DELETE")

    def test_execute_async_exception(self):
        self.mock_client.http_client.request_async = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        query = PostgrestQueryBuilder(self.mock_client, "test_table")
        query.select("*")
        result = _run(query.execute_async())

        self.assertEqual(result["status_code"], 500)
        self.assertIn("error", result)
        self.assertIn("Connection refused", result["error"])


class TestAuthAsync(unittest.TestCase):

    def setUp(self):
        self.mock_client = Mock(spec=SupabaseClient)
        self.mock_client.key = "test-key"
        self.mock_client.http_client = Mock()
        self.auth = AuthClient(self.mock_client)

    def test_sign_in_with_password_async(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps({
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.sig",
                "refresh_token": "refresh-123",
                "user": {"id": "123", "email": "test@example.com"}
            }).encode('utf-8')
        })

        result = _run(self.auth.sign_in_with_password_async("test@example.com", "password"))

        self.assertEqual(result["status_code"], 200)
        self.assertIn("access_token", result["data"])
        self.assertIsNotNone(self.auth._session)

    def test_sign_up_async(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps({
                "user": {"id": "123", "email": "test@example.com"},
                "session": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
                    "refresh_token": "refresh-123"
                }
            }).encode('utf-8')
        })

        result = _run(self.auth.sign_up_async("test@example.com", "password"))

        self.assertEqual(result["status_code"], 200)
        self.assertIn("user", result["data"])
        self.assertIsNotNone(self.auth._session)

    def test_sign_out_async(self):
        self.auth._set_session(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJleHAiOjEyMzQ1Njc4OTB9.sig",
            "refresh-123",
            {"id": "123"}
        )
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 204,
            "body": b""
        })

        result = _run(self.auth.sign_out_async())

        self.assertEqual(result["status_code"], 204)
        self.assertIsNone(self.auth._session)

    def test_refresh_session_async(self):
        self.auth._set_session("old-token", "refresh-123", {"id": "123"})
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps({
                "access_token": "new-token",
                "refresh_token": "new-refresh",
                "user": {"id": "123"}
            }).encode('utf-8')
        })

        result = _run(self.auth.refresh_session_async())

        self.assertEqual(result["status_code"], 200)
        self.assertNotEqual(self.auth._session["access_token"], "old-token")

    def test_refresh_session_async_no_token(self):
        result = _run(self.auth.refresh_session_async())

        self.assertEqual(result["status_code"], 400)
        self.assertIn("error", result)
        self.mock_client.http_client.request_async.assert_not_called()

    def test_update_user_async(self):
        self.auth._set_session(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjMiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjEyMzQ1Njc4OTB9.sig",
            "refresh-123",
            {"id": "123", "email": "test@example.com"}
        )
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps({
                "user": {"id": "123", "email": "test@example.com", "user_metadata": {"name": "Updated"}}
            }).encode('utf-8')
        })

        result = _run(self.auth.update_user_async({"data": {"name": "Updated"}}))
        self.assertEqual(result["status_code"], 200)

    def test_update_user_async_no_session(self):
        result = _run(self.auth.update_user_async({"data": {}}))

        self.assertEqual(result["status_code"], 401)
        self.assertIn("error", result)

    def test_reset_password_for_email_async(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps({}).encode('utf-8')
        })

        result = _run(self.auth.reset_password_for_email_async("test@example.com"))

        self.assertEqual(result["status_code"], 200)
        call_kwargs = self.mock_client.http_client.request_async.call_args[1]
        self.assertIn("/recover", call_kwargs["path"])

    def test_refresh_if_needed_async(self):
        result = _run(self.auth.refresh_if_needed_async())

        self.assertEqual(result["status_code"], 200)
        self.assertFalse(result["data"]["refreshed"])


class TestStorageAsync(unittest.TestCase):

    def setUp(self):
        self.mock_client = Mock(spec=SupabaseClient)
        self.mock_client.key = "test-key"
        self.mock_client._get_auth_headers = Mock(return_value={
            "apiKey": "test-key",
            "Authorization": "Bearer test-key"
        })
        self.mock_client.http_client = Mock()
        self.bucket = StorageBucket(self.mock_client, "test-bucket")

    def test_upload_async(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps({"Key": "test.txt"}).encode('utf-8')
        })

        result = _run(self.bucket.upload_async("test.txt", b"hello", "text/plain"))

        self.assertEqual(result["status_code"], 200)
        call_kwargs = self.mock_client.http_client.request_async.call_args[1]
        self.assertEqual(call_kwargs["method"], "POST")

    def test_download_async(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": b"file content"
        })

        result = _run(self.bucket.download_async("test.txt"))

        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["data"], b"file content")

    def test_download_async_error(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 404,
            "body": json.dumps({"message": "Not found"}).encode('utf-8')
        })

        result = _run(self.bucket.download_async("missing.txt"))

        self.assertEqual(result["status_code"], 404)
        self.assertIn("error", result)

    def test_list_async(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps([{"name": "file1.txt"}, {"name": "file2.txt"}]).encode('utf-8')
        })

        result = _run(self.bucket.list_async())

        self.assertEqual(result["status_code"], 200)
        self.assertEqual(len(result["data"]), 2)

    def test_delete_async(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps([]).encode('utf-8')
        })

        result = _run(self.bucket.delete_async("test.txt"))

        self.assertEqual(result["status_code"], 200)
        call_kwargs = self.mock_client.http_client.request_async.call_args[1]
        self.assertEqual(call_kwargs["method"], "DELETE")

    def test_delete_async_multiple(self):
        self.mock_client.http_client.request_async = AsyncMock(return_value={
            "status_code": 200,
            "body": json.dumps([]).encode('utf-8')
        })

        result = _run(self.bucket.delete_async(["file1.txt", "file2.txt"]))
        self.assertEqual(result["status_code"], 200)


class TestSyncAsyncParity(unittest.TestCase):
    """Verify sync and async methods return identical results."""

    def setUp(self):
        self.mock_client = Mock(spec=SupabaseClient)
        self.mock_client.key = "test-key"
        self.mock_client._get_auth_headers = Mock(return_value={
            "apiKey": "test-key",
            "Authorization": "Bearer test-key"
        })
        self.mock_client.http_client = Mock()

    def test_sync_and_async_same_result(self):
        response = {
            "status_code": 200,
            "body": json.dumps([{"id": 1}]).encode('utf-8')
        }
        self.mock_client.http_client.request = Mock(return_value=response)
        self.mock_client.http_client.request_async = AsyncMock(return_value=response)

        query_sync = PostgrestQueryBuilder(self.mock_client, "test")
        query_sync.select("*")
        sync_result = query_sync.execute()

        query_async = PostgrestQueryBuilder(self.mock_client, "test")
        query_async.select("*")
        async_result = _run(query_async.execute_async())

        self.assertEqual(sync_result, async_result)

    def test_sync_and_async_same_error(self):
        response = {
            "status_code": 500,
            "body": json.dumps({"message": "Server error"}).encode('utf-8')
        }
        self.mock_client.http_client.request = Mock(return_value=response)
        self.mock_client.http_client.request_async = AsyncMock(return_value=response)

        query_sync = PostgrestQueryBuilder(self.mock_client, "test")
        query_sync.select("*")
        sync_result = query_sync.execute()

        query_async = PostgrestQueryBuilder(self.mock_client, "test")
        query_async.select("*")
        async_result = _run(query_async.execute_async())

        self.assertEqual(sync_result, async_result)


if __name__ == '__main__':
    unittest.main()
