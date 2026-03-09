Full V1 Implementation Plan for the AI Agent
WW2 Pacific 2nd Edition Referee-First CV Web App

This plan is for a clean-room, web-native implementation of a tabletop assistant/referee for WW2 Pacific 1940 Second Edition, using a fixed overhead camera, manual correction, and server-side simulated dice. TripleA should be used as a behavioral reference and validation oracle, not as code or asset source. The official TripleA materials confirm that the WW2 Pacific map includes the Second Edition version and is intended to work according to the official rules; the TripleA rulebook also defines the standard phase sequence, and the "bot rules" page is about automated hosts in the lobby, not gameplay AI behavior.

Scope guidance: This is a multi-month project. Phases 1–6 (spec, schemas, rules engine, combat, API, and a basic frontend with manual-only input) constitute a "playable alpha" that can run a full game without any CV. That milestone should be the first target. Phases 7–8 layer on vision and reconciliation. Phases 9–11 add manual correction, the bot, and replay. Phases 12–15 cover evaluation, testing, deployment, and post-game analytics.

0. Project Goal

Build a full-stack application that:

reads a live overhead camera feed of a physical WW2 Pacific board

detects and tracks units on the board

maps detections into a canonical game state

acts as the authoritative referee

validates legal actions by phase

resolves combat with simulated server-side dice

offers simple bot suggestions

stores official game history for replay, analytics, and future learning

later supports memory retrieval and stronger AI

1. Hard Constraints to Lock

The agent must treat the following as fixed V1 requirements:

Scenario: WW2 Pacific 1940 Second Edition

Camera: fixed overhead only

Referee model: authoritative referee only

Manual correction: allowed and first-class

Dice: simulated on the server

Bot: simple advisor/opponent first, stronger later

Rules source: behavioral mirroring of public rules, not direct code reuse

Licensing posture: do not copy TripleA GPL code/assets/XML into the product without explicit approval; TripleA repositories and asset repositories are GPL-3.0 licensed.

2. Core Product Philosophy

The system must be built around four layers of truth:

Official game state

Official event log

Official combat RNG / dice history

Observed camera state as evidence only

Non-negotiable design rule

CV never directly mutates the official state.

The rules engine is the source of truth.

The frontend is an operator console.

The bot reasons only from the official committed state.

3. High-Level Architecture

Implement the app as a modular monolith with seven logical modules behind a single FastAPI process. These modules are cleanly separated in code so they can be extracted into independent services later if scaling requires it, but for V1 they share a single process and database.

frontend (React + TypeScript + Vite)

Responsibilities:

live board UI

calibration flow

overlays

manual correction

phase controls

combat screen

bot suggestions

replay screen

The frontend is a single-page React application built with TypeScript and Vite. It communicates with the backend via REST and WebSocket.

vision module

Responsibilities:

camera ingestion

board detection

homography / top-down rectification

object detection

tracking

zone assignment

confidence scoring

Camera architecture: V1 assumes the camera is physically connected to the server machine (USB webcam or local IP camera). The vision module captures frames server-side. Browser-based camera input is a V2 option.

OpenCV's homography tools are the right primitive for mapping the camera image into a stable top-down board coordinate system, and Ultralytics supports tracking on detect/segment models with BoT-SORT and ByteTrack.

reconciliation module

Responsibilities:

compare current observation with prior official state

produce a proposed state delta

flag ambiguity, occlusion, or impossible transitions

request user confirmation/correction

rules module

Responsibilities:

canonical game-state schema

move validation

phase machine

transport/carrier/battle/legality rules

purchase / placement validation

territory ownership / income / victory logic

combat module

Responsibilities:

simulated dice

battle round resolution

casualty application

retreat handling

battle logs

deterministic replay data

bot module

Responsibilities:

purchase suggestions

combat move ranking

non-combat move suggestions

simple heuristic planning

battle simulation-backed scoring

data module

Responsibilities:

PostgreSQL persistence

event store

replay history

analytics

4. Repo / Monorepo Layout

Use a single monorepo. The repository root is the project root.

apps/
  web/                    # React + TypeScript + Vite frontend
  api/                    # FastAPI backend (single process, all modules)
modules/
  vision/
  reconciliation/
  rules/
  combat/
  bot/
  data/
