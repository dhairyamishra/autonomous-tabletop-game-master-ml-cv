import React, { useState } from "react";
import type { GameState, PendingBattle, Player } from "../types";
import { resolveCombat } from "../api";

const PLAYER_COLORS: Record<Player, string> = {
  japan: "#c0392b",
  usa: "#2980b9",
  uk_pacific: "#27ae60",
  anzac: "#e67e22",
  china: "#f39c12",
};

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
    return null;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ fontWeight: 700, fontSize: 11, color: "#888", textTransform: "uppercase", letterSpacing: 0.5, padding: "0 2px" }}>
        Active Battles
      </div>
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

  const attackerColor = PLAYER_COLORS[battle.attacker];
  const defenderColor = PLAYER_COLORS[battle.defender];

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
    <div style={{
      background: "#16213e",
      borderRadius: 8,
      padding: 10,
      border: "1px solid #2a2a3e",
    }}>
      {/* Zone header */}
      <div style={{
        textAlign: "center",
        fontSize: 12,
        fontWeight: 600,
        color: "#ddd",
        marginBottom: 8,
        textTransform: "capitalize",
      }}>
        {battle.zone_id.replace(/_/g, " ")}
      </div>

      {/* Attacker vs Defender split */}
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{
          flex: 1,
          background: "#1a1a2e",
          borderRadius: 6,
          padding: 8,
          borderLeft: `3px solid ${attackerColor}`,
        }}>
          <div style={{ fontSize: 10, color: attackerColor, fontWeight: 700, marginBottom: 2 }}>
            {battle.attacker.toUpperCase().replace(/_/g, " ")}
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#fff" }}>
            {battle.attacking_units.length}
          </div>
          <div style={{ fontSize: 10, color: "#888" }}>units attacking</div>
        </div>

        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minWidth: 32,
        }}>
          <div style={{
            background: "#2a2a3e",
            borderRadius: 16,
            width: 28,
            height: 28,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 10,
            fontWeight: 700,
            color: "#666",
          }}>
            VS
          </div>
        </div>

        <div style={{
          flex: 1,
          background: "#1a1a2e",
          borderRadius: 6,
          padding: 8,
          borderRight: `3px solid ${defenderColor}`,
          textAlign: "right",
        }}>
          <div style={{ fontSize: 10, color: defenderColor, fontWeight: 700, marginBottom: 2 }}>
            {battle.defender.toUpperCase().replace(/_/g, " ")}
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#fff" }}>
            {battle.defending_units.length}
          </div>
          <div style={{ fontSize: 10, color: "#888" }}>units defending</div>
        </div>
      </div>

      {/* Controls */}
      {!result && (
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <input
            type="number"
            placeholder="Retreat after round..."
            value={retreatRound}
            onChange={(e) => setRetreatRound(e.target.value)}
            style={{
              flex: 1,
              padding: "4px 8px",
              fontSize: 11,
              background: "#1a1a2e",
              border: "1px solid #333",
              color: "#fff",
              borderRadius: 4,
              outline: "none",
            }}
          />
          <button
            onClick={handleResolve}
            disabled={loading}
            className="btn-primary"
            style={{
              padding: "5px 14px",
              background: "#e67e22",
              color: "#fff",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 11,
              fontWeight: 700,
              opacity: loading ? 0.5 : 1,
              whiteSpace: "nowrap",
            }}
          >
            {loading ? "Rolling..." : "Resolve"}
          </button>
        </div>
      )}

      {/* Result */}
      {result && (
        <div style={{
          padding: 8,
          background: "#0d1117",
          borderRadius: 6,
          border: "1px solid #2a2a3e",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ color: "#55efc4", fontWeight: 700, fontSize: 12 }}>
              {String(result.status).replace(/_/g, " ")}
            </span>
            <span style={{ color: "#888", fontSize: 10 }}>
              {String(result["rounds"] ?? 0)} round{Number(result["rounds"]) !== 1 ? "s" : ""}
            </span>
          </div>
          <div style={{ display: "flex", gap: 12, fontSize: 11, marginBottom: 4 }}>
            <span style={{ color: attackerColor }}>
              -{((result["attacker_losses"] as string[] | undefined) ?? []).length} attacker
            </span>
            <span style={{ color: defenderColor }}>
              -{((result["defender_losses"] as string[] | undefined) ?? []).length} defender
            </span>
          </div>
          {Boolean(result["territory_captured"]) && (
            <div style={{ color: "#f0c040", fontSize: 11, fontWeight: 600 }}>Territory captured</div>
          )}
          <div style={{ color: "#555", fontSize: 9, marginTop: 4 }}>
            RNG: <code>{String(result["rng_seed"] ?? "").slice(0, 16)}&hellip;</code>
          </div>
        </div>
      )}
    </div>
  );
}
