# Hexforge — Architecture (north star)

Source of truth for how the codebase is organized and why. The feature spec and the
repo-reorg prompt both defer to this document.

## 1. What Hexforge is
A **hosted, multi-tenant, open-source** web service for worldbuilding and running tabletop
RPG games in **live, real-time sessions**. Users register, create games, and invite players.
A single account can be the **DM of one game and a player in another**. Everyone sees only
the games they belong to — except the open reference content (SRD), which anyone can read
to build their own world.

- **Backend:** FastAPI **JSON API**, Python 3.12+, SQLAlchemy 2.x, Alembic.
- **Frontend:** Vue 3 SPA (Vite), served as static assets by the API (or a sibling static host).
- **Data:** SQLite by default (WAL mode; zero-config for self-hosters); **model portably** so Postgres is a config change, not a rewrite.
- **Real-time first.** Play is synchronous — multiple authenticated participants share live state (initiative, map, fog, dice) over websockets; presence and role-filtered broadcast are core, not add-ons (see §7).
- **AI is optional & assistive.** A helper that generates NPCs/lore and answers rules questions (RAG) — never required to run the app, never autonomous. The LLM provider is pluggable and can be turned off entirely.
- **Open source & self-hostable.** Others run their own instance: minimal required infra, config over code, no mandatory external services (see §8).
- **No desktop app.** No pywebview, no PyInstaller, no offline mode, no local-file assumption. (Superseded.)

## 2. Architectural style
Package-by-feature **modular monolith** with a **service layer**, sitting on top of a
**pure, system-agnostic domain core**. Deliberately *not* full Clean Architecture: no
separate domain-entity layer, no repository interfaces, no ORM↔domain mappers. The one
piece of ceremony we keep is the service boundary, because it's what makes logic testable
and lets many consumers (SPA, public API, agents) share one brain.

## 3. Layers & dependency direction
Dependencies point **inward**: the pure core is stable and depended upon; the volatile
edges (HTTP, LLM, external clients) depend on it, never the reverse.

```
                 outer / volatile  (adapters — HTTP, agents, external)
   api/v1  ·  modules/*/routes  ·  ai/tools
                        │  depends inward
   modules/*  (features: own campaign-scoped persistence + orchestration)
                        │
   generation/  (composes engine + content, calls the LLM *port*)
                        │
   content/     (open SRD reference domain; read-mostly; feeds RAG + public API)
                        │
   engine/ + rulesets/  (PURE system-agnostic rules — no I/O, no FastAPI, no DB, no LLM)
                 inner / stable

   cross-cutting (used by many, depend on nothing feature-specific):
     core/   identity/   games/   authz/   shared/   ai/(impl of the LLM port)
```

**Two hard rules that keep the core reusable:**
1. **The core does no I/O.** `engine`, `content`, `generation` never open a DB connection, make an HTTP request, or call the LLM directly. Data comes in as arguments, results go out as values.
2. **External volatility hides behind ports.** Persistence lives in the module/domain *services*; the LLM lives behind an interface in `ai/` that `generation` depends on (so self-hosted Qwen can be swapped without touching generators). This is hexagonal/ports-and-adapters applied *only* where it pays off.

Plus the module boundary itself: **`service.py` never imports FastAPI; `routes.py` never
runs ORM/DB queries** (validate with `schemas` → call `service` → return `schemas`).

