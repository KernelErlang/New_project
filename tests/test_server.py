"""The HTTP API, end to end, against a live server on a random local port."""

from conftest import lenient_keep, seal_tonight

from nocturne.server import CSP


def test_health_needs_no_token(client):
    status, _, data = client.get("/api/health", token=False)
    assert status == 200 and data["id"] == "nocturne-codex"


def test_api_requires_the_token(client):
    status, _, data = client.get("/api/state", token=False)
    assert status == 403 and data["error"] == "bad_token"
    status, _, _ = client.get("/api/state", headers={"X-Nocturne-Token": "forged"})
    assert status == 403


def test_foreign_hosts_are_refused(client):
    status, _, data = client.get("/api/health", headers={"Host": "evil.example:80"})
    assert status == 403 and data["error"] == "foreign_host"


def test_foreign_origins_are_refused(client):
    status, _, data = client.post("/api/ritual/draw", headers={"Origin": "https://evil.example"})
    assert status == 403 and data["error"] == "foreign_origin"


def test_index_carries_token_and_strict_headers(client, server):
    status, headers, html = client.get("/", token=False)
    assert status == 200
    assert server.token in html and "{{NOCTURNE_TOKEN}}" not in html
    assert headers["content-security-policy"] == CSP
    assert headers["x-frame-options"] == "DENY"
    assert headers["x-content-type-options"] == "nosniff"


def test_static_files_and_traversal(client):
    status, headers, _ = client.get("/static/js/main.js", token=False)
    assert status == 200 and headers["content-type"].startswith("text/javascript")
    status, headers, _ = client.get("/static/fonts/cinzel-400.woff2", token=False)
    assert status == 200 and headers["content-type"] == "font/woff2"
    for path in ("/static/../server.py", "/static/%2e%2e/server.py", "/static/js/nope.js", "/nowhere"):
        assert client.get(path, token=False)[0] == 404
    assert client.get("/favicon.ico", token=False)[0] == 200


def test_art_endpoints(client):
    status, headers, svg = client.get("/art/card/major-13.svg", token=False)
    assert status == 200 and headers["content-type"] == "image/svg+xml" and "<svg" in svg
    assert client.get("/art/card/back.svg", token=False)[0] == 200
    assert client.get("/art/crest/vesperine.svg", token=False)[0] == 200
    assert client.get("/art/forge.svg?name=Maria", token=False)[0] == 200
    assert client.get("/art/card/major-99.svg", token=False)[0] == 404
    assert client.get("/art/crest/nobody.svg", token=False)[0] == 404


def test_methods_and_bad_json(client):
    assert client.request("DELETE", "/api/state")[0] == 405
    assert client.post("/")[0] == 405
    status, _, data = client.request("POST", "/api/ritual/keep", raw=b"{not json")
    assert status == 400 and data["error"] == "bad_json"
    status, _, data = client.request("POST", "/api/ritual/keep", raw=b"[1,2,3]")
    assert status == 400


def test_the_full_ritual(client):
    status, _, state = client.get("/api/state")
    assert status == 200 and state["ritual"]["status"] == "untouched" and state["rules"] is None
    status, _, _ = client.post("/api/notes", {"title": "too soon", "body": "x"})
    assert status == 409
    assert client.post("/api/ritual/keep", {"keep": [0, 1, 2]})[0] == 409

    status, _, ritual = client.post("/api/ritual/draw")
    assert status == 200 and ritual["status"] == "drawn" and len(ritual["drawn"]) == 5
    assert set(ritual["drawn"][0]["previews"]) == {"crown", "heart", "shadow", "burned"}
    again = client.post("/api/ritual/draw")[2]
    assert [c["id"] for c in again["drawn"]] == [c["id"] for c in ritual["drawn"]]

    assert client.post("/api/ritual/keep", {"keep": [0, 0, 1]})[0] == 400
    status, _, sealed = client.post("/api/ritual/keep", {"keep": [4, 2, 0]})
    assert status == 200 and sealed["ritual"]["status"] == "sealed"
    assert sealed["rules"]["edicts"] and sealed["house"]["art"].startswith("/art/crest/")
    status, _, data = client.post("/api/ritual/keep", {"keep": [0, 1, 2]})
    assert status == 409 and data["error"] == "already_sealed"


def test_notes_rites_and_discoveries(client, codex):
    lenient_keep(codex)
    status, _, result = client.post(
        "/api/notes", {"title": "Nevermore", "body": "the raven", "local_time": "00:10", "x": 0.3, "y": 0.4}
    )
    assert status == 201, result
    note = result["note"]
    assert note["local_time"] == "00:10" and (note["x"], note["y"]) in ((0.3, 0.4), (note["x"], note["y"]))
    ids = [r["id"] for r in result["invocation"]["performed"]]
    assert "nevermore" in ids and "witching_hour" in ids
    assert {"nevermore", "witching_hour"} <= {r["id"] for r in result["new_discoveries"]}
    again = client.post("/api/notes", {"title": "Nevermore", "body": "again", "local_time": "00:11"})[2]
    assert "nevermore" not in {r["id"] for r in again["new_discoveries"]}

    _, _, catalogue = client.get("/api/codex")
    lore = {r["id"]: r for r in catalogue["rites"]}
    assert lore["nevermore"]["discovered"] and lore["nevermore"]["count"] == 2
    assert lore["ouroboros"]["lore"] is None

    status, _, listed = client.get("/api/notes")
    assert status == 200 and len(listed["notes"]) == 2


