# WW2 Pacific 1940 Second Edition — Behavioral Rules Reference

This document summarizes only the game rules behaviors needed for implementation.
It is a clean-room behavioral description. Do not copy TripleA source code or XML.

---

## Turn Sequence

Each player takes a complete turn in order: Japan → USA → UK Pacific → ANZAC → China → (repeat)

One full cycle of all players completes one **round**.

A player's turn consists of the following phases in order:

1. **Setup** (game start only, not repeated)
2. **Purchase Units**
3. **Combat Move**
4. **Conduct Combat**
5. **Non-Combat Move**
6. **Mobilize New Units**
7. **Collect Income**
8. **Turn End**

---

## Setup Phase (Game Start Only)

- Load canonical starting unit placements from scenario data
- Each faction's starting units are placed in their designated territories and sea zones
- Starting IPC values are assigned per territory definitions
- Players confirm the initial board state (or the camera observation is used as evidence)
- Once confirmed, the setup phase completes and the first player begins their Purchase phase

---

## Purchase Units Phase

- Player has an IPC (Industrial Production Certificate) budget equal to their current treasury
- Player selects units to purchase; total cost must not exceed treasury
- Unit costs (approximate for Pacific 1940 2E):
  - Infantry: 3 IPC
  - Artillery: 4 IPC
  - Armor (Tank): 6 IPC
  - Fighter: 10 IPC
  - Bomber: 12 IPC
  - Battleship: 20 IPC
  - Aircraft Carrier: 16 IPC
  - Cruiser: 12 IPC
  - Destroyer: 8 IPC
  - Submarine: 6 IPC
  - Transport: 7 IPC
- Purchased units are held in a "to be placed" pool; they are not yet on the board
- Player may pass (spend 0 IPC)

---

## Combat Move Phase

- Player moves units that will conduct attacks this turn
- A unit that enters a territory or sea zone containing enemy units is declaring an attack
- Unit movement rules:
  - Infantry: 1 territory per turn
  - Artillery: 1 territory per turn
  - Armor: 2 territories per turn (blitz through empty enemy territory)
  - Fighter: 4 territories (must end turn on a carrier or friendly airfield)
  - Bomber: 6 territories
  - Battleship: 2 sea zones
  - Carrier: 2 sea zones
  - Cruiser: 2 sea zones
  - Destroyer: 2 sea zones
  - Submarine: 2 sea zones
  - Transport: 2 sea zones (cannot attack; carries land units)
- Units may not move through enemy-controlled territory (land units)
- Naval units may move through any sea zone not blocked by enemy fleet without submerging
- A unit committed to combat move cannot conduct non-combat move in the same turn

## Transport Rules

- Each transport carries a maximum of 2 infantry (or equivalent capacity)
- Loading and unloading in the same turn is permitted if the transport does not move after unloading
- Loaded units move with the transport
- Transports may not attack; they flee or are taken as casualties after all warships are removed

## Carrier / Fighter Landing Rules

- Fighters must be able to land on a friendly carrier or airfield at the end of their move
- A carrier must have open flight deck space (2 fighters per carrier)
- If a carrier is sunk during combat and its fighters cannot land elsewhere, the fighters are lost
- Fighters on a carrier move with the carrier

---

## Conduct Combat Phase

- All battles declared during Combat Move are resolved in this phase
- Player chooses the order to resolve multiple battles
- **Sea combat order**:
  1. Submarines fire (if not suppressed by destroyer)
  2. All other units fire simultaneously
  3. Casualties are removed
  4. Repeat until one side is eliminated or attacker retreats
- **Land combat**:
  1. All units fire simultaneously
  2. Casualties are removed
  3. Repeat until one side is eliminated or attacker retreats
- **Air in sea combat**: Fighters and bombers may participate in sea battles if they flew to the sea zone
- **Casualty selection**: Defender chooses which attacker casualties to take; attacker chooses which defender casualties. Each player must take cheapest units first (optional rule variant).
- **Retreat**: Attacker may retreat after any combat round, to any territory they moved from. Units retreat together.

## Combat Values (approximate Pacific 1940 2E)

| Unit | Attack | Defense |
|---|---|---|
| Infantry | 1 | 2 |
| Artillery | 2 | 2 |
| Armor | 3 | 3 |
| Fighter | 3 | 4 |
| Bomber | 4 | 1 |
| Battleship | 4 | 4 (2 hits) |
| Carrier | 1 | 2 |
| Cruiser | 3 | 3 |
| Destroyer | 2 | 2 |
| Submarine | 2 | 1 (can submerge) |
| Transport | 0 | 0 (taken last) |

A roll of 1–N on a 6-sided die is a hit, where N is the unit's combat value.

---

## Non-Combat Move Phase

- Player moves units that did not conduct a combat move this turn
- Same movement rules apply as Combat Move
- Units may not enter enemy-controlled territory unless it was captured this turn
- Fighters and bombers must end the phase on a carrier or friendly airfield

---

## Mobilize New Units Phase

- Purchased units are placed in controlled territories with an industrial complex (IC)
- Each territory with an IC has a production limit equal to its IPC value (units placed per turn)
- Units must be placed in a territory controlled by the player that has an IC
- Naval units are placed in a sea zone adjacent to the IC territory
- If an IC was captured this turn, it may not be used for placement until next turn

---

## Collect Income Phase

- Count all territories currently controlled by the player
- Add up the IPC values of all controlled territories
- Add IPC to treasury
- If the player's capital is occupied by an enemy, income collection is suspended

---

## Territory Ownership and Capture

- A territory is captured when the attacker wins a land combat in it
- Capturing a territory grants the attacker control and its IPC income
- Industrial complexes can be captured along with the territory (but not destroyed in Pacific 1940 2E unless otherwise specified)
- Sea zones are not "owned" — control shifts based on naval presence

---

## Victory Conditions (Pacific 1940 2E)

- **Japan wins** by controlling a specified number of Victory Cities simultaneously (typically 6 out of 9 in the Pacific region)
- **Allies win** by preventing Japan from reaching the victory threshold until a specified round, or by recapturing enough cities
- Exact victory city list and threshold to be defined in map geometry data

---

## Map-Specific Constraints (WW2 Pacific 1940 2E)

- **China**: China cannot build industrial complexes. China uses infantry and fighters only (basic version). Chinese units may only move within China and adjacent territories.
- **Kamikaze**: Japan has Kamikaze tokens (one-use attacks against naval units). Implementation deferred.
- **National Objectives**: Bonus IPC for controlling specific territory sets. Implementation deferred to V1.1.
- **Canals**: Panama Canal and Suez Canal restrict naval passage to the controlling power.
- **Neutral territories**: Some territories are neutral and cannot be entered. Others can be attacked.

---

## Phase Transition Rules

Each phase is completed by the active player signaling "Done." The system then:
1. Validates that all required actions are complete (e.g., all battles resolved before NCM)
2. Advances the phase state machine
3. Emits a `phase_advanced` event to the event log
4. Notifies the frontend via WebSocket
