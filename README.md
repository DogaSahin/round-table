# Round Table

A web app for worldbuilding and running tabletop RPG games — a wiki for your world, an NPC and
faction tracker, a combat/initiative tracker, and a battle-map with fog-of-war, built as a modular
FastAPI + Vue application.

> **Status: single-tenant, actively being rebuilt onto a hosted architecture.** Today the app is a
> single shared campaign with no accounts, logins, or multi-game isolation — that's the next epic
> (`identity`/`games`/`authz`). Every module below is DM-facing only for now: combat and maps both
> expose read-only, filtered "player view" API endpoints and their own WebSocket topics on the
> backend, but no player-facing frontend consumes them yet.

## Features

- **Dice** — roll arbitrary dice expressions, with a saved-roll shortlist and roll history.
- **Sessions** — a session log/dashboard: create sessions, log entries, mark them resolved, and
  generate a session recap.
- **Factions** — track factions with progress clocks and an activity feed.
- **NPCs** — a roster of NPCs with disposition tracking.
- **Wiki** — Markdown wiki pages with `[[wikilink]]`-style backlinks and tags.
- **Combat** — an initiative tracker: encounters, combatants, HP/AC, conditions, concentration,
  and live sync to any open tab over WebSockets.
- **Maps** — a battle-map editor: grid settings (size, offset, four movement/distance rules),
  draggable tokens with HP/status markers, manual fog-of-war (reveal/hide, reveal-all/hide-all),
  map/token image uploads, and live sync over WebSockets.

## Tech stack

- **Backend:** FastAPI (JSON API) on Python 3.12+, SQLAlchemy 2.x, Alembic migrations, SQLite.
- **Frontend:** Vue 3 (Composition API) + Vite + TypeScript, [Konva.js](https://konvajs.org/) for
  the map canvas.
- **Real-time:** native WebSockets — a small in-process topic-based pub/sub hub in
  `backend/app/core/realtime/`.

The codebase is a package-by-feature modular monolith with a service layer over a pure,
system-agnostic rules core (`engine/`): feature modules never import each other directly, shared
logic pushes down into `engine/`/`content/`/`generation/`, and cross-cutting concerns (auth, DB,
realtime) live in `core/`.

## Running it in dev

**Backend** (from `backend/`):

```bash
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"    # .venv/bin/pip on macOS/Linux
cp .env.example .env                     # optional — sane defaults work without it
.venv/Scripts/alembic upgrade head       # creates backend/data/roundtable.db
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

**Frontend** (from `frontend/`, in a separate terminal):

```bash
npm install
npm run dev    # Vite dev server, proxies /api, /media, and /ws to localhost:8000
```

Open the Vite dev server's printed URL — the app is a single DM-facing view with a nav link per
module (Dice, Sessions, Factions, NPCs, Wiki, Combat, Maps).

## Gate

Before committing, both sides should pass:

```bash
# frontend/
npm run lint && npm run format:check && npm run build && npm run test

# backend/
.venv/Scripts/ruff check . && .venv/Scripts/ruff format --check . && .venv/Scripts/mypy app && .venv/Scripts/pytest
```

CI (`.github/workflows/ci.yml`) runs the same two gates on every push and pull request to `main` and
`dev`.

## License

[MIT](LICENSE)
