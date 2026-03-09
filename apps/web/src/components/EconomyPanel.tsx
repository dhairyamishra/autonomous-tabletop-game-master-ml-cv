import React from "react";
import type { Economy, Player } from "../types";

const PLAYER_LABELS: Record<Player, string> = {
  japan: "Japan",
  usa: "USA",
  uk_pacific: "UK Pacific",
  anzac: "ANZAC",
  china: "China",
};

interface Props {
  economy: Economy;
  currentPlayer: Player;
}

export default function EconomyPanel({ economy, currentPlayer }: Props) {
  const players: Player[] = ["japan", "usa", "uk_pacific", "anzac", "china"];

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#aaa", marginBottom: 8 }}>ECONOMY (IPC)</div>
      {players.map((p) => (
        <div
          key={p}
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: "4px 0",
            borderBottom: "1px solid #2a2a3e",
            fontWeight: p === currentPlayer ? 700 : 400,
            color: p === currentPlayer ? "#fff" : "#888",
          }}
        >
          <span>{PLAYER_LABELS[p]}</span>
          <span style={{ color: "#f0c040" }}>{economy.treasury[p] ?? 0} IPC</span>
        </div>
      ))}
    </div>
  );
}
