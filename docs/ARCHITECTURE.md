# Architecture

The Nocturne Codex is a local-first web app: a **standard-library Python server** (no
dependencies) and a **vanilla JavaScript front end** (ES modules, no build step). Python is the
single source of truth for the rules and the hidden formulas; the browser draws, animates and
sings.

```text
 browser (static/)                                   python (nocturne/)
┌──────────────────────────────┐   JSON + token   ┌────────────────────────────────────────┐
│ main.js   conductor           │ ───────────────▶ │ server.py   routing, token, Host/Origin │
│ ritual.js draw/keep/burn      │                  │             checks, CSP, static & art   │
│ board.js  parchment board     │ ◀─────────────── │ codex.py    application logic            │
│ quill.js  composer, omen      │                  │   ├─ ritual.py   draw five, keep three   │
│ tome.js   codex, archive …    │   /art/*.svg     │   ├─ edicts.py   cards → rules           │
│ fx.js     30 animations       │ ◀─────────────── │   ├─ arcane.py   formulas → rites        │
│ audio.js  39 synthesised sounds│                 │   ├─ heraldry.py, cardart.py, glyphs.py │
│ theme.js  palette & effects   │                  │   └─ storage.py  SQLite                  │
└──────────────────────────────┘                   └────────────────────────────────────────┘
```

## Modules

| Module | Responsibility |
|---|---|
| `rng.py` | `FateStream`: SHA-256 counter-mode randomness with rejection sampling and Fisher–Yates. Fully specified, so draws are identical on every platform and Python version. `derive_seed` uses HMAC-SHA256. |
| `tarot.py` | The 78 cards: names, numerals, elements, ruling sigils, keywords, epigraphs, arcana. |
| `sigils.py` | The 24 sigils, extraction from text (shortcodes, variation selectors), groups by element and polarity. |
| `numerology.py` | Letter weights (gematria), digital roots with master numbers, primes, palindromes, word splitting. |
| `ritual.py` | `draw_for_day(secret, date)`, keep validation, the `Spread` (kept and burned cards by position). |
| `edicts.py` | The rules engine. `compute_rules(secret, spread)` builds a `DayRules` (aspect, tonality, resonance, awakened/banished/forbidden sigils, constraints, effect flags, formula modifiers, readable edicts, House, omen). `preview(card)` shows what a card would do in each position. `check_constraints(...)` validates a note. |
| `arcane.py` | The 29 rites and `invoke(note, rules)`: reads a note, applies consequences (chains, ward, ashes), evaluates the formulas grandest-first, caps at three, and marks awakened performances. |
| `heraldry.py` | The 12 Houses, the crest renderer (5 shields × 17 divisions × 24 charges × 6 supporters × toppers) and `forge(name)`. |
| `cardart.py`, `glyphs.py` | Procedural SVG card faces (gothic arch windows, pips, court marks, unique Major compositions), the rose-window card back, and the emblem library shared with heraldry. |
| `storage.py` | SQLite: `meta` (soul secret, settings, schema version), `rituals`, `notes`, `discoveries`. Thread-safe via a lock; a single file. |
| `codex.py` | `Codex`: the application logic behind every endpoint, with an injectable `Clock` for tests. Errors are `CodexError(status, code, message)`. |
| `server.py` | `ThreadingHTTPServer` with security headers, routing and art endpoints. `make_server` tries successive ports. |
| `cli.py` | Argument parsing, data folder, reusing a running instance (`/api/health` probe), banner, opening the browser. |

## Determinism

* **The hand**: `HMAC(secret, "nocturne/draw" ‖ date)` seeds the stream; the deck is shuffled
  and the first five dealt, each with a ⅓ chance of reversal.
* **Random edicts** (*Sleight of Hand*, *The Pact*): `HMAC(secret, "nocturne/edicts" ‖ date)`.
* **Echoes and note placement** have their own derived seeds.
* The drawn hand is **stored** with the ritual, so history survives future changes to the deck.

## HTTP API

