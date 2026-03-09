import React, { useState } from "react";
import type { GameState } from "../types";
import { advancePhase } from "../api";

interface Props {
  gameState: GameState;
  sessionId: string;
  onAdvanced?: () => void;
}

export default function PhaseControls({ gameState, sessionId, onAdvanced }: Props) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleAdvance = async () => {
    setLoading(true);
    setMessage("");
    try {
      await advancePhase(gameState.game_id, sessionId, sessionId);
      setMessage("Phase advanced.");
      onAdvanced?.();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string };
      setMessage(`Error: ${err.response?.data?.detail ?? err.message ?? "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  const hasPendingBattles = Object.values(gameState.pending_battles).some(
    (b) => b.status === "pending" || b.status === "in_progress"
  );

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#aaa", marginBottom: 8 }}>PHASE CONTROLS</div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button
          onClick={handleAdvance}
          disabled={loading || (gameState.turn.phase === "conduct_combat" && hasPendingBattles)}
          title={
            gameState.turn.phase === "conduct_combat" && hasPendingBattles
              ? "Resolve all battles before advancing"
              : "Advance to next phase"
          }
          style={{
            padding: "6px 14px",
            background: "#0984e3",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
            fontWeight: 600,
            fontSize: 12,
            opacity: (loading || (gameState.turn.phase === "conduct_combat" && hasPendingBattles)) ? 0.5 : 1,
          }}
        >
          {loading ? "..." : "Done Phase ▶"}
        </button>
      </div>

      {gameState.turn.phase === "conduct_combat" && hasPendingBattles && (
        <div style={{ marginTop: 6, color: "#e17055", fontSize: 11 }}>
          ⚠ Resolve all pending battles before advancing.
        </div>
      )}

      {message && (
        <div style={{ marginTop: 6, fontSize: 12, color: message.startsWith("Error") ? "#e17055" : "#55efc4" }}>
          {message}
        </div>
      )}
    </div>
  );
}