## 4. Package responsibilities
- **`core/`** — framework plumbing only: config, database/engine/session, module registry, security primitives (hashing, tokens), and the **real-time hub** (`core/realtime/`: connection manager, presence, auth-on-connect, role-filtered broadcast — see §7). No business logic.
- **`engine/` + `rulesets/`** — system-agnostic rules: dice resolution, grid distance, encounter/CR math, progress clocks. `engine/rules/` defines the abstract ruleset interface; `rulesets/dnd5e/` implements it as data/plugin. 5e now, other systems later.
- **`content/`** — the **open** reference domain (SRD monsters/spells/items/rules): ingestion pipeline + query service. Campaign-independent, globally readable. Feeds RAG and the public API.
- **`generation/`** — generators (names, statblocks, NPCs, settlements, world). Compose `engine` + `content` (+ the LLM port). Logic only, no persistence — callers persist.
- **`ai/`** — assistive LLM infrastructure (**optional**): the LLM client **behind a provider port** (self-hosted Qwen, Ollama, a hosted API, or disabled), a RAG pipeline over `content`, prompt orchestration, and generation/retrieval helpers surfaced to the DM. Scope is bounded to **helper** actions — generate and answer — never autonomous mutation of game state. Every AI feature degrades gracefully when the provider is off.
- **`identity/`** — accounts & auth: `User`, registration/login, sessions/tokens.
- **`games/`** — the multi-tenant spine: `Game`, `Membership` (carries the role), `Invite`.
- **`authz/`** — cross-cutting access policy: one place that answers *"can this user do X in game Y?"*, exposed as FastAPI dependencies and service-level guards.
- **`modules/`** — feature modules (combat, maps, npcs, factions, wiki, sessions, dice), each the four-file shape (`models` / `schemas` / `service` / `routes`), owning its **campaign-scoped** data.
- **`api/v1/`** — the **public, versioned** API surface: thin, curated adapters over services, decoupled from internal module routers so internal refactors don't break external consumers.
- **`shared/`** — cross-cutting types, errors, pagination, base classes.

## 5. Sharing across modules
Feature modules **must never import each other** — a `modules/wiki` that imports
`modules/npcs` welds them together, invites circular imports, and destroys the
drop-in-a-folder property. Everything a module needs from "elsewhere" resolves through one of
four patterns, all of which keep dependencies pointing **inward** or **sideways** into shared
layers — never peer-to-peer.

1. **Shared logic → push it down.** If two features need the same capability (name generation, dice, distance, statblock building), it isn't a feature — it's shared domain. Move it into `engine/`, `content/`, or `generation/` and let every consumer import *downward*. (This is why `dice` and `distance` live in `engine/`, not in a module.) Rule: *if two features need it, it wasn't a feature.*
2. **Reading another module's data → a narrow read interface, or compose in the caller.** When B needs A's data (wiki shows mentioned NPCs; combat pulls an NPC statblock), B does **not** import A's service. Either A exposes a small, stable query/provider surface that B depends on, or — preferably — the composition happens one level up (an orchestration service or a route that calls both services and stitches results), so neither peer knows the other exists.
3. **Reacting to another module's events → an event bus.** When A must react to something in B without knowing B exists ("on `session.logged`, append to a faction's activity feed"), B publishes an event to a small bus in `core/` and A subscribes. Decoupled: either side can change or vanish, and new listeners add without editing the publisher. Introduce this only when the first cross-feature side-effect appears — don't pre-build it.
4. **Cross-cutting plumbing → it lives in the core.** Auth, current user/campaign, DB session, the realtime hub, pagination, errors are not "shared between features" — they live in `core/` / `authz/` / `shared/` and everyone depends on them. Expected.

**Rule of thumb:** share by pushing common things **down** (engine/content/generation) or
**sideways** (core/shared), or **compose in the caller** — never by reaching across to a
sibling. If a need can't be expressed as one of these four, the module boundaries are
probably drawn wrong; redraw them rather than adding a cross-import.

**Enforcement:** an `import-linter` contract in `backend-ci` forbids `modules.* → modules.*`
imports (and `modules.*.service → fastapi`). This matters most with AI agents contributing
code — they reach for the direct import unless the boundary is enforced, not just documented.

## 6. Multi-tenancy & access model
- **`User` 1—* `Membership` *—1 `Game`.** Role lives on the **membership**, not the user: `Membership.role ∈ {dm, player}`. One account, many memberships, different roles per game.
- **`Invite`** = a stored record with an opaque, expiring token + target game + granted role. Joining consumes the invite and creates a membership. Invite links are unguessable tokens, not sequential IDs.
- **Every campaign-scoped resource belongs to a game** (campaign → game). Reads and writes pass through the `authz` gate: membership exists + role permits the action. Centralized so no single endpoint can forget the check and leak another table's secrets.
- **`content/` is global-read** — not game-scoped. That's the "anyone can build their own world" surface.

## 7. Real-time sessions
Play is synchronous, so real-time sync is a core subsystem, not a feature bolt-on. The hub
lives in `core/realtime/` and is used by any module with live state (combat, maps, dice).