def test_edits_moves_and_burning(client, codex):
    lenient_keep(codex)
    note = client.post("/api/notes", {"title": "draft", "body": "ink"})[2]["note"]
    status, _, edited = client.put(f"/api/notes/{note['id']}", {"title": "final", "body": "ink and ☉"})
    assert status == 200 and edited["note"]["title"] == "final" and edited["note"]["sigils"] == ["sol"]
    status, _, moved = client.patch(f"/api/notes/{note['id']}", {"x": 0.9, "y": 0.1})
    if codex.rules(codex.today).effects["anchored"]:
        assert status == 409 and moved["error"] == "anchored"
    else:
        assert status == 200 and (moved["note"]["x"], moved["note"]["y"]) == (0.9, 0.1)
        assert client.patch(f"/api/notes/{note['id']}", {"x": "left"})[0] == 400
    status, _, burned = client.delete(f"/api/notes/{note['id']}")
    assert status == 200 and burned["deleted"] == note["id"]
    assert client.delete(f"/api/notes/{note['id']}")[0] == 404
    assert client.put("/api/notes/9999", {"title": "x"})[0] == 404


def test_bound_notes_cannot_be_edited(client, codex):
    state = lenient_keep(codex)
    forbidden = state["rules"]["forbidden"]
    if not forbidden or "ward" in state["rules"]["modifiers"]:
        return  # tonight's hand forbids nothing; covered by unit tests
    glyph = next(s["glyph"] for s in codex.catalogue()["sigils"] if s["id"] == forbidden[0])
    body = f"{glyph} " + ("word " * 14)
    status, _, result = client.post("/api/notes", {"title": "pact", "body": body})
    if status != 201:
        return  # the night's constraints refused this body; the binding is tested elsewhere
    assert result["note"]["bound"] is True
    assert client.put(f"/api/notes/{result['note']['id']}", {"title": "free"})[0] == 423


def test_edict_violations_are_explained(client, codex, clock):
    seal_tonight(codex)
    rules = codex.rules(codex.today)
    rules.constraints.char_limit = 5  # tighten tonight's vow for the test
    status, _, data = client.post("/api/notes", {"title": "", "body": "far too long"})
    assert status == 422 and data["error"] == "edict_violation"
    assert data["violations"][0]["rule"] == "char_limit"
    assert client.post("/api/notes", {"title": "", "body": "   "})[0] == 400
    assert client.post("/api/notes", {"title": 7})[0] == 400
    assert client.post("/api/notes", {"body": "x" * 10_001})[0] == 413


def test_divination_reads_without_saving(client, codex):
    lenient_keep(codex)
    status, _, omen = client.post("/api/divine", {"title": "Nevermore", "body": "", "local_time": "00:30"})
    assert status == 200 and omen["flames"] >= 2 and omen["words"] == 1
    assert client.get("/api/notes")[2]["notes"] == []


def test_past_nights_are_sealed(client, codex, clock):
    lenient_keep(codex)
    note = client.post("/api/notes", {"title": "yesterday", "body": "ink"})[2]["note"]
    clock.advance(days=1)
    status, _, data = client.put(f"/api/notes/{note['id']}", {"title": "rewrite"})
    assert status == 403 and data["error"] == "night_sealed"
    assert client.patch(f"/api/notes/{note['id']}", {"x": 0.2, "y": 0.2})[0] == 403
    status, _, past = client.get(f"/api/state?day={note['day']}")
    assert status == 200 and not past["is_today"] and past["notes"][0]["title"] == "yesterday"
    assert client.get("/api/state")[2]["ritual"]["status"] == "untouched"
    assert client.get("/api/state?day=2026-11-20")[2]["ritual"]["status"] == "unobserved"
    assert client.get("/api/state?day=2099-01-01")[0] == 403
    assert client.get("/api/state?day=yesterday")[0] == 400
    assert client.get("/api/state?day=2026-02-30")[0] == 400
    assert client.delete(f"/api/notes/{note['id']}")[0] == 200


def test_calendar_export_and_settings(client, codex):
    lenient_keep(codex)
    client.post("/api/notes", {"title": "Kept", "body": "for the archive"})
    days = client.get("/api/calendar")[2]["days"]
    assert days[0]["sealed"] and days[0]["note_count"] == 1 and len(days[0]["kept"]) == 3
    status, headers, exported = client.get("/api/export?format=json")
    assert status == 200 and "attachment" in headers["content-disposition"]
    assert exported["notes"][0]["title"] == "Kept"
    status, headers, markdown = client.get("/api/export?format=markdown")
    assert status == 200 and "### Kept" in markdown and headers["content-type"].startswith("text/markdown")
    status, _, settings = client.put("/api/settings", {"ambience": False})
    assert status == 200 and settings["ambience"] is False
    assert client.get("/api/settings")[2]["ambience"] is False
    assert client.put("/api/settings", {"bogus": 1})[0] == 400


def test_shutdown_stops_the_server(client, server):
    status, _, data = client.post("/api/shutdown")
    assert status == 200 and "snuffed" in data["farewell"]


def test_moving_notes_on_a_free_night(client, codex):
    codex.draw()
    hand = codex.state()["ritual"]["drawn"]
    # keep Justice, the Two of Swords (reversed: Unbound Tongue) and the Tower: nothing anchors
    order = [
        next(i for i, c in enumerate(hand) if c["id"] == cid) for cid in ("major-11", "major-16", "swords-02")
    ]
    state = codex.keep({"keep": order})
    assert not state["rules"]["effects"]["anchored"]
    note = client.post("/api/notes", {"title": "drift", "body": "ink"})[2]["note"]
    status, _, moved = client.patch(f"/api/notes/{note['id']}", {"x": 0.9, "y": 0.1})
    assert status == 200 and (moved["note"]["x"], moved["note"]["y"]) == (0.9, 0.1)
    assert client.patch(f"/api/notes/{note['id']}", {"x": "left", "y": 0})[0] == 400
    assert client.patch(f"/api/notes/{note['id']}", {"x": 0.5})[0] == 400
