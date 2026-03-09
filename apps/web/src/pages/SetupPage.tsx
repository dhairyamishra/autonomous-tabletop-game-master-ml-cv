import React, { useState } from "react";
import { createSession } from "../api";
import { useAppStore } from "../store";
import type { Player } from "../types";

const PLAYERS: { faction: Player; label: string }[] = [
  { faction: "japan", label: "Japan (Axis)" },
  { faction: "usa", label: "USA (Allied)" },
  { faction: "uk_pacific", label: "UK Pacific (Allied)" },
  { faction: "anzac", label: "ANZAC (Allied)" },
  { faction: "china", label: "China (Allied)" },
];

interface Props {
  onStart: () => void;
}

export default function SetupPage({ onStart }: Props) {
  const { setSession } = useAppStore();
  const [assignments, setAssignments] = useState<Record<string, string>>(
    Object.fromEntries(PLAYERS.map((p) => [p.faction, p.label]))
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleStart = async () => {
    setLoading(true);
    setError("");
    try {
      const session = await createSession(assignments);
      setSession(session);
      onStart();
    } catch (e: unknown) {
      setError(`Failed to create session: ${(e as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0d1117", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "#16213e", borderRadius: 12, padding: 32, width: 480, boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}>
        <h1 style={{ color: "#fff", fontSize: 22, fontWeight: 800, marginBottom: 4 }}>
          WW2 Pacific 1940 — 2nd Edition
        </h1>
        <p style={{ color: "#888", fontSize: 13, marginBottom: 24 }}>
          Referee-First Tabletop Assistant
        </p>

        <div style={{ marginBottom: 24 }}>
          <div style={{ fontWeight: 700, color: "#aaa", fontSize: 13, marginBottom: 12 }}>PLAYER ASSIGNMENTS</div>
          {PLAYERS.map(({ faction, label }) => (
            <div key={faction} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
              <div style={{ width: 130, color: "#ddd", fontSize: 13 }}>{label}</div>
              <input
                value={assignments[faction] ?? ""}
                onChange={(e) => setAssignments((prev) => ({ ...prev, [faction]: e.target.value }))}
                placeholder={`Player name for ${faction}`}
                style={{ flex: 1, padding: "6px 10px", background: "#1a1a2e", border: "1px solid #444", color: "#fff", borderRadius: 4, fontSize: 13 }}
              />
            </div>
          ))}
        </div>

        <button
          onClick={handleStart}
          disabled={loading}
          style={{
            width: "100%",
            padding: "10px 0",
            background: "#c0392b",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontWeight: 700,
            fontSize: 15,
            cursor: "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "Starting..." : "Start Game"}
        </button>

        {error && <div style={{ marginTop: 10, color: "#e17055", fontSize: 12 }}>{error}</div>}

        <div style={{ marginTop: 16, fontSize: 11, color: "#555", textAlign: "center" }}>
          Uses server-side simulated dice • Rules engine is the source of truth
        </div>
      </div>
    </div>
  );
}
