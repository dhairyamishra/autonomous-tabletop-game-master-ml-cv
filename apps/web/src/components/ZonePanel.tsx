import React, { useState } from "react";
import type { GameState, Player, ZoneState, Unit } from "../types";

interface Props {
  gameState: GameState;
  onZoneSelect?: (zoneId: string) => void;
}

export default function ZonePanel({ gameState, onZoneSelect }: Props) {
  const [filter, setFilter] = useState<Player | "all">("all");
  const [search, setSearch] = useState("");

  const zones = Object.values(gameState.zones).filter((z) => {
    if (filter !== "all" && z.owner !== filter) return false;
    if (search && !z.zone_id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 12, height: "100%", overflowY: "auto" }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#aaa", marginBottom: 8 }}>ZONES</div>
      <input
        placeholder="Search zone..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ width: "100%", marginBottom: 8, padding: "4px 8px", background: "#1a1a2e", border: "1px solid #444", color: "#fff", borderRadius: 4, fontSize: 12 }}
      />
      <div style={{ display: "flex", gap: 4, marginBottom: 8, flexWrap: "wrap" }}>
        {(["all", "japan", "usa", "uk_pacific", "anzac", "china"] as const).map((p) => (
          <button
            key={p}
            onClick={() => setFilter(p)}
            style={{
              padding: "2px 6px",
              fontSize: 11,
              borderRadius: 3,
              border: "none",
              cursor: "pointer",
              background: filter === p ? "#3a3a5e" : "#2a2a3e",
              color: filter === p ? "#fff" : "#888",
            }}
          >
            {p === "all" ? "All" : p}
          </button>
        ))}
      </div>
      {zones.slice(0, 40).map((zone) => (
        <ZoneRow
          key={zone.zone_id}
          zone={zone}
          units={zone.units.map((uid) => gameState.units[uid]).filter(Boolean)}
          onClick={() => onZoneSelect?.(zone.zone_id)}
        />
      ))}
    </div>
  );
}

function ZoneRow({ zone, units, onClick }: { zone: ZoneState; units: Unit[]; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      style={{
        padding: "6px 8px",
        marginBottom: 4,
        borderRadius: 4,
        background: "#1a1a2e",
        cursor: "pointer",
        border: "1px solid #2a2a3e",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, fontWeight: 600, color: "#ddd" }}>
        <span style={{ textTransform: "capitalize" }}>{zone.zone_id.replace(/_/g, " ")}</span>
        <span style={{ color: "#f0c040" }}>{zone.ipc_value > 0 ? `${zone.ipc_value} IPC` : ""}</span>
      </div>
      <div style={{ fontSize: 11, color: "#888", marginTop: 2 }}>
        {zone.owner ? <span style={{ color: "#aaa" }}>{zone.owner}</span> : <span>Neutral</span>}
        {zone.has_industrial_complex && <span style={{ marginLeft: 6, color: "#74b9ff" }}>IC</span>}
        {zone.is_victory_city && <span style={{ marginLeft: 6, color: "#fd79a8" }}>★</span>}
        {units.length > 0 && (
          <span style={{ marginLeft: 8, color: "#55efc4" }}>
            {units.length} unit{units.length > 1 ? "s" : ""}
          </span>
        )}
      </div>
    </div>
  );
}
