import { useRef, useState, useEffect } from "react";

type WebSocketMessage =
  | { type: "session_init"; session_id: string }
  | { type: "transcript"; text: string; is_final: boolean };

type ConnectionStatus = "disconnected" | "connecting" | "connected";

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [transcript, setTranscript] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);

  function connect() {
    if (wsRef.current) return;

    setStatus("connecting");
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setStatus("connected");
    };

    ws.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);

      if (data.type === "session_init") {
        setSessionId(data.session_id);
      } else if (data.type === "transcript") {
        setTranscript(data.text);
      }
    };

    ws.onclose = () => {
      setStatus("disconnected");
      wsRef.current = null;
    };

    ws.onerror = () => {
      setStatus("disconnected");
      wsRef.current = null;
    };

    wsRef.current = ws;
  }

  function disconnect() {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: "end_session" }));
      wsRef.current.close();
      wsRef.current = null;
    }
  }

  function sendAudio(data: ArrayBuffer) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { status, transcript, sessionId, connect, disconnect, sendAudio };
}
