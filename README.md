# WW2 Pacific 1940 2nd Edition — Referee-First CV Web App

An autonomous tabletop game master for WW2 Pacific 1940 Second Edition.
Uses a fixed overhead camera, server-side simulated dice, a full rules engine,
and a simple heuristic bot — with the camera as evidence and the rules engine
as the authoritative source of truth.

---

## Architecture

```
apps/
  web/          React + TypeScript + Vite operator console
  api/          FastAPI modular monolith (single process)
modules/
  vision/       Camera calibration, unit detection, zone assignment
  reconciliation/ CV observation → proposed state delta
  bot/          Heuristic phase advisors
packages/
  game-schema/  Pydantic canonical models (enums, game state, events, etc.)
  rules-core/   Pure rules logic: movement, economy, phase machine, victory
  battle-core/  Pure combat logic: RNG, round resolution, simulation
infra/
  docker/       docker-compose.yml, Dockerfiles (optional containerised deploy)
data/
  map/          pacific_1940_2e.json — canonical map geometry
scripts/
  dev/          smoke_test.py, start_dev.ps1
  migration/    init_db.py
docs/
  product-spec/ v1-spec.md, non-goals.md
  rules/        behavioral-spec.md
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
2. The rules engine initializes the canonical starting state (70 zones, 138 units)
3. Use the operator console to advance phases and resolve combat
4. The bot advisor provides ranked suggestions per phase
5. All events are persisted and replayable

Phases 7–8 (vision + reconciliation) activate when a camera is connected.

---

## License

Apache 2.0. Clean-room implementation — no TripleA GPL code or assets.