packages/
  game-schema/            # Pydantic models (canonical schemas, shared enums)
  rules-core/             # Pure game logic: move validation, phase machine, economy (no I/O)
  battle-core/            # Pure combat logic: dice, round resolution, casualty math (no I/O)
  logger/
infra/
  docker/                 # Dockerfiles, docker-compose.yml
docs/
  product-spec/
  api-contracts/
  state-machine/
  rules/
  test-plans/
data/
  map/                    # Canonical map geometry, adjacency, IPC values, starting units
  datasets/
  annotations/
  synthetic/
scripts/
  dev/
  migration/
  evaluation/

The packages/ directory contains pure logic libraries with no I/O, networking, or database access. rules-core/ holds move validation, phase machine, and economy logic. battle-core/ holds dice simulation, round resolution, and casualty math. The corresponding modules/ directories wire these core packages to the API routes, database, and external inputs (camera, WebSocket, etc.).

5. Step-by-Step Execution Plan
Phase 1 — Freeze the Product Spec
Task 1.1 — Create a V1 design document

Create docs/product-spec/v1-spec.md containing:

scenario scope

camera assumptions

supported phases

simulated dice policy

manual correction policy

non-goals

known open questions

acceptance criteria

Task 1.2 — Write explicit non-goals

V1 non-goals:

no arbitrary camera angles

no multi-map support

no direct physical dice recognition

no full RL/self-play training in live gameplay

no direct TripleA code import

no hidden autonomous state edits

no vector memory / RAG retrieval (deferred to V2)

no Kubernetes or Terraform infrastructure (Docker Compose only for V1)

Task 1.3 — Create rules reference notes

Create docs/rules/behavioral-spec.md summarizing only the rules behavior needed for implementation:

turn sequence

purchase

combat movement

conduct combat

non-combat movement

mobilize

collect income

map-specific constraints for WW2 Pacific 2nd Ed

TripleA's public rulebook documents the standard turn sequence and "Done" phase-advancement pattern; the tactical handbook also emphasizes concepts like area control and positional initiative, which are useful later for bot heuristics.

Done criteria

product spec exists

non-goals exist

rules behavior summary exists

all unresolved ambiguities are explicitly listed

Phase 2 — Define the Canonical Data Contracts
Task 2.1 — Define shared enums

Create packages/game-schema/src/enums.py as Pydantic-compatible Python enums.

Shared enums for:

player

phase

zone type

unit type

unit status

event type

battle status

correction type

observation confidence band

Task 2.2 — Define canonical state schema

Create packages/game-schema/src/game_state.py using Pydantic models.

The official state must include:

game_id

scenario

ruleset_version

players

round

current_player

phase

economy

zones

units

pending_battles

pending_actions

vision_reconciliation_status

audit

Required structure
{
  "game_id": "game_001",
  "scenario": "ww2_pacific_1940_2nd_edition",
  "dice_mode": "normal_simulated",
  "turn": {
    "round": 1,
    "current_player": "japan",
    "phase": "purchase"
  },
  "economy": {},
  "zones": {},
  "pending": {},
  "audit": {
    "state_version": 1
  }
}

Generate JSON Schema from Pydantic models for frontend TypeScript type generation. Use a tool such as pydantic-to-typescript or json-schema-to-typescript to keep backend and frontend types in sync from a single source of truth.

Task 2.3 — Define observation schema

Create packages/game-schema/src/observation.py using Pydantic models.

Observation must contain:

frame metadata

camera calibration status

board transform

detections

tracking IDs

per-detection confidence

candidate zone assignments

uncertainty flags

observation summary by zone

Task 2.4 — Define event schema

Create packages/game-schema/src/events.py using Pydantic models.

Required event types:

game_created

calibration_completed

observation_received

proposed_state_generated

manual_correction_applied

purchase_committed

move_committed

combat_declared

battle_started

battle_round_rolled

casualties_assigned

retreat_declared

battle_resolved

placement_committed

income_collected

phase_advanced

turn_ended

Task 2.5 — Define bot suggestion schema

Bot output must include:

ranked suggestions

action bundle

score

reasoning breakdown

confidence band

simulation summary where relevant

Task 2.6 — Define canonical map geometry

Create data/map/pacific_1940_2e.json containing:

territory and sea-zone definitions (name, type, IPC value)

adjacency graph (land-land, land-sea, sea-sea connections)

