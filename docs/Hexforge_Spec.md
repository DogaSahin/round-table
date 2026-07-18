# Hexforge — Feature Specification & Build Plan (v2)

> Companion to `ARCHITECTURE.md` (the how-it's-structured doc). This spec is the
> **what-to-build** source of truth. **This v2 supersedes all local-first / offline /
> single-DM / desktop / HTMX assumptions from v1.**
>
> **Current state:** v1 is built (all feature modules + map engine + Vue frontend exist) as a
> **monolithic backend**. This spec describes the **target system** and the plan to get there:
> a reorg into the layered architecture, then the hosting/real-time pivot, then new domains.

---

## 1. Vision
Hexforge is a **hosted, multi-tenant, open-source** web app for **worldbuilding** and running
tabletop RPG games in **live, real-time sessions**. A user registers once, then creates games
as a DM and joins others' games as a player — the same account, different roles per game.
Each game holds its private world (wiki, timeline, NPCs, factions, maps, sessions); an **open
SRD reference library** is readable by everyone so anyone can build a world. An **optional AI
helper** generates NPCs/lore and answers rules questions. The long arc: a proper worldbuilding
tool and FRP engine that others can self-host.

## 2. Design principles
- **Hosted & multi-tenant.** Accounts, games, memberships; strict per-game data isolation.
- **Real-time first.** Live sessions with synchronized state (initiative, map, fog, dice) and presence.
- **Open source & self-hostable.** Minimal required infra; everything optional is config-selected; usable with AI off.
- **Modular monolith + service layer.** Package-by-feature; logic in services, not routes.
- **Pure, system-agnostic domain core.** Rules live in a `engine/` that does no I/O; 5e is a ruleset plugin; a couple more systems later.
- **AI is assistive & optional.** Generate/answer only, never autonomous, provider-pluggable.
- **Not full Clean Architecture.** Keep the service boundary; skip domain-entity duplication, repository interfaces, mappers.

## 3. Tech stack
| Layer | Choice | Notes |
|---|---|---|
| API | FastAPI (JSON), Uvicorn | async; native websockets |
| Language | Python 3.12+ | |
| ORM / migrations | SQLAlchemy 2.x + Alembic | model portably (no SQLite-only quirks) |
| DB (default) | **SQLite (WAL)** | zero-config self-host; Postgres via config for scale |
| Realtime | FastAPI WebSockets + in-memory hub | Redis backplane seam for horizontal scale (later) |
| Frontend | **Vue 3 SPA + Vite + TypeScript** | served as static assets by the API or a sibling host |
| Map canvas | Konva.js | layered 2D: tokens, fog, grid |
| Auth | token-based (JWT access+refresh) or server sessions | password hashing (argon2/bcrypt) |
| LLM (optional) | provider **port** | self-hosted Qwen / Ollama / hosted API / disabled |
| Vector store (RAG) | pluggable (e.g. sqlite-vec / Chroma) | optional, only if AI enabled |

## 4. System architecture (summary — see `ARCHITECTURE.md` for full detail)
Layered modular monolith. Dependencies point **inward** to a pure core.

```
outer/volatile:  api/v1 · modules/*/routes · ai/tools · realtime handlers
                          │ (depends inward)
features:        modules/*  (campaign-scoped persistence + orchestration)
                          │
domain:          generation/ → content/ → engine/ + rulesets/   (PURE, no I/O)
cross-cutting:   core/  identity/  games/  authz/  ai/(LLM port impl)  shared/
```

**Hard rules:**
1. **Pure core does no I/O** — `engine`, `content`, `generation` never touch DB, network, or the LLM directly. Data in as args, results out as values.
2. **External volatility behind ports** — persistence in services; LLM behind an `ai/` interface; HTTP in routes/api.
3. **Module boundary** — every feature is one folder, four files: `models.py` (ORM), `schemas.py` (Pydantic DTOs), `service.py` (logic, **no FastAPI**), `routes.py` (HTTP only → validate, call service, return). Modules register with core via `register(registry)`. No top-level `entities/`/`services/`/`routes/` folders.

## 5. Multi-tenancy & access model
- **`User` 1—* `Membership` *—1 `Game`.** Role lives on the **membership**: `role ∈ {dm, player}`. One account, many memberships, different roles per game.
- **`Game`** is the tenant boundary and membership scope. A game owns one or more **`Campaign`s** (multi-campaign supported); all world data hangs off a campaign.
- **`Invite`** = stored record with an **opaque, expiring token**, a target game, and a granted role; accepting it creates a membership. Links are unguessable tokens, never sequential IDs; support expiry and optional max-uses.
- **Authorization (`authz/`)** is a single cross-cutting policy answering *"can this user do X in game Y?"* Exposed as FastAPI dependencies (route guards) and service-level guards. **Every campaign-scoped read/write** resolves resource → campaign → game → membership → role. Centralized so no endpoint can forget the check.
- **Visibility within a game:** DM sees everything; players see only shared/non-secret content (see per-feature "player visibility" flags). Secrets (NPC secrets, DM notes, hidden tokens, unrevealed fog) never reach a player payload.
- **Open content** (`content/`, SRD) is **global-read** — not game-scoped.

## 6. Real-time sessions
Live play is a core subsystem (`core/realtime/`), used by any module with live state.
- **Channels are game-scoped** (`game:{id}`). Socket **authenticates on connect** (token) and must prove membership; the connection's **role filters payloads** (players never receive DM-only layers, secret tokens, or hidden monster HP).
- **Presence** per channel: who's currently at the table.
- **Server-authoritative.** DM is authoritative; players emit a bounded action set (roll dice, move own token). Last-write-wins is sufficient — no CRDT/OT.
- **Message envelope:** `{ "channel": "game:12", "topic": "combat|map|dice|presence", "action": "...", "payload": {...} }`.
- **Snapshot + deltas:** on connect a client GETs a role-filtered snapshot of active session state, then applies WS deltas.
- **Scaling seam:** in-memory manager behind an interface; a Redis pub/sub backplane can slot in later. Not built now.

## 7. Self-hosting, configuration & licensing
- **Minimal infra:** a default install needs only Python + SQLite. Postgres, Redis backplane, LLM provider, and vector store are all **optional and config-selected**. The app is fully usable with **AI disabled**.
- **Config over code** via environment: `DATABASE_URL`, `SECRET_KEY`, `LLM_PROVIDER` (`none|qwen|ollama|openai_compatible`), `LLM_BASE_URL`, `LLM_API_KEY`, `VECTOR_STORE`, `ALLOW_REGISTRATION`, `PUBLIC_BASE_URL`. Ship `.env.example` + docs. Provide an optional Dockerfile / compose for one-command self-host.
- **Migrations** apply cleanly forward; never edit a released migration.
- **Versioned public API** (`api/v1`) is a stability contract; internal refactors must not break it.
- **Licensing:** choose an OSS license for the project. Ship only OGL / Creative-Commons SRD content; keep it in `content/` **separable and attributed**; never bundle non-SRD material.

## 8. Data model
Grouped by domain. Images (map/token/portrait) stored on disk (or object store), paths in DB. JSON columns hold flexible blobs. All campaign-scoped tables carry `campaign_id`.

### 8.1 Identity
- **user**(id, email, username, password_hash, display_name, is_active, is_superuser, created_at)
- **refresh_token**(id, user_id, token_hash, expires_at, revoked) — if using JWT refresh; omit for pure server sessions.

### 8.2 Games (multi-tenant spine)
- **game**(id, name, description, owner_user_id, ruleset_key, created_at)
- **membership**(id, game_id, user_id, role['dm'|'player'], status['active'|'invited'|'removed'], joined_at) — unique (game_id, user_id)
- **invite**(id, game_id, token_hash, role, created_by, expires_at, max_uses, uses, created_at)
- **campaign**(id, game_id, name, is_active, created_at) — world data hangs off this

### 8.3 Reference content (open, global — `content/`)
- **content_source**(id, name, license, version)
- **creature**(id, source_id, name, cr, type, size, statblock_json)
- **spell**(id, source_id, name, level, school, casting_time, range, components, duration, body)
- **item**(id, source_id, name, type, rarity, body_json)
- **rule_page**(id, source_id, title, slug, category, body_md) — the open rules wiki
- **content_chunk**(id, ref_type, ref_id, text, embedding) — RAG index (optional; may live in the vector store)

### 8.4 Rulesets / engine registry
- **ruleset**(id, key, name, version, is_default) — installed rule systems (5e default)

### 8.5 Feature modules (campaign-scoped, private to game members)
- **encounter**(id, campaign_id, name, round, active_combatant_id, is_active)
- **combatant**(id, encounter_id, name, initiative, hp_current, hp_max, ac, conditions_json, sort_order, is_pc, npc_id?, token_id?, visible_to_players)
- **npc**(id, campaign_id, name, statblock_json?, motivation, secrets, voice_notes, portrait_path?, faction_id?, disposition, player_visible)
- **faction**(id, campaign_id, name, description, disposition_to_party, goals)
- **faction_clock**(id, faction_id, name, segments, filled)
- **faction_activity**(id, faction_id, session_id?, occurred_at, entry)
- **relationship**(id, campaign_id, source_type, source_id, target_type, target_id, label)
- **wiki_page**(id, campaign_id, title, slug, body_md, category, player_visible, updated_at)
- **wiki_link**(source_page_id, target_page_id); **tag**(id, campaign_id, name); **wiki_page_tag**(page_id, tag_id)
- **map**(id, campaign_id, name, image_path, image_w, image_h, grid_size_px, grid_offset_x, grid_offset_y, feet_per_square, diagonal_rule, grid_visible, is_active)
- **token**(id, map_id, name, image_path?, color, x, y, size_squares, layer, hp_current?, hp_max?, status_markers_json, is_pc, npc_id?, combatant_id?, visible_to_players)
- **fog_region**(id, map_id, kind['reveal'|'hide'], geometry_json, order_index)
- **session**(id, campaign_id, number, date, title, summary)
- **session_log**(id, session_id, logged_at, text, tag)
- **saved_roll**(id, campaign_id, user_id?, label, expression); **roll_history**(id, campaign_id, user_id, expression, result, breakdown_json, rolled_at)

### 8.6 Cross-module links (optional)
`combatant.token_id` ↔ `token.combatant_id` (shared HP); `faction_activity.session_id`; wiki `[[links]]` may point at NPCs/factions.

## 9. Domain layers
### 9.1 `engine/` (pure, system-agnostic)
Rules logic with no I/O: **dice resolution** (`NdM`, modifiers, `kh/kl`, adv/dis), **grid distance** (all four rules, §11.3), **encounter/CR math**, **progress clocks / world-sim**. `engine/rules/` defines the abstract **Ruleset interface** — the operations a game system must provide (ability scores, proficiency, CR→XP, condition set, etc.). Keep the interface **lean** (target a couple of systems, not a universal DSL).

### 9.2 `rulesets/` (rules as data/plugins)
Concrete implementations of the Ruleset interface. `rulesets/dnd5e/` first. A ruleset supplies system constants + hooks; `engine` stays generic.

### 9.3 `content/` (open reference domain)
SRD ingestion pipeline (`ingest.py`) + query service over creatures/spells/items/rules. Read-mostly, campaign-independent, global-read. Feeds in-app lookups, the public API, and RAG. Licensing per §7.

### 9.4 `generation/` (generators)
Composable generators: names, statblocks, NPCs, settlements, world features. Compose `engine` + `content` (+ the `ai` port when enabled). **Logic only, no persistence** — callers (module services / agents) persist results. Must produce useful output even with AI off (deterministic/table-based fallback).

### 9.5 `ai/` (optional assistive)
LLM client **behind a provider port** (Qwen/Ollama/hosted/off), a **RAG pipeline** over `content`, prompt orchestration, and helper functions surfaced to the DM (generate NPC/lore, answer a rules question). **Bounded to generate/answer — never autonomous game mutation.** Every feature degrades gracefully when disabled.

### 9.6 `api/v1/` (public, versioned)
Curated, stable adapters over services — decoupled from internal module routers. Exposes reference content (read) and authenticated campaign operations for integrators/self-hosters. Versioned; breaking changes require a new version.

## 10. Feature modules (detailed)
All are campaign-scoped, gated by `authz`, and role-aware (players get filtered views). Live-state modules publish over `game:{id}`.

- **Dice roller.** Notation parser lives in `engine`; the module owns saved rolls, history, and **broadcasting rolls to the table** in real time. Any participant can roll; results are visible to the table (DM can roll privately).
- **Combat tracker.** Encounter + combatants; drag-reorder initiative; HP/AC/conditions/concentration; round + next-turn (DM-authoritative). Broadcasts to the table; **players see turn order and PC HP, not hidden monster HP**. Add combatants manually or from NPCs; optional token link.
- **NPCs & factions.** NPC CRUD (portrait, statblock, motivation, **secrets — DM-only**, voice, disposition, `player_visible`); faction CRUD with **clocks** and a **timestamped activity log** (group actions); **relationship map**. Throwaway-NPC generator (uses `generation`). Secrets never sent to players.
- **Worldbuilding wiki (private, per campaign).** Markdown pages with `[[wikilinks]]` → backlinks; categories, tags, full-text search; per-page `player_visible`. Distinct from the **open SRD rules wiki** in `content/`. Command palette jumps to pages/NPCs/factions.
- **Sessions & timeline.** Per-session timestamped log (tagged), summary, recap compile; feeds the campaign **timeline** and dashboard (recent faction moves, near-full clocks, open threads).
- **Maps / VTT.** See §11.

## 11. Map engine (Roll20-style, real-time)
Konva.js layered canvas, now multi-user and role-filtered.

### 11.1 Layers (bottom→top)
1. Background image · 2. Grid (configurable, toggleable) · 3. Tokens (`visible_to_players` filters the player view) · 4. Fog (DM ~50% translucent; players opaque) · 5. DM-only layer (secret notes/tokens; never in a player payload).

### 11.2 Grid & scale
Configurable `grid_size_px` (default 70), `feet_per_square` (default 5), `grid_offset` to align to the image; snap-to-grid toggle.

### 11.3 Distance (parity with Roll20 — from `engine`)
| Rule | Formula (dx,dy in squares) | Notes |
|---|---|---|
| Chebyshev (5e default) | `max(dx,dy) × feet` | every diagonal = 5 ft |
| 5-10-5 alternating (DMG) | `(max + ⌊min/2⌋) × feet` | diagonals alternate 5/10 |
| Euclidean (Roll20 default) | `round(√(dx²+dy²)) × feet` | true straight-line |
| Manhattan | `(dx+dy) × feet` | no diagonals |

Ruler tool: click-drag + waypoints; per-map `diagonal_rule`.

### 11.4 Tokens
Image/colored disc, name label, size in squares, optional HP bar (`visible_to_players` toggle), status markers, drag-to-move (snap optional), context menu (rename/resize/remove/visibility/HP). **Moving a token broadcasts** on `game:{id}` → all participants update live (player view filtered).

### 11.5 Fog of war
Manual reveal v1: rectangle-reveal, freehand brush, hide/re-fog, reveal-all, hide-all. Persisted as ordered `fog_region` ops rendered as a mask; edits **broadcast live**. (Dynamic line-of-sight lighting is deferred.)

### 11.6 Live play + roles
Setting a map active broadcasts it as the table's current map; participants subscribe to `game:{id}` and render with role rules (players: opaque fog, filtered tokens, no DM layer).

## 12. UI / UX design (Vue 3 SPA)
### 12.1 Branding
- **Name:** Hexforge. **Mark:** hexagon outline + spark/anvil-bolt glyph in amber. Sizes: full lockup, icon-only (app/nav), monochrome (favicon). Icon SVG: hexagon `points="15,3 26,10.5 26,19.5 15,27 4,19.5 4,10.5"` (30×30, 1.2px stroke) with bolt `M15 10 L19 15 L16 15 L18 21 L11 14 L14 14 Z`.
- Dark, table-friendly default; amber = brand/active; blue = primary action; two font weights (400/500); sentence case.

### 12.2 App shell & navigation
- **Auth screens:** register / login / accept-invite.
- **Game switcher** (top bar): pick which game you're in; your role in it is shown. "Jump to anything" command palette (Ctrl-K).
- **Left nav:** campaign modules (Home/dashboard, Combat, Maps, NPCs, Factions, Wiki, Sessions, Dice) — **role-adaptive** (players see a reduced set).
- **Live session view (VTT):** map center; initiative + dice rail; presence indicator; role-filtered.
- Color semantics: disposition (red/amber/green), HP shading, purple condition chips.

### 12.3 Flows
- **Create game** → becomes DM → create campaign → invite players (generates an invite link) → players accept → land in the game with player role.
- **Player view** = live session + read access to `player_visible` content only.

## 13. Public API (v1)
Versioned REST under `/api/v1`. Read access to open reference content (creatures/spells/items/rules). Authenticated (token) access to the caller's games/campaigns per `authz`. Stable schemas; breaking changes → new version. OpenAPI published.

## 14. Security & authz
- Passwords hashed (argon2/bcrypt); tokens signed with `SECRET_KEY`; refresh rotation if JWT.
- **Every** campaign-scoped endpoint and websocket subscription passes an `authz` guard (membership + role).
- Invite tokens hashed at rest, expiring, optionally single/limited-use.
- Player payloads are filtered server-side (never rely on the client to hide secrets).
- `ALLOW_REGISTRATION` gates open sign-up for self-hosters.

## 15. Project structure (target)
```
backend/app/
├─ main.py
├─ core/     config.py database.py registry.py security.py realtime/
├─ engine/   dice.py distance.py encounter.py clocks.py rules/
├─ rulesets/ dnd5e/
├─ content/  models.py schemas.py service.py ingest.py
├─ generation/ names.py statblocks.py npc.py settlement.py world.py
├─ ai/       client.py rag.py prompts.py tools.py
├─ identity/ models.py schemas.py service.py routes.py
├─ games/    models.py schemas.py service.py routes.py
├─ authz/    policy.py deps.py
├─ modules/  combat/ maps/ npcs/ factions/ wiki/ sessions/ dice/  (each: models schemas service routes __init__)
├─ api/      v1/
└─ shared/   errors.py pagination.py types.py
frontend/    src/ (Vue 3 SPA)  tests/  vite.config.ts
docs/        Hexforge_Spec.md  ARCHITECTURE.md
```

## 16. Build sequencing
**Epic A — Repo reorg (behavior-preserving).** Split `/backend` + `/frontend`; carve monolith into feature modules + service layer; extract pure `dice`/`distance` into `engine/`; drop desktop/packaging; serve SPA as web static; add `ARCHITECTURE.md`. API + DB frozen, tests green. *(See the separate reorg prompt.)*

**Epic B — Hosting & real-time pivot.** `identity` (auth) + `games` (games/memberships/invites) + `authz` (policy) + `core/realtime` (auth'd game channels + presence + role-filtered broadcast). Retrofit existing campaign data under games/campaigns and gate every access. Convert the old DM→player push into multi-user role-filtered live sync.

**Epic C — Reference content + open rules wiki.** `content/` ingestion of SRD, query service, in-app lookups, licensing/attribution.

**Epic D — Public API v1.** Versioned surface over content + campaign services.

**Epic E — AI helper (optional).** `ai/` provider port + RAG + generate/answer helpers; `generation/` engines with non-AI fallbacks. Feature-flagged; fully disableable.

**Epic F — Ruleset abstraction.** Extract 5e specifics into `rulesets/dnd5e`; keep the `engine/rules` interface lean; prove a second system is addable.

**Epic G — Self-host packaging.** Dockerfile/compose, `.env.example`, deploy + upgrade docs, OSS license, migration hygiene.

## 17. Task backlog — tech lead notes

> Note on sourcing: the five features below (Bestiary, Campaign Timeline, Multi-Campaign
> Support, World Wheel, Campaign Arc → Session Structure) were previously drafted as a
> **standalone backlog file**, written before the hosting/multi-tenant/real-time pivot. That
> file isn't reproduced verbatim here — it's been **re-derived through the current
> architecture** as Epic H, since several of them mean something different now (Multi-Campaign
> is largely already true of the data model; a "relationship graph" becomes the World Wheel).
> If the original file surfaces, diff it against Epic H for anything I've mis-remembered.

Every epic below has three things a tech lead actually wants on a ticket: the **concern**
(what could go wrong / why this isn't just typing), the **plan** (the approach, in order),
and the **architecture touchpoints** (which layers/rules from `ARCHITECTURE.md` this leans
on). Tasks are sized to one sitting. **CRUD slice** = model + migration + seven endpoints
(list/new/create/detail/edit/update/delete), JSON in/out, every list **scoped by campaign
and gated by `authz`** per §11.1.

---

### Epic A — Repo reorg
**Concern:** this is the one epic where the failure mode is *silent regression* — a route
that quietly changes shape, a schema drift nobody notices until Epic B builds on it. It's
also the epic that happens *before* any of the new architecture exists, so it's tempting to
over-scope it into "also add auth." Don't — see Guardrails in the reorg prompt.
**Plan:** delivered by the standalone reorg prompt (split `/backend`+`/frontend`, carve the
monolith into four-file modules, extract pure `dice`/`distance` into `engine/`, drop
desktop/packaging, serve the SPA as static assets).
**Architecture touchpoints:** establishes the module boundary (`ARCHITECTURE.md` §3–4) that
everything else assumes exists.
**Acceptance:** tests green, API frozen, empty Alembic diff, four-file modules, `service.py`
has no FastAPI import.

---

### Epic B — Hosting & real-time pivot
**Concern:** this is the highest-risk epic in the whole roadmap. It's where a single missed
`authz` check leaks another game's data, and where the WS layer either gets auth right from
the first line or accumulates "we'll add the check later" debt that never gets paid. Per
§11.4, three things here are **load-bearing for every later module**: where authz fires, the
scoped-query helper, and delete/lifecycle. Get those three right before touching feature
retrofits (B15).
**Plan:** identity → games/memberships/invites → authz → retrofit existing modules → realtime
hub → wire live features → frontend. In that order — authz has to exist before B15 can use it,
and B15 has to land before realtime broadcasts something unfiltered.
**Architecture touchpoints:** §5 (multi-tenancy), §6 (sharing — B15 is exactly the "compose in
the caller" pattern, not module-to-module imports), §7 (real-time), §11.1 (the three
load-bearing decisions).

**Identity & auth**
- **B1** `user` model + migration; password hashing util in `core/security`.
- **B2** Register endpoint (`ALLOW_REGISTRATION`-gated) + validation.
- **B3** Login endpoint → issue access (+refresh) token.
- **B4** Auth dependency (`get_current_user`) + refresh/logout.

**Games, memberships, invites** *(the multi-tenant spine — get the shape right, it's everywhere after this)*
- **B5** `game` model + migration.
- **B6** `membership` model + migration (unique game+user; **role lives here, not on `user`** — §5).
- **B7** `invite` model + migration (**hashed token at rest**, expiry, max-uses — §11.1 config/secrets discipline applies to tokens too).
- **B8** CRUD slice for `game` (owner becomes DM membership on create — one transaction, not two).
- **B9** Create-invite endpoint (returns opaque link; token is random, never sequential).
- **B10** Accept-invite endpoint (creates player membership; validate expiry/uses **atomically** to avoid a race on a popular invite link).
- **B11** List my games + my role per game.
- **B12** `campaign` model + migration; game→campaigns (1—*); CRUD slice. *(This is what makes Multi-Campaign Support in Epic H "already true" — see H3.)*

**Authorization — build this before retrofitting anything**
- **B13** `authz/policy.py` — `can(user, action, resource)` resolving resource→campaign→game→membership→role. **Design note (§11.1):** implement as the thing services call via a required `AuthContext`, not a route-only check — a route-only check is exactly the pattern that lets a future endpoint forget it.
- **B14** `authz/deps.py` — FastAPI guards (`require_member`, `require_dm`) that build the `AuthContext` from the request and hand it to the service.
- **B14b** `core/scoping.py` — the `Scope` helper from §11.1 (campaign filter + soft-delete filter in one place). Build this **now**, alongside authz, so B15 has it to retrofit against instead of each module inventing its own filter.

**Retrofit existing modules** *(one task per module — don't batch, each is a real review)*
- **B15.1** combat — scope by campaign, apply `authz`, route data access through `Scope`.
- **B15.2** maps — same, plus confirm token/fog queries go through `Scope`.
- **B15.3** npcs — same, plus B16 (secrets filtering) lands here too.
- **B15.4** factions — same.
- **B15.5** wiki — same, plus `player_visible` filtering (B16).
- **B15.6** sessions — same.
- **B15.7** dice — same; saved rolls become per-user *within* a campaign, not global.
- **B16** Add `player_visible` / secrets filtering to npc, wiki, token, combatant payloads — **server-side only**, per §14 ("never rely on the client to hide secrets").

**Real-time**
- **B17** `core/realtime` connection manager + presence, behind an interface (§7 — keep the Redis seam, don't build Redis).
- **B18** WS endpoint `game:{id}` with **auth-on-connect** + membership check (reuses B13/B14 — the socket is not a second, separate auth system).
- **B19** Role-filtered broadcast helper — same filtering logic as B16, applied to WS payloads, not a re-implementation.
- **B20** Snapshot endpoints (role-filtered) for combat + map + dice — this is what a reconnecting client GETs before applying deltas (§11.2 reconnection semantics: pair this with a state version if you have time, or file it as a fast-follow).
- **B21** Wire combat changes → broadcast on `game:{id}`.
- **B22** Wire token move + fog edits → broadcast.
- **B23** Wire dice rolls → broadcast (private-roll option: DM-only rolls never leave the DM's channel — test this explicitly, it's an easy leak).
- **B24** Presence UI + live session join/leave.
- **B25** Frontend: auth screens, game switcher, create-game + invite + accept flows, role-adaptive nav, live session view.

---

### Epic C — Reference content (open SRD)
**Concern:** this is global-read data sitting next to strictly private campaign data in the
same database — the risk isn't access control (it's open to everyone by design), it's
**licensing hygiene** (§8) and **not accidentally coupling it to campaign code** (a module
importing `content` directly is fine — that's downward, per §6 case 1 — but `content`
importing a module is the violation to watch for).
**Plan:** models → ingestion → query service → UI → RAG index (optional, gates on E's config).
**Architecture touchpoints:** §9.3 (`content/` is pure/read-mostly, campaign-independent), §8
licensing.
- **C1–C4** models + migrations: content_source, creature, spell, item, rule_page.
- **C5** SRD ingestion pipeline (parse → upsert; **idempotent** — re-running an ingest on a new SRD version must not duplicate rows); attribute each `content_source` to its license.
- **C6** Query/service + list/detail endpoints (global-read, no `authz` needed — this is the one domain that's intentionally ungated).
- **C7** In-app reference lookup UI + palette integration.
- **C8** Optional `content_chunk` index build for RAG — guarded by `LLM_PROVIDER`/`VECTOR_STORE` config (§11.1 fail-fast: if AI is off, this task is a no-op, not an error).

---

### Epic D — Public API v1
**Concern:** the moment this ships, `api/v1` is a promise to strangers. Internal refactors
(which will happen — Epic F changes `engine/rules`, generators evolve) must not break it. The
temptation to route `api/v1` straight into module internals is the thing to resist.
**Plan:** thin versioned adapters over existing services — never a second implementation of
the same logic.
**Architecture touchpoints:** §9.6 (`api/v1` decoupled from internal module routers), §11.1
error envelope (this is the layer where contract stability matters most).
- **D1** `api/v1` router skeleton + versioning + OpenAPI.
- **D2** Read endpoints for content (creatures/spells/items/rules) — thin wrapper over C6's service, not a reimplementation.
- **D3** Authenticated campaign read endpoints (authz-gated, same `AuthContext` as B13/B14).
- **D4** Rate limiting + API tokens (optional) + docs page.

---

### Epic E — AI helper (optional)
**Concern:** the two failure modes are (1) the app breaking or degrading badly when
`LLM_PROVIDER=none`, and (2) a generator becoming useless without AI because someone wrote it
LLM-first instead of LLM-optional. Build the deterministic path first, bolt AI on as an
enhancement — not the other way around.
**Plan:** provider port (works when off) → RAG → generators with fallback → LLM-assisted
composer → endpoints → frontend graceful-degradation states.
**Architecture touchpoints:** §9.4–9.5 (`generation` composes `engine`+`content`+the `ai`
port; `ai` is bounded to generate/answer, never autonomous), §11.1 config validation, §11.2
background-work seam (don't call the LLM inline in a request — E4/E5 should go through the
task seam from B's era if responses are slow).
- **E1** LLM provider port + config (`none|qwen|ollama|openai_compatible`); confirm every other E task still passes with this set to `none`.
- **E2** RAG pipeline over `content` (retrieve → prompt).
- **E3** `generation` — name + statblock generators with a **deterministic/table-based fallback** (the "works with AI off" requirement from §1/§7 starts here).
- **E4** `generation.npc` composer (uses E3's generators + optional LLM enhancement).
- **E5** DM-facing "generate NPC/lore" endpoint → returns a **draft for review/save**, never auto-persisted (the DM stays the author of their world).
- **E6** "Answer a rules question" endpoint (RAG over SRD via C6).
- **E7** Frontend: AI panel + an explicit, non-broken "AI disabled" state (not a spinner that never resolves).

---

### Epic F — Rulesets
**Concern:** the trap is building a "universal ruleset interface" nobody asked for (§16/§9.1:
target a couple of systems, not a DSL). The interface is done when a second system is
addable without touching `engine/`, not when it's theoretically infinite.
**Plan:** extract the interface from what 5e already needs → implement 5e as the first plugin
→ prove portability with a thin second system.
**Architecture touchpoints:** §9.1–9.2 (`engine/rules` interface vs `rulesets/*` plugins) —
this is the clearest example in the whole codebase of "push shared logic down, keep the
implementation swappable."
- **F1** `engine/rules` abstract interface — derive it from what 5e actually needs, not speculative generality.
- **F2** `rulesets/dnd5e` implementation; move 5e-specific constants/hooks out of `engine`.
- **F3** `ruleset` registry + per-game `ruleset_key` selection (a game picks its system at creation).
- **F4** Validate a second system is addable — a **thin proof** (even a stub system with a couple of real rules), not a second full implementation. This task exists specifically to catch an interface that's secretly 5e-shaped.

---

### Epic G — Self-host packaging
**Concern:** you will not be there when someone else's install breaks. Every default has to
be safe, every failure has to be loud and early (§11.1 config validation), and the SRD
license question has to be settled, not assumed.
**Plan:** document config → containerize with safe defaults → write the upgrade path →
finalize licensing.
**Architecture touchpoints:** §8 (self-hosting constraints), §11.1 (fail-fast config).
- **G1** `.env.example` + config docs (every var from §8 — `DATABASE_URL`, `SECRET_KEY`, `LLM_PROVIDER`, etc.).
- **G2** Dockerfile + compose — SQLite default, Postgres/Redis/LLM all opt-in via config, never required.
- **G3** Deploy + upgrade + migration docs — explicitly cover "how do I upgrade without losing data," since that's the question a self-hoster asks at 11pm.
- **G4** OSS license + SRD attribution/licensing notes (§8) — get a second pair of eyes on this one; it's the one item here with real legal weight.

---

### Epic H — Worldbuilding depth (Bestiary, Timeline, Multi-Campaign UI, World Wheel, Arcs)
**Concern:** all five of these were originally scoped for the *old* local-first, single-DM
app. Re-read through the current architecture, they split into three very different kinds of
work — a genuinely new domain, a UI layer on data that already exists, and a module that's
mostly already done. Treating all five as "new features" would mean re-building things the
hosting pivot already gave you for free. **Sequence this epic after B**, not before — every
item below depends on campaign-scoping and several depend on real-time.

#### H-i. Multi-Campaign Support → mostly already delivered by B12
**Plan:** the data model (`game` → many `campaign`s) exists from Epic B. What's left is
purely the experience of moving between campaigns without losing your place, plus closing any
module that still assumes "one active campaign" implicitly.
- **H1** Campaign switcher UI (top bar) — list a game's campaigns, switch active one, persist selection per session.
- **H2** Audit every module's queries for an implicit "the" campaign assumption (a leftover from v1's single-campaign world) and confirm they all take an explicit `campaign_id` via `Scope` (§11.1) — this is a review task, not new code, but skipping it is how a stale assumption survives into production.
- **H3** Archive/duplicate-campaign actions (start a new arc in the same game without losing the old one).

#### H-ii. Bestiary → a genuinely new domain, sitting next to `content`, not inside it
**Concern:** the obvious mistake is bolting "homebrew creatures" onto the `content` module,
which is supposed to stay open/global-read SRD data. A DM's homebrew monster is **private,
campaign-scoped** — it's a feature module, not reference content. The two should *share a
statblock shape* (so the combat tracker doesn't care whether a creature came from the SRD or
a DM's bestiary) without sharing a table.
**Plan:** define a shared statblock schema in `shared/` (or `engine/`, if it needs rules
logic) that both `content.creature` and the new module can produce; build the campaign-scoped
module on top.
**Architecture touchpoints:** §6 case 1 (shared shape → shared layer, not a cross-import) and
case 2 (combat reads a creature's statblock through a narrow interface regardless of source).
- **H4** Define a shared `Statblock` schema (used by both `content.creature` and this module) in `shared/`.
- **H5** `bestiary` module: `models`/`schemas`/`service`/`routes` (campaign-scoped, four-file shape); CRUD slice.
- **H6** "Add from SRD" action — copies a `content.creature` into the campaign bestiary as a starting point (composition, not inheritance — no live link back to `content`).
- **H7** Wire the combat tracker's "add combatant" flow to search **both** SRD creatures and the campaign bestiary through the shared `Statblock` shape.
- **H8** (stretch) Feed `generation`'s statblock generator (E3) output straight into the bestiary as a save target.

#### H-iii. Campaign Timeline → a new module, deliberately separate from Session Log
**Concern:** "timeline" and "session log" sound like the same thing and aren't. Session log
(already in v1) is *real-world* — what happened at the table, tagged, timestamped by session
number. Timeline is *in-world* — dates on Varemoor's calendar, travel time, faction-clock
deadlines. Conflating them is the likely mistake; keep them as two modules that **reference**
each other rather than merging.
**Plan:** in-world calendar/date model → timeline entries → let sessions and faction activity
*publish* onto the timeline rather than the timeline reaching into them.
**Architecture touchpoints:** §6 case 3 (event bus) is the right shape here — "session N
happened" or "faction clock filled" should be able to create a timeline entry without the
`timeline` module importing `sessions` or `factions`, and without `sessions`/`factions`
knowing timeline exists.
- **H9** `timeline` module: in-world date/calendar model (configurable calendar — days-per-month, month names, matches your Varemoor worldbuilding) + `timeline_entry` (date, title, description, source type/id).
- **H10** CRUD slice for manual timeline entries (a DM can add "the Church seized the docks" directly).
- **H11** Small `core/events` bus (§6 case 3) if it doesn't exist yet from an earlier epic; keep it minimal — publish/subscribe, in-process, no persistence layer of its own.
- **H12** Publish a timeline event when a session is logged (`session.logged` → optional timeline entry) and when a faction clock fills (`clock.filled` → timeline entry) — both as **subscribers**, not edits to `sessions`/`factions`.
- **H13** Timeline view UI — chronological, filterable by source (session / faction / manual).

#### H-iv. World Wheel visualization → a read-only composition, not a new data domain
**Concern:** the temptation is to invent a new "relationships" backend concept. Don't — the
data already exists (`relationship`, `faction.disposition_to_party`, `faction_activity`). The
World Wheel is a **view that composes existing services**, the textbook case of §6 case 2
("compose in the caller," here the frontend or one aggregate read endpoint) rather than a new
coupling between `npcs` and `factions`.
**Plan:** one aggregate read endpoint (or a frontend that calls the existing endpoints and
composes client-side) → a radial/wheel visualization component.
**Architecture touchpoints:** §6 case 2 — this is the reference example to point to when
someone later asks "can I just add a new cross-module table for X."
- **H14** Decide: aggregate backend endpoint (`GET /campaigns/{id}/world-wheel`) vs. pure frontend composition of existing NPC/faction/relationship endpoints. Default to the aggregate endpoint if the payload would otherwise mean many round trips; it's still just a **read composition**, not new persistence.
- **H15** Backend: if aggregating, a thin function in a orchestration layer (not inside `npcs` or `factions`) that calls both services and shapes the response — this function does not become a new module.
- **H16** Frontend: radial/wheel component (factions as spokes, disposition as color per §12, NPCs/relationships as nodes) — reuse the existing color semantics, don't invent a new palette.
- **H17** Click-through from the wheel into the NPC/faction detail views (navigation, not new data).

#### H-v. Campaign Arc → Session Structure → a new module linking story planning to sessions
**Concern:** this is genuinely new — nothing in v1 models a story arc as a planned structure
across future sessions. The risk is scope creep into a full quest/kanban system (already
correctly deferred in §18). Keep this to **arcs containing planned beats**, each optionally
linked to a session once it happens — not a task tracker.
**Plan:** arc + beat models → link beats to sessions (planned vs. actual) → surface on the
dashboard alongside the existing "open threads."
**Architecture touchpoints:** four-file module shape, campaign-scoped + `authz` like every
other feature module; links to `sessions` via a foreign key (not an import — module-to-module
*data* references via FK are fine, module-to-module *code* imports are not, per §6).
- **H18** `arcs` module: `campaign_arc` (name, description, status) + `arc_beat` (ordered, title, description, status: planned/in-progress/resolved, `session_id?` nullable FK) models + migration.
- **H19** CRUD slice for arcs and beats (four-file shape).
- **H20** Drag-reorder beats within an arc (SortableJS, consistent with §12/existing patterns — reuse the same drag idiom as initiative reorder, don't introduce a second one).
- **H21** "Mark beat resolved in session N" action — sets `arc_beat.session_id`, the FK link from beat to session.
- **H22** Dashboard card: active arcs + their next planned beat, alongside the existing recent-activity/open-threads cards.

---

## 18. Deferred (post-roadmap)
Encounter builder with CR balancing · loot/party inventory · full quest/thread kanban (arcs
in Epic H are lighter-weight than this) · handout push · dynamic line-of-sight lighting ·
audio/ambiance · Redis realtime backplane · Postgres-at-scale tuning · homebrew/custom rule
systems beyond a couple · marketplace/sharing of worlds · full audit log · rate limiting until
public/open registration is live.

---
*End of spec. Pairs with `ARCHITECTURE.md`. Supersedes v1's local-first/desktop assumptions.*
