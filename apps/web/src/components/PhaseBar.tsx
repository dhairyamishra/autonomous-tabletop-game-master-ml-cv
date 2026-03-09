import React from "react";
import type { Phase, Player, VictoryStatus } from "../types";

const PHASE_LABELS: Record<Phase, string> = {
  setup: "Setup",
  purchase: "Purchase",
  combat_move: "Combat Move",
  conduct_combat: "Conduct Combat",
  non_combat_move: "Non-Combat Move",
  mobilize_new_units: "Mobilize",
  collect_income: "Collect Income",
  turn_end: "Turn End",
};

const PLAYER_COLORS: Record<Player, string> = {
  japan: "#c0392b",
  usa: "#2980b9",
  uk_pacific: "#27ae60",
  anzac: "#e67e22",
  china: "#f39c12",
};

interface Props {
  player: Player;
  phase: Phase;
  round: number;
  stateVersion: number;
  wsConnected: boolean;
  victoryStatus: VictoryStatus;
  pendingBattleCount: number;
}

export default function PhaseBar({
  player, phase, round, stateVersion, wsConnected, victoryStatus, pendingBattleCount,
}: Props) {
  const phases: Phase[] = [
    "purchase", "combat_move", "conduct_combat",
    "non_combat_move", "mobilize_new_units", "collect_income",
  ];
  const color = PLAYER_COLORS[player];

  return (
    <div style={{
      background: "#1a1a2e",
      padding: "6px 16px",
      display: "flex",
      alignItems: "center",
      gap: 12,
      borderBottom: "1px solid #2a2a3e",
      flexShrink: 0,
    }}>
      {/* Player + round */}
      <div style={{ fontWeight: 700, fontSize: 13, color, textTransform: "uppercase", whiteSpace: "nowrap" }}>
        {player.replace(/_/g, " ")} &mdash; R{round}
      </div>

      {/* Phase chips */}
      <div style={{ display: "flex", gap: 3, flex: 1 }}>
        {phases.map((p) => (
          <div
            key={p}
            style={{
              flex: 1,
              textAlign: "center",
              padding: "3px 4px",
              borderRadius: 4,
              fontSize: 10,
              fontWeight: p === phase ? 700 : 400,
              background: p === phase ? color : "#2a2a3e",
              color: p === phase ? "#fff" : "#666",
              border: p === phase ? `1px solid ${color}` : "1px solid transparent",
              transition: "all 0.2s",
            }}
          >
            {PHASE_LABELS[p]}
          </div>
        ))}
      </div>

      {/* Status cluster */}
      <div style={{ display: "flex", gap: 10, alignItems: "center", whiteSpace: "nowrap" }}>
        {pendingBattleCount > 0 && (
          <span style={{ color: "#e17055", fontSize: 11, fontWeight: 600 }}>
            {pendingBattleCount} battle{pendingBattleCount > 1 ? "s" : ""}
          </span>
        )}
        {victoryStatus !== "in_progress" && (
          <span style={{ color: "#f0c040", fontWeight: 700, fontSize: 12 }}>
            {victoryStatus === "japan_wins" ? "Japan Wins" : "Allies Win"}
          </span>
        )}
        <span style={{ color: "#555", fontSize: 10 }}>v{stateVersion}</span>
        <span style={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          background: wsConnected ? "#55efc4" : "#e17055",
          display: "inline-block",
          boxShadow: wsConnected ? "0 0 6px #55efc4" : "none",
        }} />
      </div>
    </div>
  );
}