zone polygons in canonical board coordinates (for CV zone assignment)

starting unit placements per faction per zone

capital designations

canal/strait restrictions (if applicable)

This is foundational data required by the rules engine (adjacency, IPC values, starting setup), the vision module (zone polygons for detection-to-zone mapping), and the frontend (map rendering). Build it once in a single canonical file.

Task 2.7 — Define WebSocket message schema

Define the real-time protocol for push updates from server to frontend:

Required message types:

state_updated — new official state version pushed after commit

observation_frame — latest vision observation summary

battle_progress — live battle round updates during combat resolution

phase_changed — current phase/player advanced

correction_requested — vision flagged an ambiguity needing confirmation

error — server-side error or validation failure

Each message must include a type discriminator, a timestamp, and a session_id.

Done criteria

all schemas compile

schemas are versioned

Pydantic models generate valid JSON Schema

sample JSON fixtures exist

map geometry file exists with all territories, adjacencies, and starting units

WebSocket message types are defined

Phase 3 — Implement the Rules Engine First
Task 3.1 — Build the turn/phase state machine

Supported V1 phases:

setup (initial board state established from preset scenario or confirmed from camera)

purchase

combat_move

conduct_combat

non_combat_move

mobilize_new_units

collect_income

turn_end

The setup phase runs once at game start. It loads the canonical starting units from the map geometry data (Task 2.6) or allows the user to confirm/correct the initial board state from camera observation. After setup completes, play proceeds to the first player's purchase phase.

The standard TripleA rulebook defines a broader phase sequence, including technology development, purchase, combat movement, fight, movement without combat, mobilize, and end of turn / collect income. For V1, technology can remain disabled unless explicitly required.

Task 3.2 — Implement legal move validation

Implement move validators for:

unit movement capacity

land/sea movement restrictions

transport constraints

carrier/fighter landing constraints

attack eligibility

non-combat restrictions

placement legality

territory ownership and adjacency logic

Task 3.3 — Implement economy logic

Implement:

IPC collection

territory value changes

capture effects

purchase spend validation

placement availability

Task 3.4 — Implement battle declarations

When a player finishes combat_move, the engine must create pending battle objects from the committed move set.

Task 3.5 — Implement victory / end-game checks

Implement scenario-specific victory conditions and endgame evaluation hooks.

Done criteria

rules engine can run a full turn without CV

all phase transitions are validated

illegal actions are rejected with clear reasons

deterministic test fixtures pass

Phase 4 — Implement the Combat Service
Task 4.1 — Build the RNG model

Use server-side RNG only.

Store for each battle:

RNG algorithm version

seed or seed reference

ordered roll list

battle input hash

round logs

Task 4.2 — Implement battle round resolution

For each round:

gather eligible attacking units

gather eligible defending units

compute roll thresholds

simulate dice

compute hits

apply casualty selection flow

support retreat decision point where legal

continue until battle ends

Task 4.3 — Create battle log objects

Every combat round must generate structured event records.

Task 4.4 — Build replayable battle results

Combat resolution must be reproducible from:

committed state snapshot

battle choices

RNG stream

Done criteria

identical seed + state + choices produce identical results

battle logs are human-readable and machine-readable

replay endpoint can reconstruct battle history exactly

Phase 5 — Build the Backend Skeleton
Task 5.1 — Stand up the API app

Create apps/api with:

FastAPI Python API (single process hosting all modules)

REST endpoints

WebSocket support for live session updates

OpenAPI docs

Task 5.2 — Define session identity model

Implement a lightweight session-based player identity system. No full authentication is needed for V1.

Each game session tracks:

session ID

player-to-faction assignment (e.g., "Player 1 = Japan, Player 2 = USA/ANZAC")

active player indicator

This populates the actor field for corrections and audit records.

Task 5.3 — Create core endpoints

Required initial endpoints:

POST /session/create

POST /camera/calibrate

POST /vision/observe-frame

POST /reconcile/propose

POST /state/commit

POST /correction/apply

POST /action/validate

POST /phase/advance

POST /combat/resolve

POST /bot/suggest

GET /game/{id}/state

GET /game/{id}/events

GET /game/{id}/replay

Task 5.4 — Define WebSocket connection handling

Implement the WebSocket endpoint for live session updates using the message schema defined in Task 2.7.

