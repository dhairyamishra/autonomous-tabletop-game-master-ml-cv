import React, { useState } from "react";
import type { GameState, PendingBattle } from "../types";
import { resolveCombat } from "../api";

interface Props {
  gameState: GameState;
  sessionId: string;
  onResolved?: () => void;
}

export default function BattlePanel({ gameState, sessionId, onResolved }: Props) {
  const battles = Object.values(gameState.pending_battles).filter(
    (b) => b.status === "pending" || b.status === "in_progress"
  );

  if (battles.length === 0) {
    return (
      <div style={{ background: "#16213e", borderRadius: 8, padding: 12 }}>
        <div style={{ color: "#888", fontSize: 13 }}>No pending battles.</div>
      </div>
    );
  }

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#aaa", marginBottom: 8 }}>PENDING BATTLES</div>
      {battles.map((battle) => (
        <BattleCard
          key={battle.battle_id}
          battle={battle}
          gameState={gameState}
          sessionId={sessionId}
          onResolved={onResolved}
        />
      ))}
    </div>
  );
}

function BattleCard({
  battle, gameState, sessionId, onResolved,
}: {
  battle: PendingBattle;
  gameState: GameState;
  sessionId: string;
  onResolved?: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [retreatRound, setRetreatRound] = useState<string>("");

  const handleResolve = async () => {
    setLoading(true);
    try {
      const res = await resolveCombat({
        game_id: gameState.game_id,
        session_id: sessionId,
        actor: sessionId,
        battle_id: battle.battle_id,
        retreat_after_round: retreatRound ? parseInt(retreatRound) : undefined,
      });
      setResult(res as Record<string, unknown>);
      onResolved?.();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: "#1a1a2e", borderRadius: 6, padding: 10, marginBottom: 8, border: "1px solid #444" }}>
      <div style={{ fontWeight: 600, color: "#fff", fontSize: 13 }}>
        Battle: {battle.zone_id.replace(/_/g, " ")}
      </div>
      <div style={{ fontSize: 12, color: "#aaa", margin: "4px 0" }}>
        <span style={{ color: "#c0392b" }}>{battle.attacker}</span>
        {" vs "}
        <span style={{ color: "#2980b9" }}>{battle.defender}</span>
      </div>
      <div style={{ fontSize: 11, color: "#888" }}>
        Attackers: {battle.attacking_units.length} units &nbsp;|&nbsp;
        Defenders: {battle.defending_units.length} units
      </div>

      {!result && (
        <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="number"
            placeholder="Retreat after round #"
            value={retreatRound}
            onChange={(e) => setRetreatRound(e.target.value)}
            style={{ padding: "3px 6px", fontSize: 12, width: 140, background: "#2a2a3e", border: "1px solid #555", color: "#fff", borderRadius: 4 }}
          />
          <button
            onClick={handleResolve}
            disabled={loading}
            style={{ padding: "4px 14px", background: "#c0392b", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 12, fontWeight: 600 }}
          >
            {loading ? "Rolling..." : "Resolve Battle"}
          </button>
        </div>
      )}

      {result && (
        <div style={{ marginTop: 8, padding: 8, background: "#0d1117", borderRadius: 4, fontSize: 12 }}>
          <div style={{ color: "#55efc4", fontWeight: 700 }}>
            Result: {String(result.status).replace(/_/g, " ")}
          </div>
          <div style={{ color: "#aaa" }}>Rounds fought: {String(result["rounds"] ?? 0)}</div>
          <div style={{ color: "#c0392b" }}>Attacker losses: {((result["attacker_losses"] as string[] | undefined) ?? []).length}</div>
          <div style={{ color: "#2980b9" }}>Defender losses: {((result["defender_losses"] as string[] | undefined) ?? []).length}</div>
          {Boolean(result["territory_captured"]) && (
            <div style={{ color: "#f0c040" }}>Territory captured!</div>
          )}
          <div style={{ color: "#888", marginTop: 4 }}>
            RNG seed: <code style={{ fontSize: 10 }}>{String(result["rng_seed"] ?? "").slice(0, 16)}…</code>
          </div>
          <div style={{ color: "#666", fontSize: 11, marginTop: 2 }}>
            Update physical board to match result.
          </div>
        </div>
      )}
    </div>
  );
}
