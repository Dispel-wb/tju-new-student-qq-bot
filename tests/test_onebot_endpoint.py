# -*- coding: utf-8 -*-
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_DIR / "src" if (PROJECT_DIR / "src" / "onebot_endpoint.py").exists() else PROJECT_DIR
sys.path.insert(0, str(SOURCE_DIR))

from onebot_endpoint import (
    discover_open_endpoint,
    endpoint_candidates,
    normalize_ws_url,
    urls_from_config_dir,
)


class OneBotEndpointTests(unittest.TestCase):
    def write_config(self, directory, servers):
        path = Path(directory) / "onebot11_2707817973.json"
        path.write_text(
            json.dumps({"network": {"websocketServers": servers}}),
            encoding="utf-8",
        )
        return path

    def test_enabled_servers_are_read_without_fixed_port(self):
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(directory, [
                {"enable": False, "host": "127.0.0.1", "port": 3002},
                {"enable": True, "host": "127.0.0.1", "port": 48761},
            ])
            self.assertEqual(["ws://127.0.0.1:48761"], urls_from_config_dir(directory))

    def test_wildcard_hosts_are_mapped_to_local_connect_addresses(self):
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(directory, [
                {"enable": True, "host": "0.0.0.0", "port": 45100},
                {"enable": True, "host": "::", "port": 45101},
            ])
            self.assertEqual(
                ["ws://127.0.0.1:45100", "ws://[::1]:45101"],
                urls_from_config_dir(directory),
            )

    def test_explicit_override_has_priority_but_config_remains_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            self.write_config(directory, [
                {"enable": True, "host": "127.0.0.1", "port": 45102},
            ])
            with mock.patch.dict("os.environ", {"BOT_WS_URL": "ws://localhost:45103"}, clear=False):
                self.assertEqual(
                    ["ws://localhost:45103", "ws://127.0.0.1:45102"],
                    endpoint_candidates("auto", [Path(directory)]),
                )

    def test_discovery_selects_reachable_configured_endpoint(self):
        unavailable = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(unavailable.close)
        unavailable.bind(("127.0.0.1", 0))
        unavailable_port = unavailable.getsockname()[1]
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(listener.close)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.dict("os.environ", {}, clear=True):
            self.write_config(directory, [
                {"enable": True, "host": "127.0.0.1", "port": unavailable_port},
                {"enable": True, "host": "127.0.0.1", "port": port},
            ])
            self.assertEqual(
                f"ws://127.0.0.1:{port}",
                discover_open_endpoint("auto", [Path(directory)], timeout=0.2),
            )

    def test_invalid_urls_are_rejected(self):
        self.assertIsNone(normalize_ws_url("auto"))
        self.assertIsNone(normalize_ws_url("http://127.0.0.1:3002"))
        self.assertIsNone(normalize_ws_url("ws://127.0.0.1"))


if __name__ == "__main__":
    unittest.main()
