"""Helper utility functions for URL parsing, encoding, and multipart."""

try:
    import time
except ImportError:
    import utime as time


def parse_url(url):
    """Parse URL into components.

    Args:
        url: URL string (e.g., "https://xxx.supabase.co/path")

    Returns:
        dict: {"scheme": str, "host": str, "port": int, "path": str}
    """
    # Remove scheme
    if "://" in url:
        scheme, rest = url.split("://", 1)
    else:
        scheme = "https"
        rest = url

    # Extract host and path
    if "/" in rest:
        host, path = rest.split("/", 1)
        path = "/" + path
    else:
        host = rest
        path = "/"

    # Extract port if present
    if ":" in host:
        host, port_str = host.split(":", 1)
        port = int(port_str)
    else:
        port = 443 if scheme == "https" else 80

    return {
        "scheme": scheme,
        "host": host,
        "port": port,
        "path": path
    }


def url_encode_value(value):
    """URL encode a single value.

    Args:
        value: Value to encode (str, int, float, bool)

    Returns:
        str: URL-encoded value
    """
    if value is None:
        return ""

    # Convert to string
    s = str(value)

    # URL encode - simple implementation
    result = []
    for char in s:
        # Check if alphanumeric (MicroPython compatible)
        is_alnum = ('a' <= char <= 'z') or ('A' <= char <= 'Z') or ('0' <= char <= '9')
        if is_alnum or char in "-_.~":
            result.append(char)
        elif char == " ":
            result.append("+")
        else:
            # Encode as hex
            result.append("%%%02X" % ord(char))

    return "".join(result)


def url_encode(params):
    """Convert dict to URL query string.

    Args:
        params: Dict of query parameters

    Returns:
        str: URL-encoded query string (e.g., "key1=value1&key2=value2")
    """
    if not params:
        return ""

    parts = []
    for key, value in params.items():
        encoded_key = url_encode_value(key)
        encoded_value = url_encode_value(value)
        parts.append(f"{encoded_key}={encoded_value}")

    return "&".join(parts)


def generate_boundary():
    """Generate a unique boundary for multipart/form-data.

    Returns:
        str: Boundary string
    """
    try:
        timestamp = time.ticks_ms()
    except AttributeError:
        # Fallback for CPython or different MicroPython versions
        import time as _time
        timestamp = int(_time.time() * 1000)

    return f"----MicroPythonBoundary{timestamp}"


def build_multipart_body(boundary, file_path, file_data, content_type=None):
    """Build multipart/form-data body for file upload.

    Args:
        boundary: Boundary string
        file_path: Path/filename for the uploaded file
        file_data: File content (bytes)
        content_type: Optional MIME type (default: application/octet-stream)

    Returns:
        bytes: Complete multipart body
    """
    if content_type is None:
        content_type = guess_content_type(file_path)

    # Extract filename from path
    filename = file_path.split("/")[-1]

    # Build multipart body
    parts = []

    # Start boundary
    parts.append(f"--{boundary}\r\n".encode('utf-8'))

    # Content-Disposition header
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode('utf-8'))

    # Content-Type header
    parts.append(f"Content-Type: {content_type}\r\n\r\n".encode('utf-8'))

    # File data
    parts.append(file_data)

    # End boundary
    parts.append(f"\r\n--{boundary}--\r\n".encode('utf-8'))

    return b"".join(parts)


def guess_content_type(path):
    """Guess MIME type from file extension.

    Args:
        path: File path or name

    Returns:
        str: MIME type
    """
    ext = path.lower().split(".")[-1] if "." in path else ""

    mime_types = {
        # Images
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "ico": "image/x-icon",

        # Text
        "txt": "text/plain",
        "html": "text/html",
        "css": "text/css",
        "js": "application/javascript",
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",

        # Documents
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

        # Archives
        "zip": "application/zip",
        "tar": "application/x-tar",
        "gz": "application/gzip",

        # Audio/Video
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
    }

    return mime_types.get(ext, "application/octet-stream")


def get_current_timestamp():
    """
    Get current Unix timestamp (MicroPython compatible).

    Returns:
        int: Current Unix timestamp in seconds

    Example:
        >>> timestamp = get_current_timestamp()
        >>> print(timestamp)
        1704067200
    """
    try:
        import time
    except ImportError:
        import utime as time

    # Check for an abnormal 2000 epoch, used on some microcontrollers.
    # If this is a 2000 EPOCH board, offset by the missing 30 years (946684800).
    # That value is the number of seconds between 1970-01-01 and 2000-01-01
    #  (30 years, including 7 leap years: 30 * 365.25 * 86400 = 946684800).
    t = int(time.time())
    if time.gmtime(0)[0] == 2000:
        t += 946684800
    return t
