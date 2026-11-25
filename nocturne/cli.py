"""Command line entry point: ``python -m nocturne`` (or the one-click launchers)."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

from . import APP_NAME, __version__
from .codex import Codex
from .config import DB_NAME, DEFAULT_HOST, DEFAULT_PORT, default_data_dir
from .server import make_server
from .storage import Store

BANNER = r"""
        .   *        +         .        *
    ┌─────────────────────────────────────────┐
    │   N O C T U R N E      C O D E X        │
    │   a grimoire for the hours after dusk   │
    └─────────────────────────────────────────┘
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nocturne",
        description=f"{APP_NAME}: a gothic, tarot-driven private grimoire for daily notes.",
    )
    parser.add_argument(
        "--host", default=DEFAULT_HOST, help="address to bind (default: %(default)s — this computer only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="preferred port; the next free one is used if taken (default: %(default)s)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="where the private database lives (default: your user data folder, or $NOCTURNE_HOME)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="do not open a browser window automatically"
    )
    parser.add_argument("--verbose", action="store_true", help="log every request")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    return parser


def probe(host: str, port: int, timeout: float = 0.6) -> bool:
    """True if a Nocturne Codex already answers at ``host:port``."""
    url = f"http://{host}:{port}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode()).get("id") == "nocturne-codex"
    except (OSError, ValueError):
        return False


def _print(text: str) -> None:
    try:
        print(text, flush=True)
    except UnicodeEncodeError:  # pragma: no cover - legacy Windows consoles
        print(text.encode("ascii", "replace").decode("ascii"), flush=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.port and probe(args.host, args.port):
        url = f"http://{args.host}:{args.port}/"
        _print(f"The Codex is already open at {url} — summoning it.")
        if not args.no_browser:
            webbrowser.open(url)
        return 0

    data_dir = (args.data_dir or default_data_dir()).expanduser()
    store = Store(data_dir / DB_NAME)
    codex = Codex(store, data_dir=data_dir)
    try:
        server = make_server(codex, args.host, args.port, quiet=not args.verbose)
    except OSError as exc:
        _print(f"Could not open the Codex: {exc}")
        store.close()
        return 1

    _print(BANNER)
    _print(f"  The Codex is open at  {server.url}")
    _print(f"  Your notes are kept in {data_dir}")
    _print("  Close this window (or press Ctrl+C) to snuff the candle.\n")
    if not args.no_browser:
        threading.Timer(0.4, webbrowser.open, (server.url,)).start()
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        _print("\n  The candle is snuffed. Sleep well.")
    finally:
        server.server_close()
        store.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
