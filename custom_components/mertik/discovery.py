"""Find Mertik WiFi modules on the local network.

The module answers a UDP broadcast on port 30718, always to port 30719, with
its name (for example "mmWiFiBoxV2") followed by its 6-byte MAC address.
"""

from __future__ import annotations

import asyncio
import socket
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

QUERY = bytes.fromhex("000100f6")
QUERY_PORT = 30718
REPLY_PORT = 30719

# The reply port can be bound only once, so one search at a time.
_LOCK = asyncio.Lock()


def parse_reply(data: bytes) -> dict[str, str] | None:
    """Return the name and MAC address in a discovery reply, or None."""
    if len(data) < 7 or b"WiFiBox" not in data[:-6]:
        return None
    return {
        "name": data[:-6].strip(b"\xff\x00").decode("ascii", "replace"),
        "mac": ":".join(f"{b:02x}" for b in data[-6:]),
    }


def discover(timeout: float = 3.0) -> list[dict[str, str]]:
    """Broadcast the query and return the modules that answer, by IP address."""
    found: dict[str, dict[str, str]] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", REPLY_PORT))
        sock.settimeout(0.3)
        deadline = time.monotonic() + timeout
        next_query = 0.0
        while (now := time.monotonic()) < deadline:
            if now >= next_query:
                sock.sendto(QUERY, ("255.255.255.255", QUERY_PORT))
                next_query = now + 1.0
            try:
                data, (host, _port) = sock.recvfrom(1024)
            except socket.timeout:
                continue
            module = parse_reply(data)
            if module is not None:
                found[host] = {"host": host, **module}
    except OSError:
        pass
    finally:
        sock.close()
    return sorted(found.values(), key=lambda module: module["host"])


async def async_discover(hass: HomeAssistant, timeout: float = 3.0) -> list[dict[str, str]]:
    """Search the network without blocking Home Assistant."""
    async with _LOCK:
        return await hass.async_add_executor_job(discover, timeout)


async def async_find_moved_host(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    """Return the new IP address of this entry's module, if it answers elsewhere.

    The module is recognised by its MAC address. Without a known MAC address a
    module is only taken when it is the only one answering and no other entry
    uses its address.
    """
    modules = await async_discover(hass)
    if entry.unique_id:
        hosts = [m["host"] for m in modules if m["mac"] == entry.unique_id]
    else:
        taken = {
            other.data.get("host")
            for other in hass.config_entries.async_entries(entry.domain)
            if other.entry_id != entry.entry_id
        }
        hosts = [m["host"] for m in modules if m["host"] not in taken]
        if len(modules) != 1:
            hosts = []
    if hosts and hosts[0] != entry.data["host"]:
        return hosts[0]
    return None