Required behavior:

client connects with session_id

server pushes state_updated, observation_frame, battle_progress, phase_changed, correction_requested events in real time

client receives typed messages matching the WebSocket schema

Task 5.5 — Add persistence

Use PostgreSQL for:

official state snapshots

event log

battle logs

sessions and player assignments

game metadata

evaluation results

Done criteria

API boots locally

DB migrations run

schemas are stored

endpoints return typed responses

WebSocket connection delivers live updates

Phase 6 — Build the Frontend Operator Console
Task 6.1 — Build the live board screen

Required panels:

Left

live camera feed

overlays

raw/top-down toggle

confidence heatmap toggle

Center

official state

current player

current phase

round

economy summary

pending battles

pending confirmations

Right

detected units by zone

correction panel

legal actions

bot suggestions

event log

battle summary

Task 6.2 — Build the calibration wizard

Steps:

camera check

board found / not found

corner confirmation

zone overlay confirmation

calibration success

Task 6.3 — Build the manual correction panel

Correction must be zone-based first, not freehand drawing.

User can edit:

owner

unit type

count

status

note/reason

Task 6.4 — Build phase advancement controls

Buttons:

Confirm Observation

Commit Move

Resolve Battle

Done Phase

Undo Last Commit

Task 6.5 — Build combat UI

Show:

battle participants

combat values

each roll

hits

casualty choices

retreat choices

final result

"board needs update" reminder

Done criteria

full game can be operated from the web UI

official vs observed vs proposed state is visually distinct

battle flow is understandable to a non-developer tester

Phase 7 — Implement Vision and Board Calibration
Task 7.1 — Build calibration flow

Calibration must:

detect the physical board bounds

compute homography

rectify the image into a canonical top-down plane

lock a per-session board transform

Homography-based rectification is the correct tool for perspective normalization of a fixed overhead board camera.

Task 7.2 — Build unit detection

Train or continue training the detector for:

unit type

ownership/faction/color

position

confidence

Prefer instance segmentation if feasible, because overlapping ships and planes will be easier to separate than with boxes alone.

Ultralytics tracking supports detect and segment models and can run BoT-SORT or ByteTrack for tracked video streams.

Task 7.3 — Build tracking

Assign stable track IDs across frames.

Track-level outputs should include:

track ID

class

confidence

centroid

mask/bbox

zone candidates

occlusion flags

Task 7.4 — Build zone assignment

Every detection must be projected into the canonical top-down board and assigned to one or more candidate zones with scores. Zone polygons come from the canonical map geometry defined in Task 2.6.

Task 7.5 — Build uncertainty detection

Flag:

overlap

occlusion

low confidence class

unstable track

impossible count jump

multiple candidate zones

Done criteria

calibration works on a known tabletop setup

detector runs on live frames

detections project into zones

uncertainties are surfaced, not hidden

Phase 8 — Build the Reconciliation Layer
Task 8.1 — Implement observation-to-proposal conversion

Given:

latest observation

last official state

current phase

produce:

proposed zone deltas

suspicious mismatches

required confirmations

blocked transitions if needed

Task 8.2 — Implement delta-based movement inference

For movement phases, the system must infer zone deltas, not replace the whole board snapshot blindly.

Use:

previous official state

new observed state

movement legality constraints

current phase

unit movement history

Task 8.3 — Separate three concepts in code

Always keep separate:

observed_state

proposed_state

official_state

Task 8.4 — Add confidence gates

Low-confidence or impossible state changes must be routed to manual review.

Done criteria

a frame sequence can produce a proposed move delta

illegal or ambiguous deltas are blocked

official state changes only happen after validation + confirmation

Phase 9 — Implement Manual Correction as a First-Class Flow
Task 9.1 — Support two correction types
Observation correction

Use when the model misread the board.

Referee override

Use when the official state must be manually repaired.

These must be separate event types.

Task 9.2 — Require audit notes on referee overrides

Every override must capture:

actor (populated from session identity, Task 5.2)

before

after

reason

timestamp

Task 9.3 — Validate corrected states

Run corrected data back through the rules engine before final commit.

Done criteria

corrections are easy to perform

corrections are fully logged

illegal corrected states are rejected

Phase 10 — Implement the Simple Bot
Task 10.1 — Build a heuristic advisor first

Use a score made from:

