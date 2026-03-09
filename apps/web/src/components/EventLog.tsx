import React, { useEffect, useState } from "react";
import { getEvents } from "../api";

interface Props {
  gameId: string;
}

export default function EventLog({ gameId }: Props) {
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    getEvents(gameId).then((evs) => setEvents(evs as Record<string, unknown>[])).catch(() => {});
  }, [gameId]);

  const recentEvents = [...events].reverse();

  return (
    <div style={{
      background: "#16213e",
      borderRadius: 6,
      height: "100%",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
    }}>
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "5px 10px",
          cursor: "pointer",
          userSelect: "none",
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 700, fontSize: 10, color: "#666", textTransform: "uppercase", letterSpacing: 0.5 }}>
          Events
        </span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 10, color: "#55efc4" }}>
            {events.length}
          </span>
          <span style={{
            fontSize: 9,
            color: "#555",
            transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
            display: "inline-block",
          }}>
            &#9660;
          </span>
        </div>
      </div>

      {expanded && (
        <div style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "0 10px 6px" }}>
          {recentEvents.length === 0 && (
            <div style={{ color: "#555", fontSize: 10 }}>No events yet.</div>
          )}
          {recentEvents.map((ev, i) => (
            <div key={i} style={{
              fontSize: 10,
              color: "#888",
              borderBottom: "1px solid #2a2a3e",
              paddingBottom: 2,
              marginBottom: 2,
            }}>
              <span style={{ color: "#74b9ff" }}>{String(ev["event_type"] ?? "")}</span>
              {" \u2014 "}
              <span style={{ color: "#aaa" }}>{String(ev["actor"] ?? "system")}</span>
              {ev["from_phase"] != null && (
                <span> &middot; {String(ev["from_phase"])} &rarr; {String(ev["to_phase"] ?? "")}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
