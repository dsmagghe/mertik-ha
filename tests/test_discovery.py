"""Parsing of the discovery reply, without Home Assistant."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "mertik"))

from discovery import parse_reply  # noqa: E402

# Reply of a real module (8 Nov 2026), MAC 00:23:3c:00:44:2d.
REAL_REPLY = bytes.fromhex("ffffffffffffffffffffffffff6d6d57694669426f78563200233c00442d")


class DiscoveryReply(unittest.TestCase):
    def test_real_reply(self):
        self.assertEqual(
            parse_reply(REAL_REPLY), {"name": "mmWiFiBoxV2", "mac": "00:23:3c:00:44:2d"}
        )

    def test_other_devices_are_ignored(self):
        self.assertIsNone(parse_reply(b"\xff" * 30))
        self.assertIsNone(parse_reply(b"hello"))


if __name__ == "__main__":
    unittest.main()
