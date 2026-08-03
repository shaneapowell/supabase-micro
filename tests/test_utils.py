"""Unit tests for supabase_micro utils module."""

import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestEpoch2000(unittest.TestCase):
    """Test 2000-epoch detection and offset in get_current_timestamp.

    Some MicroPython boards (e.g., certain ESP32 variants) use January 1, 2000
    as their Unix epoch instead of the standard January 1, 1970. On those
    boards, `time.gmtime(0)` returns year 2000 instead of 1970, and
    `time.time()` returns seconds since 2000-01-01 rather than 1970-01-01.

    `get_current_timestamp()` detects this by checking `time.gmtime(0)[0] == 2000`
    and, when true, adds the offset 946684800 to convert to standard Unix time.
    That value is the number of seconds between 1970-01-01 and 2000-01-01
    (30 years, including 7 leap years: 30 * 365.25 * 86400 = 946684800).
    """

    @patch("time.gmtime")
    @patch("time.time")
    def test_2000_epoch_offset_applied(self, mock_time, mock_gmtime):
        """When gmtime(0) returns year 2000, timestamp should be offset by 946684800."""
        mock_time.return_value = 1000000
        mock_gmtime.return_value = (2000, 1, 1, 0, 0, 0, 4, 1, 0)

        from supabase_micro.utils import get_current_timestamp

        result = get_current_timestamp()
        self.assertEqual(result, 1000000 + 946684800)

    @patch("time.gmtime")
    @patch("time.time")
    def test_normal_epoch_no_offset(self, mock_time, mock_gmtime):
        """When gmtime(0) returns year 1970, no offset should be applied."""
        mock_time.return_value = 1000000
        mock_gmtime.return_value = (1970, 1, 1, 0, 0, 0, 4, 1, 0)

        from supabase_micro.utils import get_current_timestamp

        result = get_current_timestamp()
        self.assertEqual(result, 1000000)


if __name__ == "__main__":
    unittest.main()
