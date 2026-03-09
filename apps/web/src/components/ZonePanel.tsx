import React, { useState } from "react";
import type { GameState, Player, ZoneState, Unit } from "../types";

const AXIS_OWNERS: Player[] = ["japan"];
const ALLIED_OWNERS: Player[] = ["usa", "uk_pacific", "anzac", "china"];

interface Props {
  gameState: GameState;
  factionFilter: "axis" | "allies";
  onZoneSelect?: (zoneId: string) => void;
}

export default function ZonePanel({ gameState, factionFilter, onZoneSelect }: Props) {
  const [search, setSearch] = useState("");

  const factionPlayers = factionFilter === "axis" ? AXIS_OWNERS : ALLIED_OWNERS;

  const zones = Object.values(gameState.zones).filter((z) => {
    if (!z.owner || !factionPlayers.includes(z.owner)) return false;
    if (search && !z.zone_id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const totalUnits = zones.reduce(
    (sum, z) => sum + z.units.length, 0
  );

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 10, flex: 1, overflowY: "auto", minHeight: 0 }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 6,
      }}>
        <span style={{ fontWeight: 700, fontSize: 11, color: "#888", textTransform: "uppercase", letterSpacing: 0.5 }}>
          {factionFilter === "axis" ? "Axis Zones" : "Allied Zones"}
        </span>
        <span style={{ fontSize: 10, color: "#55efc4" }}>
          {zones.length} zones &middot; {totalUnits} units
        </span>
      </div>
      <input
        placeholder="Search zone..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{
          width: "100%",
          marginBottom: 6,
          padding: "4px 8px",
          background: "#1a1a2e",
          border: "1px solid #333",
          color: "#fff",
          borderRadius: 4,
          fontSize: 11,
          outline: "none",
        }}
      />
      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
        {zones.slice(0, 50).map((zone) => (
          <ZoneRow
            key={zone.zone_id}
            zone={zone}
            units={zone.units.map((uid) => gameState.units[uid]).filter(Boolean)}
            onClick={() => onZoneSelect?.(zone.zone_id)}
          />
        ))}
        {zones.length === 0 && (
          <div style={{ color: "#555", fontSize: 11, padding: 8, textAlign: "center" }}>
            No zones found.
          </div>
        )}
      </div>
    </div>
  );
}

function ZoneRow({ zone, units, onClick }: { zone: ZoneState; units: Unit[]; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      className="zone-row"
      style={{
        padding: "5px 7px",
        borderRadius: 4,
        background: "#1a1a2e",
        cursor: "pointer",
        border: "1px solid transparent",
        transition: "border-color 0.15s, background 0.15s",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontWeight: 600, color: "#ddd" }}>
        <span style={{ textTransform: "capitalize" }}>{zone.zone_id.replace(/_/g, " ")}</span>
        <span style={{ color: "#f0c040", fontSize: 10 }}>
          {zone.ipc_value > 0 ? `${zone.ipc_value} IPC` : ""}
        </span>
      </div>
      <div style={{ fontSize: 10, color: "#888", marginTop: 1, display: "flex", gap: 6 }}>
        {zone.has_industrial_complex && <span style={{ color: "#74b9ff" }}>IC</span>}
        {zone.is_victory_city && <span style={{ color: "#fd79a8" }}>&#9733;</span>}
        {units.length > 0 && (
          <span style={{ color: "#55efc4" }}>
            {units.length} unit{units.length > 1 ? "s" : ""}
          </span>
        )}
      </div>
    </div>
  );
}
