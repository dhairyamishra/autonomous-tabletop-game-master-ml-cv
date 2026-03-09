import { create } from "zustand";
import type { GameState, SessionInfo, BotSuggestion, WsMessage, Observation } from "./types";

interface AppStore {
  session: SessionInfo | null;
  gameState: GameState | null;
  botSuggestions: BotSuggestion[];
  wsConnected: boolean;
  lastWsMessage: WsMessage | null;
  pendingConfirmations: string[];
  latestObservation: Observation | null;
  correctionDrawerOpen: boolean;

  setSession: (s: SessionInfo) => void;
  setGameState: (s: GameState) => void;
  setBotSuggestions: (suggestions: BotSuggestion[]) => void;
  setWsConnected: (v: boolean) => void;
  setLastWsMessage: (msg: WsMessage) => void;
  addPendingConfirmation: (zone_id: string) => void;
  clearPendingConfirmations: () => void;
  setLatestObservation: (obs: Observation | null) => void;
  setCorrectionDrawerOpen: (v: boolean) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  session: null,
  gameState: null,
  botSuggestions: [],
  wsConnected: false,
  lastWsMessage: null,
  pendingConfirmations: [],
  latestObservation: null,
  correctionDrawerOpen: false,

  setSession: (s) => set({ session: s }),
  setGameState: (s) => set({ gameState: s }),
  setBotSuggestions: (suggestions) => set({ botSuggestions: suggestions }),
  setWsConnected: (v) => set({ wsConnected: v }),
  setLastWsMessage: (msg) => set({ lastWsMessage: msg }),
  addPendingConfirmation: (zone_id) =>
    set((state) => ({
      pendingConfirmations: [...state.pendingConfirmations, zone_id],
    })),
  clearPendingConfirmations: () => set({ pendingConfirmations: [] }),
  setLatestObservation: (obs) => set({ latestObservation: obs }),
  setCorrectionDrawerOpen: (v) => set({ correctionDrawerOpen: v }),
}));
