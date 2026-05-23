import { WS_BASE } from "./api";
export function openProgressWS(sessionId: string, onEvent: (e: { event: string; data: any }) => void): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/progress/${sessionId}`);
  ws.onmessage = (m) => {
    try { onEvent(JSON.parse(m.data)); } catch {}
  };
  return ws;
}
export function makeSessionId(): string {
  return "s_" + Math.random().toString(36).slice(2, 12);
}
