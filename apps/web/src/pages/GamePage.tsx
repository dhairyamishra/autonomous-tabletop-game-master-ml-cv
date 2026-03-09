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
import BoardFeed from "../components/BoardFeed";
import CombatPrediction from "../components/CombatPrediction";
import type { Player } from "../types";

const AXIS_PLAYERS: Player[] = ["japan"];

export default function GamePage() {
  const {
    session,
    gameState,
    setGameState,
    wsConnected,
    latestObservation,
    correctionDrawerOpen,
    setCorrectionDrawerOpen,
    botSuggestions,
  } = useAppStore();

  const refresh = useCallback(() => {
    if (session?.game_id) {
      getGameState(session.game_id).then(setGameState).catch(console.error);
    }
  }, [session?.game_id, setGameState]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useWebSocket(session?.game_id ?? null, session?.session_id ?? null);

  if (!session || !gameState) {
    return (
      <div style={{
        color: "#888",
        padding: 40,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        background: "#0d1117",
        fontSize: 14,
      }}>
        Loading game state...
      </div>
    );
  }

  const currentPlayer = gameState.turn.current_player;
  const isAxisTurn = AXIS_PLAYERS.includes(currentPlayer);
  const pendingBattleCount = Object.values(gameState.pending_battles).filter(
    (b) => b.status === "pending" || b.status === "in_progress"
  ).length;

  const latestSimulation = botSuggestions.length > 0
    ? botSuggestions[0].simulation_summary ?? null
    : null;

  return (
    <div style={{
      display: "flex",
      flexDirection: "row",
      width: "100vw",
      height: "100vh",
      overflow: "hidden",
      background: "#0d1117",
      color: "#fff",
      fontFamily: "system-ui, -apple-system, sans-serif",
    }}>

      {/* LEFT SIDEBAR — 20vw */}
      <div style={{
        width: "20vw",
        height: "100vh",
        overflowY: "auto",
        borderRight: "2px solid #1a1a2e",
        padding: 8,
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}>
        <SidebarHeader label="Japan" color="#c0392b" active={isAxisTurn} />
        <EconomyPanel economy={gameState.economy} currentPlayer={currentPlayer} side="axis" />
        {isAxisTurn && (
          <>
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
            <CombatPrediction
              gameState={gameState}
              simulationSummary={latestSimulation}
            />
            <BotPanel gameState={gameState} />
            <button
              onClick={() => setCorrectionDrawerOpen(!correctionDrawerOpen)}
              className="correction-toggle"
            >
              {correctionDrawerOpen ? "Close Corrections" : "Corrections"}
            </button>
          </>
        )}
        <ZonePanel gameState={gameState} factionFilter="axis" />
      </div>

      {/* CENTER — 60vw */}
      <div style={{
        width: "60vw",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}>

        {/* TOP BAR — 10vh */}
        <div style={{ height: "10vh", flexShrink: 0 }}>
          <PhaseBar
            player={gameState.turn.current_player}
            phase={gameState.turn.phase}
            round={gameState.turn.round}
            stateVersion={gameState.audit.state_version}
            wsConnected={wsConnected}
            victoryStatus={gameState.victory_status}
            pendingBattleCount={pendingBattleCount}
          />
        </div>

        {/* VIDEO FEED — flex:1 fills remaining ~75vh */}
        <div style={{
          flex: 1,
          minHeight: 0,
        }}>
          <BoardFeed
            observation={latestObservation}
            isCalibrated={latestObservation?.is_calibrated ?? false}
            wsConnected={wsConnected}
          />
        </div>

        {/* BOTTOM BAR — 15vh */}
        <div style={{ height: "15vh", flexShrink: 0, overflow: "hidden" }}>
          <EventLog gameId={gameState.game_id} />
        </div>

        {/* Correction drawer */}
        <div className={`correction-drawer ${correctionDrawerOpen ? "open" : ""}`}>
          <CorrectionPanel
            gameState={gameState}
            sessionId={session.session_id}
            onCorrected={refresh}
          />
        </div>
      </div>

      {/* RIGHT SIDEBAR — 20vw */}
      <div style={{
        width: "20vw",
        height: "100vh",
        overflowY: "auto",
        borderLeft: "2px solid #1a1a2e",
        padding: 8,
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}>
        <SidebarHeader label="Allies" color="#2980b9" active={!isAxisTurn} />
        <EconomyPanel economy={gameState.economy} currentPlayer={currentPlayer} side="allies" />
        {!isAxisTurn && (
          <>
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
            <CombatPrediction
              gameState={gameState}
              simulationSummary={latestSimulation}
            />
            <BotPanel gameState={gameState} />
            <button
              onClick={() => setCorrectionDrawerOpen(!correctionDrawerOpen)}
              className="correction-toggle"
            >
              {correctionDrawerOpen ? "Close Corrections" : "Corrections"}
            </button>
          </>
        )}
        <ZonePanel gameState={gameState} factionFilter="allies" />
      </div>

    </div>
  );
}

function SidebarHeader({ label, color, active }: { label: string; color: string; active: boolean }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 8,
      padding: "4px 2px",
      flexShrink: 0,
    }}>
      <div style={{
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: active ? color : "#333",
        boxShadow: active ? `0 0 8px ${color}` : "none",
        transition: "all 0.3s",
      }} />
      <span style={{
        fontWeight: 700,
        fontSize: 12,
        color: active ? color : "#555",
        textTransform: "uppercase",
        letterSpacing: 1,
        transition: "color 0.3s",
      }}>
        {label}
      </span>
      {active && (
        <span style={{
          fontSize: 9,
          color: "#888",
          background: "#2a2a3e",
          padding: "1px 6px",
          borderRadius: 3,
        }}>
          ACTIVE
        </span>
      )}
    </div>
  );
}
