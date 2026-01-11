import { useRef, useState, useEffect } from "react";

type WebSocketMessage =
  | { type: "session_init"; session_id: string }
  | { type: "transcript"; text: string; is_final: boolean }
  | { type: "marcus_state"; patience: number; emotion: string; current_offer: number | null; outcome: string | null };

type ConnectionStatus = "disconnected" | "connecting" | "connected";

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [transcript, setTranscript] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [marcusEmotion, setMarcusEmotion] = useState<string>("neutral");
  const [marcusPatience, setMarcusPatience] = useState<number>(100);

  function connect() {
    if (wsRef.current) return;

    setStatus("connecting");
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setStatus("connected");
    };

    ws.onmessage = (event) => {
      // Handle binary audio data
      if (event.data instanceof Blob) {
        const audioBlob = event.data;
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
        return;
      }

      // Handle JSON messages
      const data: WebSocketMessage = JSON.parse(event.data);

      if (data.type === "session_init") {
        setSessionId(data.session_id);
      } else if (data.type === "transcript") {
        setTranscript(data.text);
      } else if (data.type === "marcus_state") {
        setMarcusEmotion(data.emotion);
        setMarcusPatience(data.patience);
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

  function sendMessage(message: object) {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return { status, transcript, sessionId, marcusEmotion, marcusPatience, connect, disconnect, sendAudio, sendMessage };
}