Every `/api/*` route except `/api/health` requires the header `X-Nocturne-Token: <token>`.
The token is minted at launch and embedded in the page as `<meta name="nocturne-token">`.
Responses are JSON. Errors look like `{"error": "<code>", "message": "…"}`.

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/api/health` | — | `{app, id, version}` (no token needed) |
| GET | `/api/state?day=YYYY-MM-DD` | — | Everything for a night: ritual, rules, house, notes, echo, settings, discoveries |
| POST | `/api/ritual/draw` | `{}` | Today's five cards with per-position previews (idempotent) |
| POST | `/api/ritual/keep` | `{keep: [crown, heart, shadow]}` | The new state (409 if already sealed) |
| GET | `/api/notes?day=` | — | `{day, notes}` |
| POST | `/api/notes` | `{title, body, local_time?, velocity?, x?, y?}` | `{note, invocation, new_discoveries}` (201) |
| PUT | `/api/notes/{id}` | `{title, body, local_time?, velocity?}` | Same as POST (423 if bound, 403 if the night is sealed) |
| PATCH | `/api/notes/{id}` | `{x, y}` (0–1) | `{note}` (409 on anchored nights) |
| DELETE | `/api/notes/{id}` | — | `{deleted, moths}` |
| POST | `/api/divine` | `{title, body, …}` | `{flames, sigils, bound, violations, words}` (reads without saving) |
| GET | `/api/codex` | — | Sigils, deck, houses, rites (hints; lore only once discovered), positions |
| GET | `/api/calendar` | — | Every observed night |
| GET | `/api/export?format=json\|markdown` | — | A download |
| GET/PUT | `/api/settings` | partial settings | Settings (validated and clamped) |
| POST | `/api/shutdown` | `{}` | Stops the server |

Art (no token, cacheable): `/art/card/{id}.svg`, `/art/card/back.svg`,
`/art/crest/{house}.svg`, `/art/forge.svg?name=…`.

Error codes include `bad_token`, `foreign_host`, `foreign_origin`, `ritual_required`,
`not_drawn`, `already_sealed`, `bad_keep`, `edict_violation` (with `violations`),
`night_sealed`, `bound`, `anchored`, `future_veiled`, `bad_day`, `bad_json`, `too_long` and
`too_large`.

## Security model

* Binds to `127.0.0.1` by default.
* The `Host` header must be the server's own loopback address (defeats DNS rebinding).
* Token on every API call (other sites cannot read the page, so they cannot learn it), plus
  an `Origin` check.
* The request body is read in full before any refusal, so a refused request cannot poison a
  kept-alive connection. Bodies are capped at 64 KiB.
* Static files are served only from inside `static/` (path traversal is refused).
* CSP: `default-src 'self'`; no inline scripts, no external origins; plus `X-Frame-Options:
  DENY`, `nosniff`, `no-referrer` and COOP.
* Notes are inserted into the page only after HTML escaping (`ink.js` → `renderInk`).

## Front end

* `main.js` boots, holds state and wires every module.
* `theme.js` turns `rules.aspect.palette` into CSS custom properties and `rules.effects` into
  `fx-*` body classes. Most edicts are pure CSS.
* `fx.js` keeps two canvases (the ambient sky behind, rites in front) and an SVG/HTML overlay
  layer. The particle kinds are ember, ash, petal, mote, star, feather, droplet, spore, moth,
  spark, ring, shooting star, smoke and streak.
* `audio.js` is the Choir: oscillators, filtered noise, additive inharmonic bells and a
  generated convolution reverb, tuned to `rules.tonality` (root and mode).
* `test_frontend.py` keeps the halves honest: every rite's animation and sound exist, the effect
  flags match, every sigil glyph is covered by the bundled font, imports resolve, and no
  external URL appears anywhere in the page.

## Extending

* **A new rite**: add a `Rite` to `arcane.RITES` and its check in `_check`, then an animation in
  `fx.js` (`ANIMATIONS`) and a sound in `audio.js` (`SOUNDS`). The parity tests will remind you.
* **A new edict effect**: add the flag to `edicts.EFFECT_FLAGS` and to `theme.js`, then style
  `.fx-<flag>` in the CSS.
* **A new House**: append to `heraldry.HOUSES`. Every charge must exist in `glyphs.EMBLEMS`.
