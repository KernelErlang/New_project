"""A small, private HTTP server for the Codex (standard library only).

Security model — the Codex is a *local* app:

* it binds to ``127.0.0.1`` by default, so other machines cannot reach it;
* the ``Host`` header must name the loopback address, which defeats DNS-rebinding;
* every ``/api`` call (except the health probe) must carry a random per-launch token
  that is only embedded in the page served to the browser, so other web pages cannot
  read or write your notes even though they run on the same machine;
* a strict Content-Security-Policy forbids any external script, style, font or request.
"""

from __future__ import annotations

import hmac
import json
import mimetypes
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlsplit

from . import APP_NAME, __version__
from .codex import Codex, CodexError
from .config import STATIC_DIR

MAX_BODY_BYTES = 64 * 1024
TOKEN_HEADER = "X-Nocturne-Token"
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; media-src 'self' blob:; "
    "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".json": "application/json",
    ".txt": "text/plain; charset=utf-8",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

Route = tuple[str, "re.Pattern[str]", str]


def _route(method: str, pattern: str, name: str) -> Route:
    return method, re.compile(f"^{pattern}$"), name


ROUTES: tuple[Route, ...] = (
    _route("GET", r"/api/health", "health"),
    _route("GET", r"/api/state", "state"),
    _route("POST", r"/api/ritual/draw", "draw"),
    _route("POST", r"/api/ritual/keep", "keep"),
    _route("GET", r"/api/notes", "list_notes"),
    _route("POST", r"/api/notes", "create_note"),
    _route("PUT", r"/api/notes/(?P<id>\d+)", "update_note"),
    _route("PATCH", r"/api/notes/(?P<id>\d+)", "move_note"),
    _route("DELETE", r"/api/notes/(?P<id>\d+)", "delete_note"),
    _route("POST", r"/api/divine", "divine"),
    _route("GET", r"/api/codex", "catalogue"),
    _route("GET", r"/api/calendar", "calendar"),
    _route("GET", r"/api/export", "export"),
    _route("GET", r"/api/settings", "get_settings"),
    _route("PUT", r"/api/settings", "put_settings"),
    _route("POST", r"/api/shutdown", "shutdown"),
)


class NocturneServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(
        self,
        address: tuple[str, int],
        codex: Codex,
        token: str | None = None,
        static_dir: Path = STATIC_DIR,
        quiet: bool = True,
    ) -> None:
        super().__init__(address, NocturneHandler)
        self.codex = codex
        self.token = token or secrets.token_urlsafe(32)
        self.static_dir = static_dir.resolve()
        self.quiet = quiet
        host, port = self.server_address[:2]
        names = {"127.0.0.1", "localhost", "[::1]", str(host)}
        self.allowed_hosts = {f"{name}:{port}" for name in names} | (names if port == 80 else set())

    @property
    def url(self) -> str:
        host, port = self.server_address[:2]
        if host in ("0.0.0.0", "::", ""):
            host = "127.0.0.1"
        return f"http://{host}:{port}/"


