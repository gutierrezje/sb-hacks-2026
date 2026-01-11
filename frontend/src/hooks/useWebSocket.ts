import { useRef, useState, useEffect } from "react";

type WebSocketMessage =
  | { type: "session_init"; session_id: string }
  | { type: "transcript"; text: string; is_final: boolean }
  | { type: "marcus_response"; text: string }
  | { type: "marcus_state"; patience: number; emotion: string; current_offer: number | null; outcome: string | null };

type ConnectionStatus = "disconnected" | "connecting" | "connected";

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [transcript, setTranscript] = useState("");
  const [conversationHistory, setConversationHistory] = useState<Array<{ speaker: "user" | "marcus", text: string }>>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [marcusEmotion, setMarcusEmotion] = useState<string>("neutral");
  const [marcusPatience, setMarcusPatience] = useState<number>(100);
  const [marcusCurrentOffer, setMarcusCurrentOffer] = useState<number | null>(null);

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
        // Add final user transcript to conversation history
        if (data.is_final && data.text.trim()) {
          setConversationHistory(prev => [...prev, { speaker: "user", text: data.text }]);
        }
      } else if (data.type === "marcus_response") {
        // Add Marcus's response to conversation history
        setConversationHistory(prev => [...prev, { speaker: "marcus", text: data.text }]);
        setTranscript(""); // Clear interim transcript
      } else if (data.type === "marcus_state") {
        setMarcusEmotion(data.emotion);
        setMarcusPatience(data.patience);
        setMarcusCurrentOffer(data.current_offer);
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
      try {
        if (wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "end_session" }));
        }
        wsRef.current.close();
      } catch (error) {
        console.error('Error disconnecting WebSocket:', error);
      } finally {
        wsRef.current = null;
        setStatus("disconnected");
      }
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

  return { status, transcript, conversationHistory, sessionId, marcusEmotion, marcusPatience, marcusCurrentOffer, connect, disconnect, sendAudio, sendMessage };
}
