# WW2 Pacific 1940 2nd Edition — Referee-First CV Web App

An autonomous tabletop game master for the physical board game **Axis & Allies: Pacific 1940 Second Edition**. Uses a fixed overhead camera, server-side simulated dice, a full rules engine, and a heuristic bot — with the camera as evidence and the rules engine as the authoritative source of truth.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start (Local Development)](#quick-start-local-development)
- [Convenience Script](#convenience-script)
- [Docker Deployment](#docker-deployment)
- [PostgreSQL Setup](#postgresql-setup)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [WebSocket Protocol](#websocket-protocol)
- [Game Concepts](#game-concepts)
- [Module Details](#module-details)
- [Design Decisions](#design-decisions)
- [V1 Playable Alpha](#v1-playable-alpha)
- [Smoke Tests](#smoke-tests)
- [Implementation Status](#implementation-status)
- [License](#license)

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Backend API | FastAPI + Uvicorn | >= 0.111 |
| Data Models | Pydantic | >= 2.7 |
| ORM / Database | SQLAlchemy 2.0 (async), SQLite (default) / PostgreSQL | >= 2.0.30 |
| Frontend | React + TypeScript + Vite | React 19, Vite 7 |
| State Management | Zustand | 5.x |
| Data Fetching | TanStack Query + Axios | 5.x |
| Computer Vision | OpenCV + Ultralytics YOLO | >= 4.9, >= 8.2 |
| Combat RNG | HMAC-SHA256 CSPRNG | stdlib |
| Containerisation | Docker Compose (nginx + Python slim) | optional |

### Python Dependencies (`apps/api/requirements.txt`)

| Package | Version |
|---|---|
| fastapi | >= 0.111.0 |
| uvicorn[standard] | >= 0.29.0 |
| pydantic | >= 2.7.0 |
| pydantic-settings | >= 2.2.0 |
| sqlalchemy | >= 2.0.30 |
| alembic | >= 1.13.1 |
| aiosqlite | >= 0.20.0 |
| python-multipart | >= 0.0.9 |
| websockets | >= 12.0 |
| httpx | >= 0.27.0 |
| opencv-python-headless | >= 4.9.0 |
| ultralytics | >= 8.2.0 |
| numpy | >= 1.26.0 |
| pillow | >= 10.3.0 |

### Node.js Dependencies (`apps/web/package.json`)

| Package | Version |
|---|---|
| @tanstack/react-query | ^5.90.21 |
| axios | ^1.13.6 |
| react-resizable-panels | ^4.7.2 |
| react-router-dom | ^7.13.1 |
| zustand | ^5.0.11 |
| typescript | ~5.9.3 |
| vite | ^7.3.1 |

---

## Architecture

```
┌──────────────────┐         REST / WS          ┌──────────────────────────────┐
│  React Frontend  │ ◄─────────────────────────► │  FastAPI Modular Monolith    │
│  (Vite + TS)     │                             │  (single process)            │
└──────────────────┘                             └──────────────┬───────────────┘
                                                                │
                                   ┌────────────────────────────┼────────────────────────────┐
                                   │                            │                            │
                          ┌────────▼────────┐         ┌────────▼────────┐         ┌─────────▼────────┐
                          │   game-schema   │         │   rules-core    │         │   battle-core    │
                          │   (Pydantic)    │         │   (pure logic)  │         │   (pure logic)   │
                          └─────────────────┘         └─────────────────┘         └──────────────────┘
                                   │                            │                            │
                          ┌────────▼────────┐         ┌────────▼────────┐         ┌─────────▼────────┐
                          │     vision      │         │ reconciliation  │         │       bot        │
                          │ (OpenCV / YOLO) │         │   (diffing)     │         │  (heuristic AI)  │
                          └─────────────────┘         └─────────────────┘         └──────────────────┘
                                                                │
                                                      ┌────────▼────────┐
                                                      │  SQLite / PG    │
                                                      │  (persistence)  │
                                                      └─────────────────┘
```

**Key architectural principles:**

- **CV never mutates official state** — `observed_state` != `proposed_state` != `official_state`
- **Rules engine is the source of truth** — all state changes validated by `rules-core`
- **Deterministic combat** — HMAC-SHA256 CSPRNG; identical seed + inputs = identical replay
- **Event sourcing** — every change backed by a typed event in the database
- **In-memory hot cache** — `StateStore` holds live `GameState` objects; DB is for persistence and replay
- **Modular monolith** — single FastAPI process; modules are separable later

---

## Project Structure

```
apps/
  api/                      FastAPI modular monolith (single process)
    main.py                 App entry point, CORS, router registration, WS endpoint, health check
    config.py               Pydantic-settings config loaded from .env
    database.py             Async SQLAlchemy engine/session factory
    models.py               4 ORM models: GameSession, StateSnapshot, EventRecord, BattleLog
    state_store.py          In-memory game state cache with WS broadcast callbacks
    ws_manager.py           Per-game WebSocket connection manager
    path_setup.py           sys.path manipulation for package imports
    requirements.txt        Python dependency pins
    routes/
      session.py            Session creation and retrieval
      game.py               State, events, replay, action validation, phase advancement
      combat.py             Battle resolution with CSPRNG
      state.py              Delta commit to official state
      bot.py                Heuristic bot suggestions
      correction.py         Manual corrections and referee overrides
      vision.py             Camera calibration, frame processing, reconciliation

  web/                      React + TypeScript + Vite operator console
    src/
      App.tsx               Root component: SetupPage or GamePage
      main.tsx              ReactDOM root render
      store.ts              Zustand store (session, gameState, bot, WS, observation)
      api.ts                Axios API client (14 functions)
      types.ts              TypeScript interfaces mirroring backend Pydantic schemas
      components/
        PhaseBar.tsx         Current player, round, phase chips, WS indicator
        PhaseControls.tsx    "Done Phase" button with validation
        BattlePanel.tsx      Battle cards with resolve button and round-by-round results
        CombatPrediction.tsx Monte Carlo win-rate predictions
        EconomyPanel.tsx     IPC treasury display per faction
        ZonePanel.tsx        Searchable zone list with indicators
        BotPanel.tsx         Bot suggestion cards with score breakdowns
        CorrectionPanel.tsx  Manual correction form
        EventLog.tsx         Collapsible event log
        BoardFeed.tsx        Camera feed with detection overlay
      hooks/
        useWebSocket.ts     Auto-connect/disconnect, message parsing
      pages/
        SetupPage.tsx        Game creation form with player-faction assignments
        GamePage.tsx         3-column layout: Axis sidebar | center board | Allied sidebar

packages/
  game-schema/src/          Pydantic canonical models
    enums.py                12 enums: Player, Phase, ZoneType, UnitType, UnitStatus, EventType, etc.
    game_state.py           Full GameState model tree (TurnState, Economy, ZoneState, Unit, etc.)
    events.py               19 typed event models extending BaseEvent; AnyEvent union
    observation.py          CV observation models: Detection, ZoneObservation, BoardTransform
    bot.py                  Bot output models: BotSuggestion, ScoreBreakdown, SimulationSummary
    websocket_messages.py   6 WS message types; AnyWsMessage union

  rules-core/src/           Pure rules logic (no I/O)
    phase_machine.py        Turn/phase state machine with advance/validation
    economy.py              IPC economy: purchase validation, income collection, production
    movement.py             Land/air/naval move validation, transports, carriers, BFS reachability
    victory.py              Victory conditions: Japan needs 6/9 victory cities
    map_data.py             Map JSON loader with adjacency BFS, unit cost/combat value lookups
    setup.py                build_initial_state() — 39 zones, ~138 units, starting treasuries

  battle-core/src/          Pure combat logic (no I/O)
    rng.py                  HMAC-SHA256 CSPRNG d6 dice stream from seed
    resolution.py           Full battle loop: simultaneous fire, casualty selection, retreat
    simulation.py           Monte Carlo simulation (200 runs) for battle predictions

modules/
  vision/                   CV pipeline
    calibration.py          Board calibration via contour detection + homography
    detector.py             YOLO unit detection with confidence banding and zone assignment
    zone_mapper.py          Polygon-in-point zone assignment via OpenCV pointPolygonTest

  reconciliation/           Observation-to-delta diffing
    reconciler.py           Compare observed vs official, flag ambiguities, split auto/manual

  bot/                      Heuristic phase advisors
    advisor.py              5 advisors: purchase, combat move, combat decision, non-combat, placement

infra/docker/
  docker-compose.yml        2-service stack: api + web
  Dockerfile.api            Python slim image for the API
  Dockerfile.web            Node build + nginx for the frontend

data/map/
  pacific_1940_2e.json      Canonical map: 39 zones, 9 victory cities, adjacency, starting units

scripts/
  dev/
    smoke_test.py           33 end-to-end HTTP checks against the running API
    start_dev.ps1           PowerShell dev launcher (DB + API + frontend)
  migration/
    init_db.py              SQLAlchemy create_all for database initialization

docs/
  product-spec/
    v1-spec.md              Product specification document
    non-goals.md            Explicit V1 exclusions
  rules/
    behavioral-spec.md      Clean-room game rules behavioral reference
```

---

## Quick Start (Local Development)

### Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- No Docker required — the app uses a local SQLite database by default.

### 1. Install Python dependencies

```powershell
pip install -r apps/api/requirements.txt
```

### 2. Initialize the database

```powershell
$env:PYTHONPATH = (Get-Location).Path
python scripts/migration/init_db.py
```

This creates `referee.db` in the repo root.

### 3. Start the API

```powershell
$env:PYTHONPATH = (Get-Location).Path
uvicorn apps.api.main:app --reload --port 8000
```

| URL | Description |
|---|---|
| http://localhost:8000 | API root |
| http://localhost:8000/docs | Swagger UI (interactive, all 14 endpoints) |
| http://localhost:8000/redoc | ReDoc (alternative API docs) |
| `ws://localhost:8000/ws/{game_id}` | WebSocket for real-time updates |

### 4. Start the frontend

```powershell
cd apps/web
npm install
npm run dev
```

| URL | Description |
|---|---|
| http://localhost:5173 | Operator console |

### 5. Verify everything works

```powershell
$env:PYTHONPATH = (Get-Location).Path
python scripts/dev/smoke_test.py
```

Runs 33 end-to-end checks across all API endpoints. All checks should pass.

---

## Convenience Script

The PowerShell dev launcher starts the full stack in one command:

```powershell
.\scripts\dev\start_dev.ps1
```

This script:

1. Starts PostgreSQL via Docker Compose (the `db` service)
2. Waits 3 seconds for the database to be ready
3. Starts the API server (`uvicorn`) in a new PowerShell window
4. Starts the frontend dev server (`npm run dev`) in a new PowerShell window

> **Note:** The convenience script defaults to PostgreSQL. For pure SQLite local development, use the manual steps in [Quick Start](#quick-start-local-development) instead.

---

## Docker Deployment

Build and run the full stack with Docker Compose:

```powershell
docker compose -f infra/docker/docker-compose.yml up --build
```

| Service | Container | Port | Description |
|---|---|---|---|
| `api` | `referee_api` | 8000 | FastAPI backend (Python slim) |
| `web` | `referee_web` | 80 | React frontend (nginx) |

The web container's nginx configuration proxies `/api/` and `/ws/` requests to the API container.

To run in detached mode:

```powershell
docker compose -f infra/docker/docker-compose.yml up --build -d
```

To stop:

```powershell
docker compose -f infra/docker/docker-compose.yml down
```

---

## PostgreSQL Setup

The app defaults to SQLite, but supports PostgreSQL for production use.

### Option A: Environment variable

Set `DATABASE_URL` before starting the API:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/referee_db"
```

### Option B: `.env` file

Create a `.env` file in the repo root:

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/referee_db
```

The `JSON` column type used by SQLAlchemy works identically on both SQLite and PostgreSQL.

---

## Environment Variables

All settings are defined in `apps/api/config.py` and loaded via Pydantic-settings from environment variables or a `.env` file.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./referee.db` | Async database connection string |
| `APP_NAME` | `WW2 Pacific Referee API` | Application name (shown in docs) |
| `APP_VERSION` | `1.0.0` | Application version |
| `DEBUG` | `false` | Enables SQLAlchemy echo and uvicorn reload |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"]` | Allowed CORS origins (JSON list) |
| `CAMERA_DEVICE_INDEX` | `0` | OpenCV camera device index |
| `CAMERA_CAPTURE_FPS` | `5` | Frame capture rate for vision pipeline |
| `DETECTION_MODEL_PATH` | `models/detector.pt` | Path to YOLO detection model weights |
| `CALIBRATION_MODEL_PATH` | `models/calibration.pt` | Path to calibration model weights |

Frontend environment (set in `apps/web/.env`):

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

---

## API Reference

All endpoints are also available interactively at http://localhost:8000/docs (Swagger UI).

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "ok", "version": "1.0.0"}` |

---

### Session

| Method | Path | Description |
|---|---|---|
| `POST` | `/session/create` | Create a new game session |
| `GET` | `/session/{session_id}` | Retrieve session metadata |

#### `POST /session/create`

Creates a new game session, generates a game ID, builds the initial game state (39 zones, ~138 starting units across 5 factions), and persists everything to the database.

**Request body:**

```json
{
  "player_assignments": {
    "japan": "Player 1",
    "usa": "Player 2"
  }
}
```

**Response:**

```json
{
  "session_id": "uuid",
  "game_id": "uuid",
  "player_assignments": { "japan": "Player 1", "usa": "Player 2" },
  "current_player": "japan",
  "current_phase": "setup",
  "current_round": 1
}
```

#### `GET /session/{session_id}`

Returns session metadata including game ID, player assignments, current phase/player/round, active status, and creation timestamp. Returns 404 if not found.

---

### Game

| Method | Path | Description |
|---|---|---|
| `GET` | `/game/{game_id}/state` | Full current game state |
| `GET` | `/game/{game_id}/events` | Event log (paginated) |
| `GET` | `/game/{game_id}/replay` | All snapshots + events for replay |
| `POST` | `/game/action/validate` | Validate an action without applying |
| `POST` | `/game/phase/advance` | Advance to next phase/player |

#### `POST /game/action/validate`

Validates whether a proposed action is legal under the current game state without modifying anything. Supports three action types:

**Move** — validates unit can reach target zone via BFS:

```json
{
  "game_id": "uuid",
  "player": "japan",
  "action_type": "move",
  "unit_id": "uuid",
  "to_zone": "kwangtung"
}
```

**Purchase** — validates IPC cost against player treasury:

```json
{
  "game_id": "uuid",
  "player": "japan",
  "action_type": "purchase",
  "purchases": [
    { "unit_type": "infantry", "count": 3 },
    { "unit_type": "fighter", "count": 1 }
  ]
}
```

**Placement** — validates against IC production capacity:

```json
{
  "game_id": "uuid",
  "player": "japan",
  "action_type": "place",
  "unit_type": "infantry",
  "to_zone": "japan"
}
```

**Response:**

```json
{
  "is_legal": true,
  "reason": "Purchase is valid",
  "total_cost": 12
}
```

#### `POST /game/phase/advance`

Advances the game to the next phase. Validates preconditions (e.g., all battles must be resolved before non-combat move). Persists a phase-advanced event and broadcasts via WebSocket.

**Request body:**

```json
{
  "game_id": "uuid",
  "session_id": "uuid",
  "actor": "operator_name"
}
```

**Response:**

```json
{
  "success": true,
  "new_phase": "combat_move",
  "new_player": "japan",
  "new_round": 1,
  "state_version": 3
}
```

#### `GET /game/{game_id}/events`

Returns the event log. Supports `limit` (default 100) and `offset` (default 0) query parameters.

#### `GET /game/{game_id}/replay`

Returns `{ "game_id", "snapshots": [...], "events": [...] }` — the full history for replaying a game.

---

### Combat

| Method | Path | Description |
|---|---|---|
| `POST` | `/combat/resolve` | Resolve a pending battle |

#### `POST /combat/resolve`

Resolves a pending battle using the HMAC-SHA256 CSPRNG. Applies casualties (cheapest-first), handles two-hit battleships, supports retreat, updates territory ownership on capture, persists a battle log, and broadcasts round-by-round results via WebSocket.

**Request body:**

```json
{
  "game_id": "uuid",
  "session_id": "uuid",
  "actor": "operator_name",
  "battle_id": "uuid",
  "casualty_policy": "cheapest_first",
  "retreat_after_round": null,
  "retreat_to_zone": null
}
```

**Response:**

```json
{
  "battle_id": "uuid",
  "status": "attacker_won",
  "rounds": 3,
  "attacker_losses": ["unit_id_1"],
  "defender_losses": ["unit_id_2", "unit_id_3"],
  "territory_captured": true,
  "rng_seed": "hex_seed_for_audit",
  "state_version": 5
}
```

---

### State

| Method | Path | Description |
|---|---|---|
| `POST` | `/state/commit` | Apply an approved delta to official state |

#### `POST /state/commit`

Applies zone/unit deltas to the official game state. Persists a state snapshot and event record, then broadcasts a WebSocket update.

**Request body:**

```json
{
  "game_id": "uuid",
  "session_id": "uuid",
  "actor": "operator_name",
  "phase": "combat_move",
  "delta": {
    "zones": {
      "kwangtung": { "owner": "japan" }
    },
    "units": {
      "unit_id": { "zone_id": "kwangtung", "status": "active" }
    }
  }
}
```

**Response:**

```json
{
  "success": true,
  "state_version": 6,
  "game_id": "uuid"
}
```

---

### Bot

| Method | Path | Description |
|---|---|---|
| `POST` | `/bot/suggest` | Get heuristic AI suggestions |

#### `POST /bot/suggest`

Returns ranked top-3 suggestions from the heuristic bot for the given player and phase. Each suggestion includes an action description, score breakdown (7 heuristic terms), and reasoning.

**Request body:**

```json
{
  "game_id": "uuid",
  "player": "japan",
  "phase": "purchase"
}
```

**Response:**

```json
{
  "game_id": "uuid",
  "player": "japan",
  "phase": "purchase",
  "suggestions": [
    {
      "rank": 1,
      "action": { "type": "purchase", "items": [...] },
      "score": 0.85,
      "score_breakdown": { ... },
      "reasoning": "Infantry-heavy purchase maximizes defensive IPC efficiency"
    }
  ]
}
```

---

### Correction

| Method | Path | Description |
|---|---|---|
| `POST` | `/correction/apply` | Apply manual correction or referee override |

#### `POST /correction/apply`

Two correction types:

- **`observation_correction`** — adjusts what CV reported without rules checks
- **`referee_override`** — patches official state directly; reason required

Can add/remove units and change zone ownership. Returns before/after snapshots for audit.

**Request body:**

```json
{
  "game_id": "uuid",
  "session_id": "uuid",
  "actor": "referee_name",
  "correction_type": "referee_override",
  "zone_id": "japan",
  "changes": {
    "owner": "japan",
    "add_units": { "infantry": 2 },
    "remove_units": ["unit_id_to_remove"]
  },
  "reason": "Correcting misplaced units"
}
```

**Response:**

```json
{
  "success": true,
  "correction_type": "referee_override",
  "state_version": 7,
  "before": { "zone_id": "japan", "owner": "japan", "ipc_value": 8, "unit_ids": [...] },
  "after": { "zone_id": "japan", "owner": "japan", "ipc_value": 8, "unit_ids": [...] }
}
```

---

### Vision

| Method | Path | Description |
|---|---|---|
| `POST` | `/vision/calibrate` | Trigger board calibration |
| `POST` | `/vision/observe-frame` | Process a camera frame |
| `POST` | `/vision/reconcile/propose` | Propose a state delta from observation |

#### `POST /vision/calibrate`

Triggers board calibration from the current camera frame using contour detection and homography computation. Records a calibration event on success.

#### `POST /vision/observe-frame`

Accepts a multipart file upload of a camera frame image. Runs YOLO detection, assigns detected units to zones, and returns detections with confidence scores. Query params: `game_id`, `session_id`.

#### `POST /vision/reconcile/propose`

Compares the latest CV observation against the official game state and proposes deltas. Flags ambiguities and splits results into auto-approve vs manual-review categories. Query params: `game_id`, `session_id`, `observation_id`.

> **Note:** All vision endpoints gracefully degrade when CV dependencies (trained model, camera) are not available, returning stub responses instead of errors.

---

## WebSocket Protocol

Connect to `ws://localhost:8000/ws/{game_id}` for real-time push updates.

### Connection

On connect, the server sends an acknowledgment:

```json
{
  "type": "connected",
  "game_id": "uuid",
  "current_player": "japan",
  "current_phase": "purchase",
  "state_version": 1
}
```

### Server-Pushed Message Types

| Type | Trigger | Description |
|---|---|---|
| `state_updated` | Any state mutation | Full or partial state update |
| `observation_frame` | New CV frame processed | Detection results from camera |
| `battle_progress` | During combat resolution | Round-by-round battle results |
| `phase_changed` | Phase advancement | New phase, player, and round |
| `correction_requested` | Reconciliation ambiguity | Operator review needed |
| `error` | Any server error | Error message for the client |

All messages are JSON with a `type` field. The frontend `useWebSocket` hook auto-parses these and triggers state refetches on `state_updated` messages.

---

## Game Concepts

### Factions (Player Order)

| # | Faction | Side |
|---|---|---|
| 1 | Japan | Axis |
| 2 | USA | Allies |
| 3 | UK Pacific | Allies |
| 4 | ANZAC | Allies |
| 5 | China | Allies |

### Turn Phases (Order)

| # | Phase | Description |
|---|---|---|
| 1 | `purchase` | Buy new units with IPC treasury |
| 2 | `combat_move` | Move units into enemy-occupied zones |
| 3 | `conduct_combat` | Resolve all battles |
| 4 | `non_combat_move` | Reposition remaining units |
| 5 | `mobilize_new_units` | Place purchased units at ICs |
| 6 | `collect_income` | Gain IPC from controlled territories |
| 7 | `turn_end` | End of turn; next player begins |

A `setup` phase precedes the first purchase phase.

### Unit Types

| Unit | Domain | Attack | Defense | Move | Cost |
|---|---|---|---|---|---|
| Infantry | Land | 1 | 2 | 1 | 3 |
| Artillery | Land | 2 | 2 | 1 | 4 |
| Armor | Land | 3 | 3 | 2 | 6 |
| Fighter | Air | 3 | 4 | 4 | 10 |
| Bomber | Air | 4 | 1 | 6 | 12 |
| Battleship | Sea | 4 | 4 | 2 | 20 |
| Carrier | Sea | 0 | 2 | 2 | 16 |
| Cruiser | Sea | 3 | 3 | 2 | 12 |
| Destroyer | Sea | 2 | 2 | 2 | 8 |
| Submarine | Sea | 2 | 1 | 2 | 6 |
| Transport | Sea | 0 | 0 | 2 | 7 |
| Industrial Complex | Facility | — | — | — | 15 |
| AA Gun | Facility | — | — | 1 | 5 |

### Victory Conditions

- **Japan wins** by controlling 6 of 9 victory cities at the end of a complete round
- **Allies win** if Japan's capital is captured

### Map

The canonical map (`data/map/pacific_1940_2e.json`) defines:

- 39 zones (land and sea)
- 9 victory cities
- Adjacency graph for movement BFS
- Starting unit placements for all 5 factions
- IPC values and industrial complex locations
- Unit costs and combat values

---

## Module Details

### game-schema

The canonical Pydantic models shared across all backend modules. Defines 12 enum types, the full `GameState` model tree (turn state, economy, zones, units, pending battles, audit metadata), 19 typed event models with a union discriminator, CV observation schemas, bot output schemas, and 6 WebSocket message types.

### rules-core

Pure rules logic with zero I/O dependencies. The phase machine handles turn/player rotation with precondition validation (e.g., all battles must be resolved before non-combat movement). Economy handles IPC purchases, income collection with capital-occupied checks, and China's special production rules. Movement validates land units via BFS reachability, air units with landing checks, naval units with sea-only paths, and transport capacity (2 units). Victory checks Japan's victory-city count against the threshold.

### battle-core

Pure combat logic with deterministic output. The CSPRNG uses HMAC-SHA256 to generate d6 dice rolls from a seed, ensuring identical replays. Resolution implements simultaneous fire, cheapest-first casualty selection, two-hit battleships, and retreat support. The Monte Carlo simulator runs 200 random battles to estimate win probability, expected losses, and IPC swing for pre-battle predictions.

### vision

Camera calibration finds board corners via contour detection and computes a homography matrix for perspective correction. The YOLO detector lazily loads the model, maps detection classes to `UnitType` enums, applies confidence banding, and assigns detections to zones. The zone mapper uses OpenCV `pointPolygonTest()` with fallback to nearest-centroid distance.

### reconciliation

Compares CV observations against the official game state. Produces proposed deltas, flags ambiguities (e.g., unit type uncertain), checks phase consistency (e.g., only losses expected during combat), and splits results into auto-approve (high confidence) and manual-review (requires operator confirmation) categories.

### bot

Five phase-specific heuristic advisors that each return ranked top-3 suggestions with score breakdowns across 7 heuristic terms:

| Phase | Strategy |
|---|---|
| Purchase | Infantry-heavy, mixed, or naval builds based on position |
| Combat Move | IPC gain vs. defender strength ratio |
| Combat Decision | Battle odds from Monte Carlo simulation |
| Non-Combat Move | Reposition units toward front lines |
| Placement | IC selection based on threat proximity |

---

## Design Decisions

| Principle | Implementation |
|---|---|
| CV never mutates official state | Three-tier state: `observed` -> `proposed` -> `official` |
| Rules engine is source of truth | All state changes validated by `packages/rules-core` |
| Deterministic combat | HMAC-SHA256 RNG seed + inputs = identical replay |
| Manual correction is first-class | Two types: observation correction and referee override |
| Event sourcing | Every change backed by a typed event in the database |
| Modular monolith | Single FastAPI process; modules separable later |
| Local-first development | SQLite by default, no external services needed |
| Graceful CV degradation | Vision endpoints return stubs when camera/model unavailable |

---

## V1 Playable Alpha

The V1 "playable alpha" runs a full game **manually without camera vision**:

1. Create a session via the Setup page (assign players to factions)
2. The rules engine initializes the canonical starting state (39 zones, ~138 units across 5 factions)
3. Use the operator console to advance phases and resolve combat
4. The bot advisor provides ranked top-3 suggestions per phase
5. All events are persisted and replayable via the replay endpoint
6. Manual corrections available at any time for setup errors

Phases 7–8 (vision + reconciliation) activate when a camera and trained detection model are connected.

---

## Smoke Tests

The smoke test suite (`scripts/dev/smoke_test.py`) runs 33 end-to-end checks against a running API instance:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python scripts/dev/smoke_test.py
```

### What it covers

| # | Area | Checks |
|---|---|---|
| 1 | Health check | `GET /health` returns status ok |
| 2 | Swagger docs | `GET /docs` loads and contains Swagger UI |
| 3 | OpenAPI schema | Route count >= 10 |
| 4 | Session creation | `POST /session/create` returns IDs, correct starting phase/player |
| 5 | Game state | Zones loaded, economy loaded, units placed, turn info correct |
| 6 | Session retrieval | `GET /session/{id}` returns 200 |
| 7 | Action validation | Purchase validation returns `is_legal` |
| 8 | Phase advancement | Setup -> purchase transition succeeds |
| 9 | Event log | At least 1 event after phase advance |
| 10 | Bot suggestions | Returns suggestions list |
| 11 | Correction | Referee override applied successfully |
| 12 | Replay | Returns events and snapshots |

The test expects the API to be running at `http://localhost:8000`.

---

## Implementation Status

### Fully Implemented

- **API**: 14 REST endpoints + WebSocket, async DB, in-memory state cache, event sourcing
- **Frontend**: Setup page, 3-column game page with 10 components, Zustand store, WebSocket hook, TanStack Query
- **game-schema**: 12 enums, full GameState model tree, 19 event types, observation + bot + WebSocket message schemas
- **rules-core**: Phase machine with turn/player rotation, purchase/income/production economy, land/air/naval movement with transport + carrier rules, victory conditions, map data loader with BFS adjacency
- **battle-core**: HMAC-SHA256 CSPRNG dice stream, full battle resolution (simultaneous fire, casualty selection, retreat, two-hit battleships), Monte Carlo simulation (200 runs)
- **bot**: 5 phase-specific heuristic advisors with scored ranked suggestions
- **Infrastructure**: Docker Compose stack, DB init script, smoke test suite (33 checks)

### Implemented — Needs External Assets

- **Vision pipeline** (`modules/vision/`): Calibration, YOLO detector, and zone mapper code is complete but requires a trained `models/detector.pt` model file and a connected camera
- **Zone polygons** in `pacific_1940_2e.json`: Placeholders (`[[0,0],...]`) — need real coordinates from board calibration
- **Reconciliation** (`modules/reconciliation/`): Observation-to-delta diffing is complete but depends on a working vision pipeline

### Not Yet Implemented

- **Unit / integration tests** — `pyproject.toml` references a `tests/` directory that does not exist
- **CI/CD** — no GitHub Actions or other pipeline configuration
- **Alembic migrations** — listed as a dependency but no migration files; DB uses `create_all`
- **Replay UI** — backend replay endpoint exists, no frontend component yet
- **Calibration wizard UI** — placeholder camera feed box only

---

## License

Apache 2.0 — see [LICENSE](LICENSE). Clean-room implementation — no TripleA GPL code or assets.
