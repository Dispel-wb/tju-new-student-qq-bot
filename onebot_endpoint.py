# -*- coding: utf-8 -*-
import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


AUTO_VALUES = {"", "auto", "detect", "discover"}


def normalize_ws_url(value):
    value = str(value or "").strip()
    if value.lower() in AUTO_VALUES:
        return None
    if "://" not in value:
        value = "ws://" + value
    parsed = urlsplit(value)
    if parsed.scheme not in ("ws", "wss") or not parsed.hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    if port is None or not 1 <= port <= 65535:
        return None
    host = parsed.hostname
    if host in ("0.0.0.0", "::", "[::]"):
        host = "127.0.0.1" if host == "0.0.0.0" else "::1"
    display_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    netloc = f"{display_host}:{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path or "", parsed.query, ""))


def _server_urls(value):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() == "websocketservers" and isinstance(child, list):
                for server in child:
                    if not isinstance(server, dict) or server.get("enable", server.get("enabled", True)) is False:
                        continue
                    direct = normalize_ws_url(server.get("url"))
                    if direct:
                        found.append(direct)
                        continue
                    host = str(server.get("host") or "127.0.0.1").strip()
                    port = server.get("port")
                    url_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
                    candidate = normalize_ws_url(f"ws://{url_host}:{port}") if port is not None else None
                    if candidate:
                        found.append(candidate)
            found.extend(_server_urls(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_server_urls(child))
    return found


def urls_from_config_dir(config_dir):
    directory = Path(config_dir).expanduser()
    if not directory.is_dir():
        return []
    files = sorted(
        directory.glob("onebot11_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    urls = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        urls.extend(_server_urls(payload))
    return list(dict.fromkeys(urls))


def default_config_dirs(base_dir=None):
    base = Path(base_dir or __file__).resolve()
    if base.is_file():
        base = base.parent
    candidates = []
    configured = os.environ.get("BOT_ONEBOT_CONFIG_DIR", "").strip()
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend((
        base / "protocol" / "config",
        base.parent / "protocol" / "config",
        Path.home() / "qq-smart-bot" / "protocol" / "config",
    ))
    return list(dict.fromkeys(path.resolve() for path in candidates))


def endpoint_candidates(configured_url="auto", config_dirs=None, base_dir=None):
    urls = []
    explicit = os.environ.get("BOT_WS_URL", "").strip()
    for raw in (explicit, configured_url):
        for part in str(raw or "").replace(";", ",").split(","):
            normalized = normalize_ws_url(part)
            if normalized:
                urls.append(normalized)
    directories = config_dirs if config_dirs is not None else default_config_dirs(base_dir)
    for directory in directories:
        urls.extend(urls_from_config_dir(directory))
    return list(dict.fromkeys(urls))


def endpoint_is_open(url, timeout=1.0):
    parsed = urlsplit(url)
    try:
        with socket.create_connection((parsed.hostname, parsed.port), timeout=timeout):
            return True
    except OSError:
        return False


def discover_open_endpoint(configured_url="auto", config_dirs=None, base_dir=None, timeout=1.0):
    for url in endpoint_candidates(configured_url, config_dirs, base_dir):
        if endpoint_is_open(url, timeout=timeout):
            return url
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Discover an enabled local OneBot WebSocket server.")
    parser.add_argument("--configured-url", default="auto")
    parser.add_argument("--config-dir", action="append", default=[])
    parser.add_argument("--wait", type=float, default=0.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)
    config_dirs = args.config_dir or None
    if args.list:
        for url in endpoint_candidates(args.configured_url, config_dirs, Path(__file__).resolve().parent):
            print(url)
        return 0
    deadline = time.monotonic() + max(0.0, args.wait)
    while True:
        endpoint = discover_open_endpoint(
            args.configured_url,
            config_dirs,
            Path(__file__).resolve().parent,
        )
        if endpoint:
            print(endpoint)
            return 0
        if time.monotonic() >= deadline:
            print("No enabled and reachable OneBot WebSocket server was found.", file=sys.stderr)
            return 1
        time.sleep(max(0.1, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
