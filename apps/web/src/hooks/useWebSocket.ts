import { useEffect, useRef } from "react";
import { createWebSocket } from "../api";
import { useAppStore } from "../store";
import type { WsMessage } from "../types";

export function useWebSocket(gameId: string | null, sessionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const { setWsConnected, setLastWsMessage, setGameState } = useAppStore();

  useEffect(() => {
    if (!gameId || !sessionId) return;

    const ws = createWebSocket(gameId, sessionId);
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data as string);
        setLastWsMessage(msg);

        if (msg.type === "state_updated" && msg.game_id) {
          // Refetch full state on update
          import("../api").then(({ getGameState }) => {
            getGameState(msg.game_id as string).then((state) => {
              setGameState(state);
            });
          });
        }
      } catch {
        // malformed message
      }
    };

    return () => {
      ws.close();
    };
  }, [gameId, sessionId]);

  return wsRef;
}
