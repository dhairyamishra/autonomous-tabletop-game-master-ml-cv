import React from "react";
import type { GameState, PendingBattle, Player, SimulationSummary } from "../types";

const PLAYER_COLORS: Record<Player, string> = {
  japan: "#c0392b",
  usa: "#2980b9",
  uk_pacific: "#27ae60",
  anzac: "#e67e22",
  china: "#f39c12",
};

const PLAYER_LABELS: Record<Player, string> = {
  japan: "JAPAN",
  usa: "USA",
  uk_pacific: "UK PACIFIC",
  anzac: "ANZAC",
  china: "CHINA",
};

const UNIT_ICONS: Record<string, string> = {
  infantry: "\u{1F6B6}",
  artillery: "\u{1F4A5}",
  armor: "\u{1F6E1}",
  fighter: "\u2708",
  bomber: "\u{1F4A3}",
  battleship: "\u{1F6A2}",
  carrier: "\u2693",
  cruiser: "\u{1F6A4}",
  destroyer: "\u{1F30A}",
  submarine: "\u{1F6E5}",
  transport: "\u{1F4E6}",
};

interface Props {
  gameState: GameState;
  simulationSummary: SimulationSummary | null;
}

export default function CombatPrediction({ gameState, simulationSummary }: Props) {
  const battles = Object.values(gameState.pending_battles).filter(
    (b) => b.status === "pending" || b.status === "in_progress"
  );

  if (battles.length === 0) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {battles.map((battle) => (
        <BattlePredictionCard
          key={battle.battle_id}
          battle={battle}
          gameState={gameState}
          simulationSummary={simulationSummary}
        />
      ))}
    </div>
  );
}

function BattlePredictionCard({
  battle,
  gameState,
  simulationSummary,
}: {
  battle: PendingBattle;
  gameState: GameState;
  simulationSummary: SimulationSummary | null;
}) {
  const attackerColor = PLAYER_COLORS[battle.attacker];
  const defenderColor = PLAYER_COLORS[battle.defender];

  const attackerUnits = countUnits(battle.attacking_units, gameState);
  const defenderUnits = countUnits(battle.defending_units, gameState);

  const attackerWinRate = simulationSummary
    ? simulationSummary.win_probability * 100
    : null;
  const defenderWinRate = attackerWinRate !== null ? 100 - attackerWinRate : null;

  return (
    <div style={{
      background: "#16213e",
      borderRadius: 10,
      padding: 12,
      border: "1px solid #2a2a3e",
    }}>
      <div style={{
        textAlign: "center",
        fontSize: 11,
        color: "#888",
        marginBottom: 8,
        textTransform: "capitalize",
      }}>
        {battle.zone_id.replace(/_/g, " ")}
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        {/* Attacker card */}
        <FactionCard
          player={battle.attacker}
          color={attackerColor}
          winRate={attackerWinRate}
          unitCounts={attackerUnits}
          role="ATK"
        />

        {/* VS divider */}
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minWidth: 40,
        }}>
          <div style={{
            background: "#2a2a3e",
            borderRadius: 20,
            width: 36,
            height: 36,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 12,
            fontWeight: 700,
            color: "#888",
          }}>
            VS
          </div>
        </div>

        {/* Defender card */}
        <FactionCard
          player={battle.defender}
          color={defenderColor}
          winRate={defenderWinRate}
          unitCounts={defenderUnits}
          role="DEF"
        />
      </div>
    </div>
  );
}

function FactionCard({
  player,
  color,
  winRate,
  unitCounts,
  role,
}: {
  player: Player;
  color: string;
  winRate: number | null;
  unitCounts: Record<string, number>;
  role: string;
}) {
  const totalUnits = Object.values(unitCounts).reduce((a, b) => a + b, 0);

  return (
    <div style={{
      flex: 1,
      background: "#1a1a2e",
      borderRadius: 8,
      padding: 10,
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
        <span style={{ color, fontWeight: 700, fontSize: 12 }}>
          {PLAYER_LABELS[player]}
        </span>
        <span style={{ color: "#555", fontSize: 10 }}>{role}</span>
      </div>

      {winRate !== null ? (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: "#fff", lineHeight: 1 }}>
            {winRate.toFixed(0)}%
          </div>
          <div style={{ fontSize: 10, color: "#888" }}>Win Rate</div>
        </div>
      ) : (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#555" }}>--</div>
          <div style={{ fontSize: 10, color: "#555" }}>No simulation</div>
        </div>
      )}

      <div style={{ fontSize: 11, color: "#aaa", marginBottom: 4 }}>
        {totalUnits} unit{totalUnits !== 1 ? "s" : ""}
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {Object.entries(unitCounts).map(([type, count]) => (
          <span key={type} style={{ fontSize: 11, color: "#888" }}>
            {UNIT_ICONS[type] ?? ""} {count}
          </span>
        ))}
      </div>
    </div>
  );
}

function countUnits(unitIds: string[], gameState: GameState): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const uid of unitIds) {
    const unit = gameState.units[uid];
    if (!unit) continue;
    counts[unit.unit_type] = (counts[unit.unit_type] ?? 0) + 1;
  }
  return counts;
}