territory/economic value

expected enemy value destroyed

expected own value lost

positional gain

capital safety

follow-up mobility

counterattack risk

The tactical handbook's emphasis on area control and initiative is a useful design anchor for these heuristic terms.

Task 10.2 — Use the same battle simulator as the referee

For candidate attacks:

enumerate legal attacks

simulate expected outcomes

rank plans

choose top-k

Task 10.3 — Split bot logic by phase

Implement phase-specific modules:

purchaseAdvisor

combatMoveAdvisor

combatDecisionAdvisor

nonCombatAdvisor

placementAdvisor

Task 10.4 — Return ranked candidate bundles

Do not return only one move. Return top 3 with reasons.

Task 10.5 — Defer strong learning-based play

Do not build RL into V1 gameplay. Long-term, a stronger policy/value + search approach can evolve toward an AlphaZero-style architecture, but that belongs after the rules engine, state logging, and self-play infrastructure exist.

Done criteria

bot suggestions are legal

suggestions are explainable

bot uses official state only

bot is battle-simulator-aware

Phase 11 — Add Persistence and Replay
Task 11.1 — Build event sourcing

Every meaningful state change must be event-backed.

Task 11.2 — Store state snapshots

Snapshot:

after each commit

after each battle resolution

at each phase end

at each turn end

Task 11.3 — Build replay

Replay must reconstruct:

state by version

events by timestamp

battle history

corrections

phase transitions

Done criteria

full games are replayable

event log can reconstruct any historical state

replay never mutates official state

V2 scope (deferred): Vector memory and similar-position retrieval via pgvector. Once enough clean game data exists, store embeddings for post-game summaries, tactical patterns, pivotal positions, human annotations, and similar-state descriptions. RAG/memory is for similar-position retrieval, post-game coaching, and explanations — it is not the source of truth for legality or state transitions.

Phase 12 — Build the CV Dataset and Evaluation Loop
Task 12.1 — Create annotation spec

Annotate:

piece type

owner

bbox or mask

zone

occlusion

stacked/overlapping status

lighting condition

frame source

Task 12.2 — Collect diverse board images

Must include:

clean boards

cluttered boards

hands in frame

partial occlusions

different lighting

various camera heights

real gameplay states

Task 12.3 — Build evaluation metrics

Track:

per-class detection quality

zone assignment accuracy

count accuracy

track stability

reconciliation error rate

manual correction rate per game

Task 12.4 — Build a calibration benchmark

Track:

board-finding success rate

corner accuracy

rectification stability

Done criteria

dataset versioning exists

metrics are reported per training run

regressions are catchable automatically

Phase 13 — Build End-to-End Acceptance Tests
Task 13.1 — Rules tests

Scenarios:

legal purchase

illegal purchase

valid combat move

illegal non-combat move

transport edge cases

carrier landing edge cases

battle resolution reproducibility

income updates

victory triggers

Task 13.2 — Vision tests

Scenarios:

piece detection

overlapping units

low light

board calibration loss

zone assignment

Task 13.3 — Reconciliation tests

Scenarios:

valid move inference

impossible move detection

missing unit correction

conflicting observation vs official state

Task 13.4 — UI tests

Scenarios:

full setup flow

phase advancement

battle resolution

manual correction

replay

Task 13.5 — Full-game dry run

Run a scripted game with:

camera feed

corrections

simulated battles

phase transitions

replay verification

Done criteria

one full game can be played and replayed end-to-end

official state remains internally consistent throughout

Phase 14 — Deployment and Ops
Task 14.1 — Containerize the application

Dockerize via docker-compose.yml:

API + all backend modules (single container)

PostgreSQL

Redis if needed

web app (frontend build served by nginx or similar)

Task 14.2 — Add model versioning

Store:

detector version

tracker config

calibration model version

bot version

rules version

Task 14.3 — Add observability

Capture:

request logs

inference latency

calibration failures

correction frequency

battle resolution timings

bot response timings

Task 14.4 — Add session persistence

Support:

resume game

save calibration per table/camera setup

export replay

Done criteria

local dev stack works via docker-compose

logs and metrics are visible

Phase 15 — Post-Game Analytics and Future Learning
Task 15.1 — Generate post-game summaries

Summaries should include:

winner

economy curve

decisive battles

major corrections

tactical mistakes

pivotal turns

