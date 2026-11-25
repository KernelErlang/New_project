"""Shared fixtures: a frozen clock, a temporary Codex and a live local server."""

from __future__ import annotations

import datetime as dt
import http.client
import json
import threading
from typing import Any

import pytest

from nocturne.codex import Clock, Codex
from nocturne.server import NocturneServer, make_server
from nocturne.storage import Store

SECRET = bytes(range(32))


class FixedClock(Clock):
    """A clock that only moves when told to."""

    def __init__(self, moment: dt.datetime) -> None:
        self.moment = moment

    def now(self) -> dt.datetime:
        return self.moment

    def advance(self, **delta: float) -> None:
        self.moment += dt.timedelta(**delta)


class Client:
    """A tiny HTTP client that can forge any header (Host included)."""

    def __init__(self, server: NocturneServer) -> None:
        self.host, self.port = server.server_address[:2]
        self.token = server.token

    def request(
        self,
        method: str,
        path: str,
        body: Any = None,
        *,
        token: bool = True,
        headers: dict[str, str] | None = None,
        raw: bytes | None = None,
    ) -> tuple[int, dict[str, str], Any]:
        conn = http.client.HTTPConnection(self.host, self.port, timeout=10)
        sent = dict(headers or {})
        if token:
            sent.setdefault("X-Nocturne-Token", self.token)
        payload = raw
        if body is not None:
            payload = json.dumps(body).encode()
            sent.setdefault("Content-Type", "application/json")
        conn.request(method, path, body=payload, headers=sent)
        response = conn.getresponse()
        data = response.read()
        result_headers = {k.lower(): v for k, v in response.getheaders()}
        conn.close()
        content_type = result_headers.get("content-type", "")
        if content_type.startswith("application/json"):
            return response.status, result_headers, json.loads(data.decode())
        return response.status, result_headers, data.decode("utf-8", "replace")

    def get(self, path: str, **kw: Any):
        return self.request("GET", path, **kw)

    def post(self, path: str, body: Any = None, **kw: Any):
        return self.request("POST", path, {} if body is None else body, **kw)

    def put(self, path: str, body: Any = None, **kw: Any):
        return self.request("PUT", path, body, **kw)

    def patch(self, path: str, body: Any = None, **kw: Any):
        return self.request("PATCH", path, body, **kw)

    def delete(self, path: str, **kw: Any):
        return self.request("DELETE", path, **kw)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(dt.datetime(2026, 11, 25, 21, 30))


@pytest.fixture
def store(tmp_path):
    store = Store(tmp_path / "codex.sqlite3")
    yield store
    store.close()


@pytest.fixture
def codex(store, clock, tmp_path) -> Codex:
    store._set_meta("soul_secret", SECRET.hex())  # a fixed soul: every test run draws the same hands
    return Codex(store, clock=clock, data_dir=tmp_path)


@pytest.fixture
def server(codex):
    srv = make_server(codex, "127.0.0.1", 0)
    thread = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


@pytest.fixture
def client(server) -> Client:
    return Client(server)


def seal_tonight(codex: Codex, keep=(0, 1, 2)) -> dict:
    codex.draw()
    return codex.keep({"keep": list(keep)})


def lenient_keep(codex: Codex) -> dict:
    """Seal tonight's hand while dodging Shadow constraints that would block test notes."""
    hand = codex.draw()["drawn"]
    harsh = {"major-03", "major-05", "major-06", "major-11", "major-20", "major-21"}

    def gentle(card: dict) -> bool:
        if card["id"] in harsh and not card["reversed"]:
            return False
        return not (card["suit"] == "wands" and not card["reversed"])

    shadow = next((i for i, c in enumerate(hand) if gentle(c)), 2)
    others = [i for i in range(5) if i != shadow][:2]
    return codex.keep({"keep": [others[0], others[1], shadow]})