- **Channels are game-scoped** (`game:{id}`). A socket must **authenticate on connect** and prove a membership in that game; the connection's **role filters its payloads** (players never receive DM-only map layers, secret tokens, or hidden HP). Real-time therefore depends on `identity`, `games`, and `authz`.
- **Presence** — who is currently at the table — is tracked per channel.
- **Server-authoritative state.** The DM is authoritative; players emit a bounded set of actions (roll dice, move their own token). Last-write-wins is fine for a single table — no CRDT/OT complexity needed.
- **Scaling seam.** The hub is an in-memory connection manager **behind an interface** — fine for one self-hosted process. If an instance ever scales horizontally, a pub/sub backplane (e.g. Redis) slots in behind that interface. Don't build it now; keep the seam.

## 8. Self-hosting & open-source constraints
Being open-source and self-hostable is a design constraint, not just a distribution choice:

- **Minimal required infra.** A default install needs only Python + SQLite. Postgres, a Redis backplane, and an LLM provider are all **optional** and config-selected. The app must be fully usable with AI disabled.
- **Config over code.** All deployment choices (DB URL, LLM provider/endpoint, secrets) come from environment/config, never hard-coded. Ship an `.env.example` and clear docs.
- **Robust migrations.** Self-hosters upgrade between versions; Alembic migrations must apply cleanly forward. Never edit a released migration.
- **Versioned public API.** `api/v1` is a stability contract for external integrators and self-hosters — internal refactors must not break it.
- **Licensing.** Choose an OSS license for the project. Ship only properly-licensed reference content — the D&D 5e SRD is available under the OGL / Creative Commons; keep licensed content in `content/` **separable and attributed**, and never bundle non-SRD material.

## 9. Target folder structure (backend)
```
backend/app/
├─ main.py                 # create_app(): builds core, mounts api + module routers
├─ core/        config.py  database.py  registry.py  security.py  websocket.py
├─ engine/      dice.py  distance.py  encounter.py  clocks.py  rules/
├─ rulesets/    dnd5e/
├─ content/     models.py  schemas.py  service.py  ingest.py
├─ generation/  names.py  statblocks.py  npc.py  settlement.py  world.py
├─ ai/          client.py  rag.py  prompts.py  tools.py
├─ identity/    models.py  schemas.py  service.py  routes.py
├─ games/       models.py  schemas.py  service.py  routes.py   # Game, Membership, Invite
├─ authz/       policy.py  deps.py
├─ modules/     combat/ maps/ npcs/ factions/ wiki/ sessions/ dice/
│                 └─ (each: models.py schemas.py service.py routes.py __init__.py)
├─ api/         v1/
└─ shared/      errors.py  pagination.py  types.py
```
Growth rule: a layer is **files inside a folder**; when one file (e.g. `models.py`)
outgrows a handful of items, promote it to a package with an `__init__.py` that re-exports
— imports elsewhere don't change. Grow into folders; don't start there.

## 10. Build sequencing
**A. Reorg PR (behavior-preserving, first).** Split `/backend` + `/frontend`; carve the
monolith into feature modules + service layer; extract the pure rules that already exist
(`dice`, grid `distance`) into `engine/`; drop all desktop/packaging; serve the SPA as
static web assets; add this `ARCHITECTURE.md`. Create `core/`, `modules/`, `engine/`,
`shared/` now (they hold real code); reserve the other package names here and create each
when its feature epic lands. API + DB stay frozen; tests stay green.

**B. Hosting pivot epic (next).** `identity/` (accounts/auth) + `games/`
(games/memberships/invites) + `authz/` (policy), **plus the `core/realtime/` hub** (auth'd,
game-scoped channels + presence + role-filtered broadcast) since it depends on games+authz
and powers the live combat/map/dice sync. This turns the single-tenant app into the
multi-tenant, real-time service; scope existing campaign data under games and gate it.

**C. Feature epics (each its own PR series).**
- `content/` — SRD ingestion + query + RAG source (mind the licensing, §8).
- `ai/` — **optional** assistive helper behind a provider port (Qwen/Ollama/hosted/off) + RAG; must degrade gracefully when disabled.
- `generation/` — name/statblock/NPC/world generators.
- `rulesets/` — 5e as data first; keep the `engine/rules` interface **lean** (target a couple of systems, not a universal rules DSL).
- `api/v1` — public, versioned surface for integrators and self-hosters.

