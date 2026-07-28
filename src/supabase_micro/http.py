"""Low-level HTTP/HTTPS client for MicroPython using only built-in modules."""

import socket
import ssl
try:
    import json as _json
except ImportError:
    import ujson as _json


class HTTPClient:
    """Minimal HTTP/HTTPS client using socket and ssl modules."""

    def __init__(self, host, port=443, use_ssl=True):
        """Initialize HTTP client.

        Args:
            host: Hostname (e.g., "xxx.supabase.co")
            port: Port number (default 443 for HTTPS)
            use_ssl: Whether to use SSL/TLS (default True)
        """
        self.host = host
        self.port = port
        self.use_ssl = use_ssl

    def _build_request_bytes(self, method, path, headers, body):
        """Build HTTP request bytes. Shared by request() and request_async()."""
        request_lines = [
            f"{method} {path} HTTP/1.1",
            f"Host: {self.host}",
        ]

        # Add headers
        if headers:
            for key, value in headers.items():
                request_lines.append(f"{key}: {value}")

        # Add Content-Length if body provided
        if body:
            if isinstance(body, str):
                body = body.encode('utf-8')
            request_lines.append(f"Content-Length: {len(body)}")

        # Connection close for simplicity
        request_lines.append("Connection: close")

        # End of headers
        request_lines.append("")
        request_lines.append("")

        # Build request bytes
        request_bytes = "\r\n".join(request_lines).encode('utf-8')
        if body:
            request_bytes += body
        return request_bytes

    def request(self, method, path, headers=None, body=None):
        """Make an HTTP request.

        MIRROR: Async variant request_async() in this module.
        Any logic change here must be replicated in request_async().

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: Request path (e.g., "/rest/v1/table")
            headers: Optional dict of headers
            body: Optional request body (bytes or str)

        Returns:
            dict: {"status_code": int, "headers": dict, "body": bytes}
        """
        """Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: Request path (e.g., "/rest/v1/table")
            headers: Optional dict of headers
            body: Optional request body (bytes or str)

        Returns:
            dict: {"status_code": int, "headers": dict, "body": bytes}
        """
        sock = None
        try:
            # DNS lookup
            addr_info = socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM)
            addr = addr_info[0][-1]

            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)

            # Wrap with SSL if needed
            if self.use_ssl:
                try:
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    sock = ctx.wrap_socket(sock, server_hostname=self.host)
                except AttributeError:
                    # Fallback for older MicroPython versions
                    sock = ssl.wrap_socket(sock)

            # Build request (uses shared helper)
            request_bytes = self._build_request_bytes(method, path, headers, body)

            # Send request
            sock.write(request_bytes) if hasattr(sock, 'write') else sock.send(request_bytes)

            # Parse response
            return self._parse_response(sock)

        finally:
            if sock:
                sock.close()

    def _parse_response(self, sock):
        """Parse HTTP response.

        MIRROR: Async variant _parse_response_async() in this module.
        Any logic change here must be replicated in _parse_response_async().

        Args:
            sock: Socket to read from

        Returns:
            dict: {"status_code": int, "headers": dict, "body": bytes}
        """
        # Read status line
        status_line = self._read_line(sock).decode('utf-8')
        parts = status_line.split(' ', 2)
        status_code = int(parts[1]) if len(parts) >= 2 else 0

        # Read headers
        headers = {}
        while True:
            line = self._read_line(sock).decode('utf-8')
            if not line or line == '\r\n':
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        # Read body
        body = self._read_body(sock, headers)

        return {
            "status_code": status_code,
            "headers": headers,
            "body": body
        }

    def _read_line(self, sock):
        """Read a single line from socket (until \r\n).

        MIRROR: Async variant _read_line_async() in this module.
        Any logic change here must be replicated in _read_line_async().

        Args:
            sock: Socket to read from

        Returns:
            bytes: Line content (without \r\n)
        """
        line = b""
        while True:
            char = sock.read(1) if hasattr(sock, 'read') else sock.recv(1)
            if not char:
                break
            line += char
            if line.endswith(b"\r\n"):
                return line[:-2]
        return line

    def _read_body(self, sock, headers):
        """Read response body based on Content-Length, chunked encoding, or until EOF.

        MIRROR: Async variant _read_body_async() in this module.
        Any logic change here must be replicated in _read_body_async().

        Args:
            sock: Socket to read from
            headers: Response headers dict

        Returns:
            bytes: Response body
        """
        # Check for chunked transfer encoding
        transfer_encoding = headers.get('transfer-encoding', '').lower()

        if 'chunked' in transfer_encoding:
            # Handle chunked encoding
            chunks = []
            while True:
                # Read chunk size line (hex number)
                size_line = self._read_line(sock)
                if not size_line:
                    break

                # Parse chunk size (may have chunk extensions after ';')
                size_str = size_line.decode('utf-8').split(';')[0].strip()
                try:
                    chunk_size = int(size_str, 16)
                except ValueError:
                    break

                # If chunk size is 0, we're done
                if chunk_size == 0:
                    # Read trailing headers (if any) until empty line
                    while True:
                        trailer = self._read_line(sock)
                        if not trailer or trailer == b'':
                            break
                    break

                # Read chunk data
                chunk_data = b""
                while len(chunk_data) < chunk_size:
                    remaining = chunk_size - len(chunk_data)
                    data = sock.read(remaining) if hasattr(sock, 'read') else sock.recv(remaining)
                    if not data:
                        break
                    chunk_data += data

                chunks.append(chunk_data)

                # Read trailing \r\n after chunk data
                self._read_line(sock)

            return b"".join(chunks)

        elif headers.get('content-length'):
            # Read exact length
            length = int(headers['content-length'])
            body = b""
            while len(body) < length:
                chunk = sock.read(length - len(body)) if hasattr(sock, 'read') else sock.recv(length - len(body))
                if not chunk:
                    break
                body += chunk
            return body
        else:
            # Read until EOF (connection close)
            chunks = []
            while True:
                chunk = sock.read(1024) if hasattr(sock, 'read') else sock.recv(1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)

    # ========================================================================
    # Async variants — mirror the sync methods above using uasyncio.
    # ========================================================================

    async def request_async(self, method, path, headers=None, body=None):
        """Async variant of request(). Makes an HTTP request without blocking.

        Mirrors request() but uses asyncio.open_connection() with ssl parameter
        instead of raw socket I/O. Any logic change in request() must be replicated here.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: Request path (e.g., "/rest/v1/table")
            headers: Optional dict of headers
            body: Optional request body (bytes or str)

        Returns:
            dict: {"status_code": int, "headers": dict, "body": bytes}
        """
        import asyncio
        import ssl

        # SSL context setup (same as sync)
        ctx = None
        if self.use_ssl:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            except AttributeError:
                pass

        # Async connect with SSL (open_connection handles both TCP and SSL)
        reader, writer = await asyncio.open_connection(
            self.host, self.port, ssl=ctx, ssl_hostname=self.host
        )

        # Send request (uses shared builder)
        request_bytes = self._build_request_bytes(method, path, headers, body)
        writer.write(request_bytes)
        await writer.drain()

        # Parse response
        return await self._parse_response_async(reader)

    async def _read_line_async(self, reader):
        """Async variant of _read_line(). Reads a line (until \\r\\n) using StreamReader.

        Mirrors _read_line() but uses await reader.readline() instead of byte-at-a-time
        sock.read(1). Any logic change in _read_line() must be replicated here.

        Args:
            reader: uasyncio.StreamReader

        Returns:
            bytes: Line content (without \\r\\n)
        """
        raw = await reader.readline()
        if raw.endswith(b"\r\n"):
            return raw[:-2]
        return raw.rstrip(b"\n")

    async def _parse_response_async(self, reader):
        """Async variant of _parse_response(). Parses HTTP response using StreamReader.

        Mirrors _parse_response() but uses await reader.readline() instead of sock.read().
        Any logic change in _parse_response() must be replicated here.

        Args:
            reader: uasyncio.StreamReader

        Returns:
            dict: {"status_code": int, "headers": dict, "body": bytes}
        """
        # Read status line
        status_line = (await self._read_line_async(reader)).decode('utf-8')
        parts = status_line.split(' ', 2)
        status_code = int(parts[1]) if len(parts) >= 2 else 0

        # Read headers
        headers = {}
        while True:
            line = (await self._read_line_async(reader)).decode('utf-8')
            if not line or line == '\r\n':
                break
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        # Read body
        body = await self._read_body_async(reader, headers)

        return {
            "status_code": status_code,
            "headers": headers,
            "body": body
        }

    async def _read_body_async(self, reader, headers):
        """Async variant of _read_body(). Reads response body using StreamReader.

        Mirrors _read_body() but uses await reader.read() instead of sock.read().
        Any logic change in _read_body() must be replicated here.

        Args:
            reader: uasyncio.StreamReader
            headers: Response headers dict

        Returns:
            bytes: Response body
        """
        # Check for chunked transfer encoding
        transfer_encoding = headers.get('transfer-encoding', '').lower()

        if 'chunked' in transfer_encoding:
            # Handle chunked encoding
            chunks = []
            while True:
                # Read chunk size line (hex number)
                size_line = await self._read_line_async(reader)
                if not size_line:
                    break

                # Parse chunk size (may have chunk extensions after ';')
                size_str = size_line.decode('utf-8').split(';')[0].strip()
                try:
                    chunk_size = int(size_str, 16)
                except ValueError:
                    break

                # If chunk size is 0, we're done
                if chunk_size == 0:
                    # Read trailing headers (if any) until empty line
                    while True:
                        trailer = await self._read_line_async(reader)
                        if not trailer or trailer == b'':
                            break
                    break

                # Read chunk data
                chunk_data = b""
                while len(chunk_data) < chunk_size:
                    remaining = chunk_size - len(chunk_data)
                    data = await reader.read(remaining)
                    if not data:
                        break
                    chunk_data += data

                chunks.append(chunk_data)

                # Read trailing \\r\\n after chunk data
                await self._read_line_async(reader)

            return b"".join(chunks)

        elif headers.get('content-length'):
            # Read exact length
            length = int(headers['content-length'])
            body = b""
            while len(body) < length:
                chunk = await reader.read(length - len(body))
                if not chunk:
                    break
                body += chunk
            return body
        else:
            # Read until EOF (connection close)
            chunks = []
            while True:
                chunk = await reader.read(1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
