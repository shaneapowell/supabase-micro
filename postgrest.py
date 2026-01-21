"""PostgREST query builder for database operations."""

try:
    import json as _json
except ImportError:
    import ujson as _json

from utils import url_encode


class PostgrestQueryBuilder:
    """Query builder for PostgREST API operations.

    Supports method chaining for building queries:
    client.table("users").select("*").eq("id", 1).execute()
    """

    def __init__(self, client, table_name):
        """Initialize query builder.

        Args:
            client: SupabaseClient instance
            table_name: Name of the table
        """
        self.client = client
        self.table_name = table_name

        # Query state
        self.method = None
        self.columns = None
        self.json_body = None
        self.params = {}

    def select(self, columns="*"):
        """Select data from table.

        Args:
            columns: Columns to select (default "*" for all)
                    Can be comma-separated: "name,email"

        Returns:
            self: For method chaining
        """
        self.method = "GET"
        self.columns = columns
        self.params["select"] = columns
        return self

    def insert(self, data):
        """Insert data into table.

        Args:
            data: Dict or list of dicts to insert

        Returns:
            self: For method chaining
        """
        self.method = "POST"
        self.json_body = data
        # Request full representation of inserted row
        self.params["select"] = "*"
        return self

    def update(self, data):
        """Update data in table.

        Args:
            data: Dict with fields to update

        Returns:
            self: For method chaining
        """
        self.method = "PATCH"
        self.json_body = data
        # Request full representation of updated rows
        self.params["select"] = "*"
        return self

    def delete(self):
        """Delete data from table.

        Returns:
            self: For method chaining
        """
        self.method = "DELETE"
        return self

    def eq(self, column, value):
        """Filter: column equals value.

        Args:
            column: Column name
            value: Value to match

        Returns:
            self: For method chaining
        """
        self.params[column] = f"eq.{value}"
        return self

    def neq(self, column, value):
        """Filter: column not equals value.

        Args:
            column: Column name
            value: Value to match

        Returns:
            self: For method chaining
        """
        self.params[column] = f"neq.{value}"
        return self

    def gt(self, column, value):
        """Filter: column greater than value.

        Args:
            column: Column name
            value: Value to compare

        Returns:
            self: For method chaining
        """
        self.params[column] = f"gt.{value}"
        return self

    def gte(self, column, value):
        """Filter: column greater than or equal to value.

        Args:
            column: Column name
            value: Value to compare

        Returns:
            self: For method chaining
        """
        self.params[column] = f"gte.{value}"
        return self

    def lt(self, column, value):
        """Filter: column less than value.

        Args:
            column: Column name
            value: Value to compare

        Returns:
            self: For method chaining
        """
        self.params[column] = f"lt.{value}"
        return self

    def lte(self, column, value):
        """Filter: column less than or equal to value.

        Args:
            column: Column name
            value: Value to compare

        Returns:
            self: For method chaining
        """
        self.params[column] = f"lte.{value}"
        return self

    def limit(self, count):
        """Limit number of results.

        Args:
            count: Maximum number of rows to return

        Returns:
            self: For method chaining
        """
        self.params["limit"] = str(count)
        return self

    def order(self, column, desc=False):
        """Order results by column.

        Args:
            column: Column name to order by
            desc: Whether to order descending (default False)

        Returns:
            self: For method chaining
        """
        order_value = f"{column}.desc" if desc else f"{column}.asc"
        self.params["order"] = order_value
        return self

    def execute(self):
        """Execute the query and return results.

        Returns:
            dict: {"data": [...], "status_code": 200} on success
                  {"error": {...}, "status_code": 4xx} on error
        """
        if not self.method:
            return {
                "error": "No method specified. Use select(), insert(), update(), or delete().",
                "status_code": 400
            }

        # Build path
        path = f"/rest/v1/{self.table_name}"

        # Build query string
        if self.params:
            query_string = url_encode(self.params)
            path = f"{path}?{query_string}"

        # Build headers
        headers = self.client._get_auth_headers()
        headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Profile": "public",
            "Content-Profile": "public"
        })

        # Add Prefer header for POST and PATCH to return representation
        if self.method in ["POST", "PATCH"]:
            headers["Prefer"] = "return=representation"

        # Build body
        body = None
        if self.json_body is not None:
            body = _json.dumps(self.json_body)

        # Make request
        try:
            response = self.client.http_client.request(
                method=self.method,
                path=path,
                headers=headers,
                body=body
            )

            status_code = response["status_code"]
            response_body = response["body"]

            # Parse JSON response
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

        except Exception as e:
            return {
                "error": str(e),
                "status_code": 500
            }
