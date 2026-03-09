# V1 Product Specification
## WW2 Pacific 1940 Second Edition — Referee-First CV Web App

---

## Scenario Scope

- **Game**: Axis & Allies: Pacific 1940, Second Edition
- **Players**: Japan (Axis) vs USA, UK Pacific, ANZAC, China (Allies)
- **Map**: Fixed canonical map representing the Pacific theater, 1940
- **Factions in play**:
  - Japan (Axis)
  - United States (Allied)
  - United Kingdom Pacific (Allied)
  - ANZAC (Allied)
  - China (Allied, limited movement rules apply)

---

## Camera Assumptions

- Single fixed overhead camera mounted above the physical board
- Camera is connected directly to the server machine (USB webcam or local IP camera)
- Camera provides a continuous video stream processed server-side
- V1 assumes minimal perspective distortion (camera nearly perpendicular to board)
- Calibration is performed once per session before play begins
- Board boundaries are detected automatically and corrected by the operator if needed
- Browser-based camera input is a V2 option only

---

## Supported Phases (per player turn)

| Phase | Key | Description |
|---|---|---|
| Setup | `setup` | One-time initialization: load starting units from preset or camera |
| Purchase | `purchase` | Buy new units within IPC budget |
| Combat Move | `combat_move` | Move units that will attack enemy-occupied territories |
| Conduct Combat | `conduct_combat` | Resolve all declared battles |
| Non-Combat Move | `non_combat_move` | Move units that will not attack |
| Mobilize New Units | `mobilize_new_units` | Place purchased units in eligible territories |
| Collect Income | `collect_income` | Count controlled territories, receive IPC |
| Turn End | `turn_end` | Advance to next player |

Technology development is disabled in V1.

---

## Simulated Dice Policy

- All dice rolls are performed server-side using a CSPRNG (secrets module or equivalent)
- No client-side dice are permitted
- Every battle stores: RNG algorithm version, seed reference, ordered roll list, battle input hash
- Identical inputs (state snapshot + choices + RNG stream) must produce identical outcomes
- Dice results are displayed in the frontend after resolution; they cannot be pre-viewed
- Physical dice rolled by players are ignored — the system uses its own rolls

---

## Manual Correction Policy

- Two correction types are supported:
  1. **Observation correction**: corrects what the CV system misread (does not touch official state)
  2. **Referee override**: directly patches the official game state (audit logged, reason required)
- Corrections are zone-based (per territory/sea zone), not pixel-based
- Every referee override captures: actor, before-state, after-state, reason, timestamp
- Corrected states are validated by the rules engine before commit
- Correction history is stored in the event log and is replayable

---

## Non-Goals (V1)

See `non-goals.md` for the full list.

---

## Known Open Questions

1. Multi-faction Allied coordination: does each Allied player take a separate turn, or is it managed collectively? (Assume separate turns in order: Japan, USA, UK Pacific, ANZAC, China)
2. China rules: China has special production and movement restrictions. Full implementation TBD — implement basic version first.
3. Kamikaze attacks: Japan has Kamikaze tokens. Include in V1 or defer?
4. National objectives: bonus IPC for holding specific territory sets. Include in V1 or defer?
5. Canal rules: Suez and Panama canals affect naval movement. Include in V1.

---

## Acceptance Criteria

V1 is complete when all of the following are true:

- [ ] A full game can be run on WW2 Pacific 1940 2nd Edition
- [ ] Camera can calibrate and detect units from a fixed overhead setup
- [ ] Official state is always separate from camera observations
- [ ] Rules engine validates all moves and phase transitions
- [ ] Combat uses simulated server-side dice
- [ ] Battle logs are replayable (same seed → same outcome)
- [ ] Manual correction works at the zone/count level
- [ ] Bot provides legal ranked suggestions for each phase
- [ ] Full event log exists for every committed action
- [ ] Replay works from game start to game end
