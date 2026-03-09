import React, { useEffect, useState } from "react";
import { getEvents } from "../api";

interface Props {
  gameId: string;
}

export default function EventLog({ gameId }: Props) {
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any

  useEffect(() => {
    getEvents(gameId).then((evs) => setEvents(evs as Record<string, unknown>[])).catch(() => {});
  }, [gameId]);

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 12, height: 240, overflowY: "auto" }}>
      <div style={{ fontWeight: 700, fontSize: 13, color: "#aaa", marginBottom: 8 }}>EVENT LOG</div>
      {events.length === 0 && <div style={{ color: "#555", fontSize: 12 }}>No events yet.</div>}
      {[...events].reverse().map((ev, i) => (
        <div key={i} style={{ fontSize: 11, color: "#888", borderBottom: "1px solid #2a2a3e", paddingBottom: 4, marginBottom: 4 }}>
          <span style={{ color: "#74b9ff" }}>{String(ev["event_type"] ?? "")}</span>
          {" — "}
          <span style={{ color: "#aaa" }}>{String(ev["actor"] ?? "system")}</span>
          {ev["from_phase"] != null && (
            <span> · {String(ev["from_phase"])} → {String(ev["to_phase"] ?? "")}</span>
          )}
        </div>
      ))}
    </div>
  );
}
