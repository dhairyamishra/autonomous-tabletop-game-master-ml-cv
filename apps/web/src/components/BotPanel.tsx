import React, { useState } from "react";
import type { BotSuggestion, GameState } from "../types";
import { getBotSuggestions } from "../api";

interface Props {
  gameState: GameState;
}

export default function BotPanel({ gameState }: Props) {
  const [suggestions, setSuggestions] = useState<BotSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    try {
      const res = await getBotSuggestions(
        gameState.game_id,
        gameState.turn.current_player,
        gameState.turn.phase,
      );
      setSuggestions(res.suggestions ?? []);
    } catch {
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 12 }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#aaa", marginBottom: 8 }}>BOT SUGGESTIONS</div>
      <button
        onClick={handleFetch}
        disabled={loading}
        style={{ padding: "5px 12px", background: "#00b894", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 12, fontWeight: 600 }}
      >
        {loading ? "Thinking..." : "Get Suggestions"}
      </button>

      {suggestions.length === 0 && !loading && (
        <div style={{ color: "#666", fontSize: 12, marginTop: 8 }}>No suggestions yet.</div>
      )}

      {suggestions.map((s) => (
        <div
          key={s.suggestion_id}
          style={{ marginTop: 8, background: "#1a1a2e", borderRadius: 6, padding: 8, border: "1px solid #333", cursor: "pointer" }}
          onClick={() => setExpanded(expanded === s.suggestion_id ? null : s.suggestion_id)}
        >
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontWeight: 700, color: "#fff", fontSize: 12 }}>#{s.rank}</span>
            <span style={{ color: "#f0c040", fontSize: 12 }}>Score: {s.score.toFixed(1)}</span>
          </div>
          <div style={{ color: "#aaa", fontSize: 11, marginTop: 2 }}>{s.reasoning}</div>

          {expanded === s.suggestion_id && (
            <div style={{ marginTop: 6, borderTop: "1px solid #333", paddingTop: 6 }}>
              {s.actions.map((a, i) => (
                <div key={i} style={{ fontSize: 11, color: "#74b9ff", marginBottom: 2 }}>
                  {a.action_type.toUpperCase()}: {a.unit_type ?? ""} {a.from_zone ? `${a.from_zone} →` : ""} {a.to_zone ?? ""}
                  {a.count ? ` ×${a.count}` : ""}
                  {a.detail ? ` (${a.detail})` : ""}
                </div>
              ))}
              <div style={{ marginTop: 4, fontSize: 11, color: "#888" }}>
                Territory: {s.score_breakdown.territory_value.toFixed(1)} |
                Atk: {s.score_breakdown.expected_enemy_value_destroyed.toFixed(1)} |
                Def: {s.score_breakdown.expected_own_value_lost.toFixed(1)} |
                Pos: {s.score_breakdown.positional_gain.toFixed(1)}
              </div>
              {s.warnings.length > 0 && (
                <div style={{ color: "#e17055", fontSize: 11, marginTop: 4 }}>
                  ⚠ {s.warnings.join("; ")}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
