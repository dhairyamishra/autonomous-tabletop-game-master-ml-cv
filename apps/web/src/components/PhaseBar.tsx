import React from "react";
import type { Phase, Player } from "../types";

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
}

export default function PhaseBar({ player, phase, round }: Props) {
  const phases: Phase[] = [
    "purchase", "combat_move", "conduct_combat",
    "non_combat_move", "mobilize_new_units", "collect_income",
  ];
  const color = PLAYER_COLORS[player];

  return (
    <div style={{ background: "#1a1a2e", padding: "8px 16px", display: "flex", alignItems: "center", gap: 16, borderBottom: "2px solid #333" }}>
      <div style={{ fontWeight: 700, fontSize: 14, color, textTransform: "uppercase" }}>
        {player.replace("_", " ")} — Round {round}
      </div>
      <div style={{ display: "flex", gap: 4, flex: 1 }}>
        {phases.map((p) => (
          <div
            key={p}
            style={{
              flex: 1,
              textAlign: "center",
              padding: "4px 6px",
              borderRadius: 4,
              fontSize: 11,
              fontWeight: p === phase ? 700 : 400,
              background: p === phase ? color : "#2a2a3e",
              color: p === phase ? "#fff" : "#888",
              border: p === phase ? `1px solid ${color}` : "1px solid #333",
              transition: "all 0.2s",
            }}
          >
            {PHASE_LABELS[p]}
          </div>
        ))}
      </div>
    </div>
  );
}
