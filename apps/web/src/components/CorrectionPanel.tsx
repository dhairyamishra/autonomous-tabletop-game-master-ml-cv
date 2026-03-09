import React, { useState } from "react";
import type { GameState, Player, UnitType } from "../types";
import { applyCorrection } from "../api";

interface Props {
  gameState: GameState;
  sessionId: string;
  onCorrected?: () => void;
}

const UNIT_TYPES: UnitType[] = [
  "infantry", "artillery", "armor", "fighter", "bomber",
  "battleship", "carrier", "cruiser", "destroyer", "submarine", "transport",
];

const PLAYERS: Player[] = ["japan", "usa", "uk_pacific", "anzac", "china"];

export default function CorrectionPanel({ gameState, sessionId, onCorrected }: Props) {
  const [selectedZone, setSelectedZone] = useState("");
  const [correctionType, setCorrectionType] = useState<"observation_correction" | "referee_override">(
    "observation_correction"
  );
  const [owner, setOwner] = useState<Player | "">("");
  const [addUnitType, setAddUnitType] = useState<UnitType>("infantry");
  const [addCount, setAddCount] = useState(1);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");

  const zoneIds = Object.keys(gameState.zones).sort();

  const handleSubmit = async () => {
    if (!selectedZone) { setMessage("Select a zone."); return; }
    if (correctionType === "referee_override" && !reason) { setMessage("Referee overrides require a reason."); return; }

    const changes: Record<string, unknown> = {};
    if (owner) changes.owner = owner;
    if (addCount > 0) changes.add_units = { [addUnitType]: addCount };

    try {
      await applyCorrection({
        game_id: gameState.game_id,
        session_id: sessionId,
        actor: sessionId,
        correction_type: correctionType,
        zone_id: selectedZone,
        changes,
        reason,
      });
      setMessage("Correction applied.");
      onCorrected?.();
    } catch (e: unknown) {
      setMessage(`Error: ${(e as Error).message}`);
    }
  };

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#aaa", marginBottom: 8 }}>MANUAL CORRECTION</div>

      <label style={labelStyle}>Correction Type</label>
      <select value={correctionType} onChange={(e) => setCorrectionType(e.target.value as typeof correctionType)} style={inputStyle}>
        <option value="observation_correction">Observation Correction (CV misread)</option>
        <option value="referee_override">Referee Override (patch official state)</option>
      </select>

      <label style={labelStyle}>Zone</label>
      <select value={selectedZone} onChange={(e) => setSelectedZone(e.target.value)} style={inputStyle}>
        <option value="">-- Select zone --</option>
        {zoneIds.map((z) => (
          <option key={z} value={z}>{z.replace(/_/g, " ")}</option>
        ))}
      </select>

      <label style={labelStyle}>Change Owner (optional)</label>
      <select value={owner} onChange={(e) => setOwner(e.target.value as Player | "")} style={inputStyle}>
        <option value="">-- No change --</option>
        {PLAYERS.map((p) => <option key={p} value={p}>{p}</option>)}
      </select>

      <label style={labelStyle}>Add Units</label>
      <div style={{ display: "flex", gap: 8 }}>
        <select value={addUnitType} onChange={(e) => setAddUnitType(e.target.value as UnitType)} style={{ ...inputStyle, flex: 2 }}>
          {UNIT_TYPES.map((u) => <option key={u} value={u}>{u}</option>)}
        </select>
        <input
          type="number"
          min={0}
          max={20}
          value={addCount}
          onChange={(e) => setAddCount(parseInt(e.target.value) || 0)}
          style={{ ...inputStyle, flex: 1, width: 60 }}
        />
      </div>

      <label style={labelStyle}>Reason {correctionType === "referee_override" ? "(required)" : "(optional)"}</label>
      <input
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        placeholder="Describe why this correction is needed"
        style={inputStyle}
      />

      <button onClick={handleSubmit} style={{ marginTop: 8, padding: "6px 14px", background: "#6c5ce7", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontWeight: 600, fontSize: 12 }}>
        Apply Correction
      </button>

      {message && <div style={{ marginTop: 8, color: "#55efc4", fontSize: 12 }}>{message}</div>}
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: 11,
  color: "#888",
  marginTop: 6,
  marginBottom: 2,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "4px 8px",
  background: "#1a1a2e",
  border: "1px solid #444",
  color: "#fff",
  borderRadius: 4,
  fontSize: 12,
};
