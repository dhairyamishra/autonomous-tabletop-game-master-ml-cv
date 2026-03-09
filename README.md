# WW2 Pacific 1940 2nd Edition — Referee-First CV Web App

An autonomous tabletop game master for WW2 Pacific 1940 Second Edition.
Uses a fixed overhead camera, server-side simulated dice, a full rules engine,
and a simple heuristic bot — with the camera as evidence and the rules engine
as the authoritative source of truth.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Backend API | FastAPI + Uvicorn | ≥ 0.111 |
| Data Models | Pydantic | ≥ 2.7 |
| ORM / Database | SQLAlchemy 2.0 (async), SQLite (default) / PostgreSQL | ≥ 2.0.30 |
| Frontend | React + TypeScript + Vite | React 19, Vite 7 |
| State Management | Zustand | 5.x |
| Data Fetching | TanStack Query + Axios | 5.x |
| Computer Vision | OpenCV + Ultralytics YOLO | ≥ 4.9, ≥ 8.2 |
| Combat RNG | HMAC-SHA256 CSPRNG | stdlib |
| Containerisation | Docker Compose (nginx + Python slim) | optional |

---

## Architecture

```
apps/
  api/                FastAPI modular monolith (single process)
    routes/           7 routers: session, game, combat, state, bot, correction, vision
  web/                React + TypeScript + Vite operator console
    src/
      components/     PhaseBar, BattlePanel, EconomyPanel, ZonePanel, BotPanel, etc.
      pages/          SetupPage, GamePage
      hooks/          useWebSocket
packages/
  game-schema/src/    Pydantic canonical models (enums, game state, events, observations, bot)
  rules-core/src/     Pure rules logic: phase machine, economy, movement, victory, map data
  battle-core/src/    Pure combat logic: CSPRNG RNG, round resolution, Monte Carlo simulation
modules/
  vision/             Camera calibration, YOLO unit detection, zone assignment
  reconciliation/     CV observation → proposed state delta
  bot/                Heuristic phase advisors (purchase, combat move, non-combat, placement)
infra/
  docker/             docker-compose.yml, Dockerfile.api, Dockerfile.web
data/
  map/                pacific_1940_2e.json — canonical map geometry
scripts/
  dev/                smoke_test.py, start_dev.ps1
  migration/          init_db.py
docs/
  product-spec/       v1-spec.md, non-goals.md
  rules/              behavioral-spec.md
```

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 20+

No Docker required — the app uses a local SQLite database by default.

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

- API: http://localhost:8000
- Docs: http://localhost:8000/docs (Swagger UI with all 15 routes)
- WebSocket: `ws://localhost:8000/ws/{game_id}`

### 4. Start the Frontend

```powershell
cd apps/web
npm install
npm run dev
```

- Frontend: http://localhost:5173

### 5. Verify

```powershell
python scripts/dev/smoke_test.py
```

Runs 33 end-to-end checks across all API endpoints.

---

## Switching to PostgreSQL

Set the `DATABASE_URL` environment variable before starting the API:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/referee_db"
```

The `JSON` column type used by SQLAlchemy works identically on both SQLite and PostgreSQL.

---

## Docker Stack (Optional)

```powershell
docker compose -f infra/docker/docker-compose.yml up --build
```

- Frontend: http://localhost:80
- API: http://localhost:8000

---

## Key Design Decisions

| Principle | Implementation |
|---|---|
| CV never mutates official state | `observed_state` ≠ `proposed_state` ≠ `official_state` |
| Rules engine is source of truth | All state changes validated by `packages/rules-core` |
| Deterministic combat | RNG seed + inputs → identical replay |
| Manual correction is first-class | Two correction types: observation correction and referee override |
| Event sourcing | Every change backed by a typed event in the database |
| Modular monolith | Single FastAPI process; modules separable later |
| Local-first development | SQLite by default, no external services needed |

---

## V1 Playable Alpha (Phases 1–6)

The "playable alpha" runs a full game manually without camera vision:
1. Create a session via the Setup page
2. The rules engine initializes the canonical starting state (39 zones, 138 units across 5 factions)
3. Use the operator console to advance phases and resolve combat
4. The bot advisor provides ranked top-3 suggestions per phase
5. All events are persisted and replayable

Phases 7–8 (vision + reconciliation) activate when a camera is connected.

---

## Implementation Status

### Fully implemented

- **API**: 15 REST endpoints + WebSocket, async DB, in-memory state cache, event sourcing
- **Frontend**: Setup page, 3-column game page with 8 components, Zustand store, WebSocket hook
- **game-schema**: 12 enums, full GameState model tree, 19 event types, observation + bot schemas
- **rules-core**: Phase machine with turn/player rotation, purchase/income, land/air/naval movement with transport + carrier rules, victory conditions, map data loader with BFS adjacency
- **battle-core**: CSPRNG dice stream, full battle resolution (simultaneous fire, casualty selection, retreat), Monte Carlo simulation (200 runs)
- **bot**: 5 phase-specific heuristic advisors with scored ranked suggestions
- **Infrastructure**: Docker Compose stack, DB init script, smoke test suite

### Implemented but needs external assets

- **Vision pipeline** (`modules/vision/`): calibration, YOLO detector, and zone mapper code is complete but requires a trained `models/detector.pt` model file and a connected camera
- **Zone polygons** in `pacific_1940_2e.json` are placeholders (`[[0,0],...]`) — need real coordinates from board calibration
- **Reconciliation** (`modules/reconciliation/`): observation-to-delta diffing is complete but depends on a working vision pipeline

### Not yet implemented

- **Unit / integration tests** — `pyproject.toml` references a `tests/` directory that does not exist
- **CI/CD** — no GitHub Actions or other pipeline configuration
- **Alembic migrations** — listed as a dependency but no migration files; DB uses `create_all`
- **Replay UI** — backend replay endpoint exists, no frontend component yet
- **Calibration wizard UI** — placeholder camera feed box only

---

## License

Apache 2.0. Clean-room implementation — no TripleA GPL code or assets.
