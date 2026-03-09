import axios from "axios";
import type { GameState, BotSuggestion, SessionInfo } from "./types";

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

// Session
export const createSession = (playerAssignments: Record<string, string>) =>
  api.post<SessionInfo>("/session/create", { player_assignments: playerAssignments }).then(r => r.data);

export const getSession = (sessionId: string) =>
  api.get<SessionInfo>(`/session/${sessionId}`).then(r => r.data);

// Game state
export const getGameState = (gameId: string) =>
  api.get<GameState>(`/game/${gameId}/state`).then(r => r.data);

export const getEvents = (gameId: string, limit = 100, offset = 0) =>
  api.get<unknown[]>(`/game/${gameId}/events`, { params: { limit, offset } }).then(r => r.data);

export const getReplay = (gameId: string) =>
  api.get(`/game/${gameId}/replay`).then(r => r.data);

// Phase
export const advancePhase = (gameId: string, sessionId: string, actor: string) =>
  api.post("/game/phase/advance", { game_id: gameId, session_id: sessionId, actor }).then(r => r.data);

// Combat
export const resolveCombat = (payload: {
  game_id: string;
  session_id: string;
  actor: string;
  battle_id: string;
  retreat_after_round?: number;
  retreat_to_zone?: string;
}) => api.post("/combat/resolve", payload).then(r => r.data);

// State commit
export const commitState = (payload: {
  game_id: string;
  session_id: string;
  actor: string;
  phase: string;
  delta: Record<string, unknown>;
  correction_type?: string;
  reason?: string;
}) => api.post("/state/commit", payload).then(r => r.data);

// Correction
export const applyCorrection = (payload: {
  game_id: string;
  session_id: string;
  actor: string;
  correction_type: string;
  zone_id: string;
  changes: Record<string, unknown>;
  reason: string;
}) => api.post("/correction/apply", payload).then(r => r.data);

// Bot
export const getBotSuggestions = (gameId: string, player: string, phase: string) =>
  api.post<{ suggestions: BotSuggestion[] }>("/bot/suggest", {
    game_id: gameId, player, phase,
  }).then(r => r.data);

// Action validation
export const validateAction = (payload: Record<string, unknown>) =>
  api.post<{ is_legal: boolean; reason: string }>("/game/action/validate", payload).then(r => r.data);

// Vision
export const calibrateCamera = (sessionId: string, gameId: string) =>
  api.post("/vision/calibrate", { session_id: sessionId, game_id: gameId }).then(r => r.data);

// WebSocket
export const createWebSocket = (gameId: string, sessionId: string): WebSocket => {
  const wsBase = BASE_URL.replace(/^http/, "ws");
  return new WebSocket(`${wsBase}/ws/${gameId}?session_id=${sessionId}`);
};
