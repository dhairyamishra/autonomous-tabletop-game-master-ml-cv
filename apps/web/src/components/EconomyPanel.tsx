import React from "react";
import type { Economy, Player } from "../types";

const PLAYER_LABELS: Record<Player, string> = {
  japan: "Japan",
  usa: "USA",
  uk_pacific: "UK Pacific",
  anzac: "ANZAC",
  china: "China",
};

const PLAYER_COLORS: Record<Player, string> = {
  japan: "#c0392b",
  usa: "#2980b9",
  uk_pacific: "#27ae60",
  anzac: "#e67e22",
  china: "#f39c12",
};

const AXIS_PLAYERS: Player[] = ["japan"];
const ALLIED_PLAYERS: Player[] = ["usa", "uk_pacific", "anzac", "china"];

interface Props {
  economy: Economy;
  currentPlayer: Player;
  side: "axis" | "allies";
}

export default function EconomyPanel({ economy, currentPlayer, side }: Props) {
  const players = side === "axis" ? AXIS_PLAYERS : ALLIED_PLAYERS;
  const totalIpc = players.reduce((sum, p) => sum + (economy.treasury[p] ?? 0), 0);

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 10 }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 6,
      }}>
        <span style={{ fontWeight: 700, fontSize: 11, color: "#888", textTransform: "uppercase", letterSpacing: 0.5 }}>
          {side === "axis" ? "Axis Economy" : "Allied Economy"}
        </span>
        <span style={{ fontSize: 11, color: "#f0c040", fontWeight: 600 }}>{totalIpc} IPC</span>
      </div>
      {players.map((p) => {
        const isCurrent = p === currentPlayer;
        return (
          <div
            key={p}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "5px 6px",
              borderRadius: 4,
              marginBottom: 2,
              background: isCurrent ? "rgba(255,255,255,0.04)" : "transparent",
              borderLeft: `3px solid ${isCurrent ? PLAYER_COLORS[p] : "transparent"}`,
            }}
          >
            <span style={{
              fontSize: 12,
              fontWeight: isCurrent ? 700 : 400,
              color: isCurrent ? "#fff" : "#999",
            }}>
              {PLAYER_LABELS[p]}
            </span>
            <span style={{ color: "#f0c040", fontSize: 12, fontWeight: 600 }}>
              {economy.treasury[p] ?? 0}
            </span>
          </div>
        );
      })}
    </div>
  );
}