class NocturneHandler(BaseHTTPRequestHandler):
    server: NocturneServer
    server_version = f"NocturneCodex/{__version__}"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    # -- logging -----------------------------------------------------------
    def log_message(self, format: str, *args: Any) -> None:
        if not self.server.quiet:
            super().log_message(format, *args)

    # -- verbs ---------------------------------------------------------------
    def do_GET(self) -> None:
        self._handle("GET")

    def do_HEAD(self) -> None:
        self._handle("GET", head=True)

    def do_POST(self) -> None:
        self._handle("POST")

    def do_PUT(self) -> None:
        self._handle("PUT")

    def do_PATCH(self) -> None:
        self._handle("PATCH")

    def do_DELETE(self) -> None:
        self._handle("DELETE")

    # -- dispatch ------------------------------------------------------------
    def _handle(self, method: str, head: bool = False) -> None:
        self._head = head
        self._raw = b""
        try:
            self._read_body()
            if self.headers.get("Host", "") not in self.server.allowed_hosts:
                raise CodexError(403, "foreign_host", "This Codex answers only to its own house.")
            parts = urlsplit(self.path)
            path = unquote(parts.path)
            query = {k: v[-1] for k, v in parse_qs(parts.query).items()}
            if path.startswith("/api/"):
                self._api(method, path, query)
            elif method != "GET":
                raise CodexError(405, "method_not_allowed", "Only reading is allowed here.")
            elif path in ("/", "/index.html"):
                self._index()
            elif path == "/favicon.ico":
                self._static("img/favicon.svg")
            elif path.startswith("/static/"):
                self._static(path[len("/static/") :])
            elif path.startswith("/art/"):
                self._art(path[len("/art/") :], query)
            else:
                raise CodexError(404, "not_found", "Nothing is written here.")
        except CodexError as exc:
            self._json(exc.to_dict(), exc.status)
        except Exception as exc:  # pragma: no cover - last line of defence
            self.log_error("unhandled error: %r", exc)
            self._json({"error": "internal", "message": "The candle guttered. Try again."}, 500)

    def _api(self, method: str, path: str, query: dict[str, str]) -> None:
        for route_method, pattern, name in ROUTES:
            match = pattern.match(path)
            if not match:
                continue
            if route_method != method:
                continue
            if name != "health":
                self._authorise()
            handler: Callable[..., None] = getattr(self, f"api_{name}")
            handler(query=query, **match.groupdict())
            return
        if any(pattern.match(path) for _, pattern, _ in ROUTES):
            raise CodexError(405, "method_not_allowed", "That rite is not performed this way.")
        raise CodexError(404, "not_found", "No such passage in the Codex.")

    def _authorise(self) -> None:
        supplied = self.headers.get(TOKEN_HEADER, "")
        if not hmac.compare_digest(supplied.encode(), self.server.token.encode()):
            raise CodexError(403, "bad_token", "The seal on this request is broken.")
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc not in self.server.allowed_hosts:
            raise CodexError(403, "foreign_origin", "Strangers may not write in this Codex.")

    def _read_body(self) -> None:
        """Read the whole body up front so a refused request never poisons the connection."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError as exc:
            self.close_connection = True
            raise CodexError(400, "bad_length", "The request's length is illegible.") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            self.close_connection = True
            raise CodexError(413, "too_large", "That scroll is far too long.")
        self._raw = self.rfile.read(length) if length else b""

    def _payload(self) -> dict:
        try:
            data = json.loads(self._raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CodexError(400, "bad_json", "The request is not legible JSON.") from exc
        if not isinstance(data, dict):
            raise CodexError(400, "bad_json", "The request must be a JSON object.")
        return data

    # -- responses -------------------------------------------------------------
    def _send(
        self,
        status: int,
        body: bytes,
        content_type: str,
        extra: dict[str, str] | None = None,
        cache: str = "no-store",
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Content-Security-Policy", CSP)
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if not getattr(self, "_head", False):
            self.wfile.write(body)

    def _json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _index(self) -> None:
        html = (self.server.static_dir / "index.html").read_text(encoding="utf-8")
        html = html.replace("{{NOCTURNE_TOKEN}}", self.server.token)
        html = html.replace("{{NOCTURNE_VERSION}}", __version__)
        self._send(200, html.encode("utf-8"), CONTENT_TYPES[".html"])

    def _static(self, relative: str) -> None:
        root = self.server.static_dir
        target = (root / relative).resolve()
        if root not in target.parents or not target.is_file():
            raise CodexError(404, "not_found", "No such relic.")
        suffix = target.suffix.lower()
        content_type = CONTENT_TYPES.get(suffix) or (
            mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        )
        cache = "max-age=604800, immutable" if suffix in (".woff2", ".png") else "no-cache"
        self._send(200, target.read_bytes(), content_type, cache=cache)

    def _art(self, relative: str, query: dict[str, str]) -> None:
        codex = self.server.codex
        match = re.match(r"^card/([a-z]+(?:-\d{2})?)\.svg$", relative)
        if match:
            svg = codex.card_art(match.group(1))
        elif (match := re.match(r"^crest/([a-z-]+)\.svg$", relative)) is not None:
            svg = codex.crest_art(match.group(1))
        elif relative == "forge.svg":
            svg = codex.forged_art(query.get("name", ""))
        else:
            raise CodexError(404, "not_found", "No such art.")
        self._send(200, svg.encode("utf-8"), CONTENT_TYPES[".svg"], cache="max-age=86400")

    # -- api endpoints -----------------------------------------------------------
    def api_health(self, query: dict[str, str]) -> None:
        self._json({"app": APP_NAME, "id": "nocturne-codex", "version": __version__})

    def api_state(self, query: dict[str, str]) -> None:
        self._json(self.server.codex.state(query.get("day")))

    def api_draw(self, query: dict[str, str]) -> None:
        self._payload()
        self._json(self.server.codex.draw())

    def api_keep(self, query: dict[str, str]) -> None:
        self._json(self.server.codex.keep(self._payload()))

    def api_list_notes(self, query: dict[str, str]) -> None:
        state = self.server.codex.state(query.get("day"))
        self._json({"day": state["day"], "notes": state["notes"]})

    def api_create_note(self, query: dict[str, str]) -> None:
        self._json(self.server.codex.create_note(self._payload()), 201)

    def api_update_note(self, query: dict[str, str], id: str) -> None:
        self._json(self.server.codex.update_note(int(id), self._payload()))

    def api_move_note(self, query: dict[str, str], id: str) -> None:
        self._json(self.server.codex.move_note(int(id), self._payload()))

    def api_delete_note(self, query: dict[str, str], id: str) -> None:
        self._json(self.server.codex.delete_note(int(id)))

    def api_divine(self, query: dict[str, str]) -> None:
        self._json(self.server.codex.divine(self._payload()))

    def api_catalogue(self, query: dict[str, str]) -> None:
        self._json(self.server.codex.catalogue())

    def api_calendar(self, query: dict[str, str]) -> None:
        self._json(self.server.codex.calendar())

    def api_export(self, query: dict[str, str]) -> None:
        codex = self.server.codex
        stamp = codex.today.isoformat()
        if query.get("format") == "markdown":
            body = codex.export_markdown().encode("utf-8")
            self._send(
                200,
                body,
                "text/markdown; charset=utf-8",
                {"Content-Disposition": f'attachment; filename="nocturne-codex-{stamp}.md"'},
            )
            return
        body = json.dumps(codex.export_json(), ensure_ascii=False, indent=2).encode("utf-8")
        self._send(
            200,
            body,
            "application/json; charset=utf-8",
            {"Content-Disposition": f'attachment; filename="nocturne-codex-{stamp}.json"'},
        )

    def api_get_settings(self, query: dict[str, str]) -> None:
        self._json(self.server.codex.settings())

    def api_put_settings(self, query: dict[str, str]) -> None:
        self._json(self.server.codex.update_settings(self._payload()))

    def api_shutdown(self, query: dict[str, str]) -> None:
        self._json({"farewell": "The candle is snuffed. Sleep well."})
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def make_server(codex: Codex, host: str, port: int, attempts: int = 20, quiet: bool = True) -> NocturneServer:
    """Bind the server, trying successive ports when the preferred one is taken."""
    last_error: OSError | None = None
    for offset in range(max(1, attempts)):
        candidate = 0 if port == 0 else port + offset
        try:
            return NocturneServer((host, candidate), codex, quiet=quiet)
        except OSError as exc:
            last_error = exc
            if port == 0:
                break
    raise OSError(f"No free port near {port}: {last_error}")


__all__ = ["NocturneServer", "make_server"]