Task 15.2 — Build similar-position retrieval (V2 prerequisite)

Given a current state, retrieve:

similar archived positions

what move was taken

final outcome

This depends on vector memory infrastructure deferred to V2.

Task 15.3 — Prepare for stronger bot training

Store clean training tuples:

official state

candidate actions

chosen action

battle outcomes

final result

Task 15.4 — Keep live learning disabled

Do not let the live system self-modify during active games.

6. Concrete V1 API Contract Summary
POST /vision/observe-frame

Input:

frame image or stream chunk

session ID

Output:

calibration status

detections

track IDs

candidate zones

uncertainties

POST /reconcile/propose

Input:

last official state

latest observation

current phase

Output:

proposed deltas

ambiguity flags

needed confirmations

POST /state/commit

Input:

approved delta or correction

actor (from session identity)

phase

Output:

new official state version

emitted events

POST /combat/resolve

Input:

battle ID

casualty policy

retreat policy

Output:

round-by-round dice results

casualties

winner

updated official state

POST /bot/suggest

Input:

official state

player

phase

Output:

ranked legal action bundles

scores

explanations

7. Minimum V1 Deliverables

The AI agent should not declare V1 complete until all of these are true:

one full game can be run on WW2 Pacific 2nd Edition

camera can calibrate and detect units from a fixed overhead setup

official state is separate from camera observations

rules engine validates moves and phase transitions

combat uses simulated server-side dice

battle logs are replayable

manual correction works at the zone/count level

bot provides legal ranked suggestions

full event log exists

replay works from start to finish

8. Implementation Order the Agent Must Follow

The coding order must be:

spec + contracts + map geometry

state schema + event schema + WebSocket schema (Pydantic models)

rules engine + phase machine (including setup phase)

combat service

API skeleton + persistence + session identity

frontend operator console (React + TypeScript + Vite)

vision calibration

vision detection + tracking

reconciliation

manual correction

bot suggestions

replay + persistence

evaluation + deployment

Do not start with the bot.
Do not start with RAG.
Do not let CV directly own game state.

9. Instructions to the AI Agent

Use this as the execution brief:

You are implementing V1 of a tabletop WW2 Pacific 1940 Second Edition referee-first web app.

Constraints:
- fixed overhead camera only (USB/local IP camera on server machine)
- authoritative referee only
- manual correction allowed
- simulated server-side dice
- simple heuristic bot first
- clean-room implementation only
- do not copy TripleA GPL code/assets/XML into product code
- use TripleA public rules/docs only as behavioral reference and validation oracle

Non-negotiable architecture:
- observed camera state != proposed state != official state
- rules engine is the source of truth
- event log is authoritative for replay
- bot reads official state only
- combat uses server-side RNG only
- all schemas are Pydantic models; JSON Schema is generated for frontend TypeScript types
- the backend is a modular monolith (single FastAPI process), not microservices

Build order:
1. Freeze specs, schemas, and map geometry
2. Implement canonical game state + event types + WebSocket schema (Pydantic)
3. Implement rules engine and phase machine (including setup phase)
4. Implement combat service with reproducible battle logs
5. Implement API + PostgreSQL persistence + session identity
6. Implement web operator console (React + TypeScript + Vite)
7. Implement camera calibration with homography/top-down rectification
8. Implement unit detection + tracking + zone assignment
9. Implement reconciliation layer
10. Implement manual correction flow
11. Implement simple bot suggestions
12. Implement replay + persistence
13. Implement evaluation, staging, and deployment

Definition of done:
- a full game can be played end-to-end
- all state transitions are auditable
- simulated battles are reproducible
- replay works
- CV ambiguity is surfaced rather than hidden
- manual correction is first-class

10. Final Engineering Notes

Treat TripleA as a behavioral reference, not a dependency.

Use OpenCV homography for board rectification and Ultralytics tracking for persistent piece identities.

Vector memory (pgvector) is deferred to V2. For V1, focus on clean event-sourced replay and structured game logs. Once enough clean official-state data exists, V2 can add embeddings for similar-position retrieval and post-game coaching.

Keep the learning loop offline until you have enough clean official-state data.

Build the replay system early; it will save enormous debugging time later.

The next strongest deliverable after this is a line-by-line technical spec for the canonical Pydantic models and endpoint request/response bodies.
