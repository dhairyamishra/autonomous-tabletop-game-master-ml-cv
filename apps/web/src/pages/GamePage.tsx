import React, { useEffect, useCallback } from "react";
import { useAppStore } from "../store";
import { getGameState } from "../api";
import { useWebSocket } from "../hooks/useWebSocket";
import PhaseBar from "../components/PhaseBar";
import EconomyPanel from "../components/EconomyPanel";
import ZonePanel from "../components/ZonePanel";
import BattlePanel from "../components/BattlePanel";
import CorrectionPanel from "../components/CorrectionPanel";
import BotPanel from "../components/BotPanel";
import PhaseControls from "../components/PhaseControls";
import EventLog from "../components/EventLog";

export default function GamePage() {
  const { session, gameState, setGameState, wsConnected } = useAppStore();

  const refresh = useCallback(() => {
    if (session?.game_id) {
      getGameState(session.game_id).then(setGameState).catch(console.error);
    }
  }, [session?.game_id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useWebSocket(session?.game_id ?? null, session?.session_id ?? null);

  if (!session || !gameState) {
    return (
      <div style={{ color: "#fff", padding: 32 }}>
        Loading game state...
      </div>
    );
  }

  return (
    <div style={{ background: "#0d1117", minHeight: "100vh", color: "#fff", fontFamily: "system-ui, sans-serif" }}>
      {/* Top bar */}
      <PhaseBar
        player={gameState.turn.current_player}
        phase={gameState.turn.phase}
        round={gameState.turn.round}
      />

      <div style={{ display: "flex", gap: 0, height: "calc(100vh - 50px)" }}>
        {/* LEFT — Camera + Zones */}
        <div style={{ width: 280, borderRight: "1px solid #222", padding: 10, display: "flex", flexDirection: "column", gap: 8, overflowY: "auto" }}>
          <CameraFeedPlaceholder />
          <ZonePanel gameState={gameState} />
        </div>

        {/* CENTER — State + Controls */}
        <div style={{ flex: 1, padding: 10, display: "flex", flexDirection: "column", gap: 8, overflowY: "auto" }}>
          <StatusBanner gameState={gameState} wsConnected={wsConnected} />
          <PhaseControls
            gameState={gameState}
            sessionId={session.session_id}
            onAdvanced={refresh}
          />
          <BattlePanel
            gameState={gameState}
            sessionId={session.session_id}
            onResolved={refresh}
          />
          <EconomyPanel
            economy={gameState.economy}
            currentPlayer={gameState.turn.current_player}
          />
          <EventLog gameId={gameState.game_id} />
        </div>

        {/* RIGHT — Bot + Correction */}
        <div style={{ width: 300, borderLeft: "1px solid #222", padding: 10, display: "flex", flexDirection: "column", gap: 8, overflowY: "auto" }}>
          <BotPanel gameState={gameState} />
          <CorrectionPanel
            gameState={gameState}
            sessionId={session.session_id}
            onCorrected={refresh}
          />
        </div>
      </div>
    </div>
  );
}

function CameraFeedPlaceholder() {
  return (
    <div style={{
      background: "#1a1a2e",
      borderRadius: 8,
      padding: 12,
      height: 180,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      border: "1px dashed #444",
    }}>
      <div style={{ color: "#555", fontSize: 12 }}>📷 Camera feed</div>
      <div style={{ color: "#444", fontSize: 10, marginTop: 4 }}>
        Vision module connects here
      </div>
    </div>
  );
}

function StatusBanner({ gameState, wsConnected }: { gameState: import("../types").GameState; wsConnected: boolean }) {
  const hasBattles = Object.values(gameState.pending_battles).some(
    (b) => b.status === "pending" || b.status === "in_progress"
  );

  return (
    <div style={{ background: "#16213e", borderRadius: 8, padding: 10, display: "flex", gap: 12, alignItems: "center" }}>
      <div>
        <span style={{ color: "#888", fontSize: 11 }}>State v{gameState.audit.state_version}</span>
        <span style={{ marginLeft: 8, color: "#888", fontSize: 11 }}>
          {wsConnected ? "🟢 Live" : "🔴 Disconnected"}
        </span>
      </div>
      {hasBattles && (
        <div style={{ color: "#e17055", fontSize: 12, fontWeight: 600 }}>
          ⚔ {Object.values(gameState.pending_battles).filter((b) => b.status === "pending" || b.status === "in_progress").length} battle(s) pending
        </div>
      )}
      {gameState.victory_status !== "in_progress" && (
        <div style={{ color: "#f0c040", fontWeight: 700, fontSize: 14 }}>
          🏆 {gameState.victory_status === "japan_wins" ? "Japan wins!" : "Allies win!"}
        </div>
      )}
    </div>
  );
}
