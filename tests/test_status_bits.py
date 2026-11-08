"""Status parsing of the Mertik protocol class, without Home Assistant."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "custom_components", "mertik"))

from mertik import Mertik  # noqa: E402


def status_response(flame="00", bits="0000", dim="64", temp="00E6"):
    """A status response as the WiFi module sends it (ASCII hex after STX)."""
    body = "303030300003" + "00" + flame + bits + dim + "000000" + temp
    return b"\x02" + body.encode("ascii") + b"\x03"


def make(bits, flame="00"):
    sock = MagicMock()
    sock.recv.return_value = status_response(flame=flame, bits=bits)
    with patch("socket.socket", return_value=sock):
        return Mertik("192.0.2.1")


class StatusBits(unittest.TestCase):
    def test_guard_flame_with_and_without_leading_bit(self):
        # bit 8 (from the left of the 16-bit word) = 0x0080
        self.assertTrue(make("8080").is_guard_flame_on)
        self.assertTrue(make("0080").is_guard_flame_on)
        self.assertFalse(make("8000").is_guard_flame_on)

    def test_igniting(self):
        self.assertTrue(make("8010").is_igniting)
        self.assertTrue(make("0010").is_igniting)
        self.assertFalse(make("8000").is_igniting)

    def test_shutting_down(self):
        self.assertTrue(make("8100").is_shutting_down)
        self.assertTrue(make("0100").is_shutting_down)
        self.assertFalse(make("8080").is_shutting_down)

    def test_aux_and_light_unchanged_when_leading_bit_set(self):
        dev = make("800C")
        self.assertTrue(dev.is_aux_on)
        self.assertTrue(dev.is_light_on)

    def test_flame_height_and_temperature(self):
        dev = make("8080", flame="C0")
        self.assertTrue(dev.is_on)
        self.assertEqual(dev.get_flame_height(), 7)
        self.assertEqual(dev.ambient_temperature, 23.0)

    def test_guard_flame_out_means_off_even_with_flame_ff(self):
        # Real status of a cold fireplace with the pilot out (8 Nov 2026):
        # flame byte FF, status word 820A (guard flame bit 0, aux bit 1).
        dev = make("820A", flame="FF")
        self.assertFalse(dev.is_on)
        self.assertEqual(dev.get_flame_height(), 0)
        self.assertFalse(dev.is_guard_flame_on)

    def test_burning_at_max_is_height_12(self):
        dev = make("8080", flame="FF")
        self.assertTrue(dev.is_on)
        self.assertEqual(dev.get_flame_height(), 12)

    def test_igniting_counts_as_on_before_the_guard_flame_is_seen(self):
        dev = make("8010", flame="FF")
        self.assertTrue(dev.is_on)

    def test_defaults_before_a_status_arrives(self):
        sock = MagicMock()
        sock.recv.return_value = b"\x02unexpected\x03"
        with patch("socket.socket", return_value=sock):
            dev = Mertik("192.0.2.1")
        self.assertFalse(dev.is_on)
        self.assertFalse(dev.is_guard_flame_on)
        self.assertIsNone(dev.ambient_temperature)


if __name__ == "__main__":
    unittest.main()
