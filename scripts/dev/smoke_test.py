"""End-to-end smoke test for the API."""
import httpx
import json
import sys

BASE = "http://localhost:8000"
results = []


def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, passed))
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail else ""))


print("=" * 60)
print("SMOKE TEST SUITE")
print("=" * 60)

# 1. Health check
print("\n1. Health check")
r = httpx.get(f"{BASE}/health")
check("GET /health status", r.status_code == 200, f"status={r.status_code}")
body = r.json()
check("Response has status=ok", body.get("status") == "ok", json.dumps(body))

# 2. Swagger docs
print("\n2. Swagger docs")
r = httpx.get(f"{BASE}/docs")
check("GET /docs loads", r.status_code == 200)
check("Contains Swagger UI", "swagger" in r.text.lower())

# 3. OpenAPI schema (count routes)
print("\n3. OpenAPI schema")
r = httpx.get(f"{BASE}/openapi.json")
check("GET /openapi.json status", r.status_code == 200)
schema = r.json()
paths = schema.get("paths", {})
route_count = sum(len(methods) for methods in paths.values())
check(f"Route count >= 10", route_count >= 10, f"found {route_count} routes across {len(paths)} paths")

# 4. Create session
print("\n4. Create session")
r = httpx.post(f"{BASE}/session/create", json={
    "player_assignments": {"japan": "Player 1", "usa": "Player 2"}
})
check("POST /session/create status", r.status_code == 200, f"status={r.status_code}")
session_data = r.json()
session_id = session_data.get("session_id", "")
game_id = session_data.get("game_id", "")
check("Response has session_id", bool(session_id), session_id[:12] + "...")
check("Response has game_id", bool(game_id), game_id[:12] + "...")
check("Current phase is setup", session_data.get("current_phase") == "setup")
check("Current player is japan", session_data.get("current_player") == "japan")

# 5. Get game state
print("\n5. Get game state")
r = httpx.get(f"{BASE}/game/{game_id}/state")
check("GET /game/state status", r.status_code == 200, f"status={r.status_code}")
state = r.json()

zones = state.get("zones", {})
check("Zones loaded", len(zones) > 0, f"{len(zones)} zones")

economy = state.get("economy", {})
check("Economy loaded", len(economy) > 0, f"players: {list(economy.keys())}")

total_units = sum(len(z.get("units", [])) for z in zones.values())
check("Units placed", total_units > 0, f"{total_units} total units")

turn = state.get("turn", {})
check("Turn has round", turn.get("round") == 1, f"round={turn.get('round')}")
check("Turn has phase", turn.get("phase") == "setup", f"phase={turn.get('phase')}")

# 6. Get session by ID
print("\n6. Get session by ID")
r = httpx.get(f"{BASE}/session/{session_id}")
check("GET /session/id status", r.status_code == 200, f"status={r.status_code}")

# 7. Validate an action (purchase)
print("\n7. Validate action (purchase)")
r = httpx.post(f"{BASE}/game/action/validate", json={
    "game_id": game_id,
    "player": "japan",
    "action_type": "purchase",
    "purchases": [{"unit_type": "infantry", "count": 1}],
})
check("POST /action/validate status", r.status_code == 200, f"status={r.status_code}")
if r.status_code == 200:
    vr = r.json()
    check("Validation returned is_legal", "is_legal" in vr, json.dumps(vr)[:200])

# 8. Phase advance (setup -> purchase)
print("\n8. Phase advance (setup -> purchase)")
r = httpx.post(f"{BASE}/game/phase/advance", json={
    "game_id": game_id,
    "session_id": session_id,
    "actor": "smoke_test",
})
check("POST /phase/advance status", r.status_code == 200, f"status={r.status_code}")
if r.status_code == 200:
    advance_data = r.json()
    check("Phase changed", advance_data.get("success") is True, json.dumps(advance_data)[:200])
    new_phase = advance_data.get("new_phase", "")
    check("New phase is purchase", new_phase == "purchase", f"new_phase={new_phase}")

# 9. Get events (should have 1 now)
print("\n9. Get events")
r = httpx.get(f"{BASE}/game/{game_id}/events")
check("GET /game/events status", r.status_code == 200, f"status={r.status_code}")
events = r.json()
check("Events is a list", isinstance(events, list), f"{len(events)} events")
check("At least 1 event after phase advance", len(events) >= 1)

# 10. Bot suggestions
print("\n10. Bot suggestions")
r = httpx.post(f"{BASE}/bot/suggest", json={
    "game_id": game_id,
    "player": "japan",
    "phase": "purchase",
})
check("POST /bot/suggest status", r.status_code == 200, f"status={r.status_code}")
if r.status_code == 200:
    bot = r.json()
    check("Bot returned suggestions list", "suggestions" in bot)

# 11. Correction apply (referee override)
print("\n11. Correction apply (referee override)")
r = httpx.post(f"{BASE}/correction/apply", json={
    "game_id": game_id,
    "session_id": session_id,
    "actor": "smoke_test",
    "correction_type": "referee_override",
    "zone_id": "japan",
    "changes": {"owner": "japan"},
    "reason": "smoke test verification",
})
check("POST /correction/apply status", r.status_code == 200, f"status={r.status_code}")
if r.status_code == 200:
    corr = r.json()
    check("Correction successful", corr.get("success") is True, json.dumps(corr)[:200])

# 12. Get replay
print("\n12. Replay endpoint")
r = httpx.get(f"{BASE}/game/{game_id}/replay")
check("GET /game/replay status", r.status_code == 200, f"status={r.status_code}")
if r.status_code == 200:
    replay = r.json()
    check("Replay has events", len(replay.get("events", [])) >= 1)
    check("Replay has snapshots", isinstance(replay.get("snapshots", []), list))

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, p in results if p)
failed = sum(1 for _, p in results if not p)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(results)} checks")
print("=" * 60)

if failed > 0:
    print("\nFailed checks:")
    for name, p in results:
        if not p:
            print(f"  - {name}")
    sys.exit(1)
else:
    print("\nAll checks passed!")