## 11. Cross-cutting concerns & decisions
These belong to no single module, which is why they get forgotten until they hurt. Each has a
**recommended default** so the agent isn't left guessing. Split by urgency.

### 11.1 Decide before Epic B (load-bearing for how every module reads & writes)

**Authorization enforcement point.** *Where* the gate fires matters more than that it exists.
- **Default:** enforce at the **service layer via a required context**, not only in routes. Every campaign-scoped service takes an `AuthContext` (user + resolved membership/role); routes build it from a FastAPI dependency and pass it in. Leaving it to per-route checks means every new endpoint is a chance to forget one and leak another game's data.

**Tenant-scoping query pattern.** Shared tables + `campaign_id` filter — but never hand-written per call.
- **Default:** a single **scoped-query helper**; give it the campaign context once and it injects the filter. A raw-session query inside a campaign module is the thing that looks wrong.
```python
# core/scoping.py  (illustrative)
class Scope:
    def __init__(self, session, campaign_id): ...
    def query(self, model):          # every campaign-scoped model MUST carry campaign_id
        return self.session.query(model).filter(
            model.campaign_id == self.campaign_id,
            model.deleted_at.is_(None),   # see lifecycle below
        )
```
Services receive a `Scope`, not a bare `Session`.

**Delete & data lifecycle.** Decide before foreign keys are everywhere.
- **Default:** **soft-delete** top-level aggregates (`game`, `campaign`) via a nullable `deleted_at` that the scoped helper filters automatically; hard-delete leaf rows. Define cascade intent explicitly: deleting a campaign soft-deletes its world data; removing a membership revokes access but keeps authored content attributed to the game; **account deletion anonymizes** authored rows (GDPR-style "right to delete") rather than orphaning FKs. Document the cascade table.

**Error envelope & API contract.** One shape, decided once.
- **Default:** a single JSON envelope from `shared/errors.py` — `{"error": {"code": "...", "message": "...", "details": {...}}}` — backed by a small typed exception hierarchy (`NotFound`, `Forbidden`, `Validation`, `Conflict`) mapped by one handler. The Vue client and `api/v1` both depend on this being stable; treat it as part of the versioned contract.

**Config validation at boot.** Env-driven config *will* be misconfigured by self-hosters.
- **Default:** a typed settings object (pydantic-settings) validated on startup; **fail fast with a clear message** on missing `SECRET_KEY`, bad `LLM_PROVIDER`, or unreachable `DATABASE_URL`. Never crash lazily at first use.

### 11.2 Build the seam now, implement later
- **Background/async work.** Slow work (LLM calls, SRD ingest, RAG index build, emails) must not block request workers. **Default:** a thin task abstraction now (FastAPI `BackgroundTasks` / a `tasks` helper); swap in a real queue (arq/RQ/Celery) behind the same interface if load demands. Never call the LLM inline in a request path without this seam.
- **File/media storage.** Map images, portraits, token art. **Default:** a small storage port (`save / url / delete`) with a local-disk implementation, so a self-hoster pointing at S3-compatible storage later is a config change. Same port philosophy as the LLM.
- **Observability.** **Default:** structured logging with a **correlation id per request and per game/session**, plus `/health` and `/ready` endpoints. Cheap now; essential for debugging a live multiplayer session later.
- **Real-time reconnection.** **Default:** snapshot-on-reconnect (see §7) **plus a monotonic state version** per channel, so a reconnecting client detects missed updates and re-syncs instead of double-applying. Keep player actions idempotent where feasible.

### 11.3 Deliberately deferred (do NOT build yet)
Horizontal scaling / Redis realtime backplane (seam noted in §7) · caching layer · rate
limiting & abuse controls (until public / open registration) · event sourcing / CQRS ·
third-party plugin system · full audit log. Building these now is cost without payoff —
revisit when there's real load or a real user base.

### 11.4 The three to lock first
If nothing else is settled before Epic B: **(1) where authz fires** (service layer + context),
**(2) the scoped-query helper** (no hand-written tenant filters), **(3) delete/lifecycle**
(soft-delete aggregates + account-deletion anonymization). Every module's data access is built
on these; retrofitting them after the schema and endpoints exist is the expensive path.

---
*This document supersedes the local-first / desktop assumptions in the original feature spec.*
