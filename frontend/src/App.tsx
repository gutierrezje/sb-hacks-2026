import { useState } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import { useAudioRecorder } from "./hooks/useAudioRecorder";

const WS_URL = "ws://localhost:8000/ws/negotiate";

function App() {
  const { status, transcript, connect, disconnect, sendAudio, sendMessage } =
    useWebSocket(WS_URL);

  const { isRecording, start, stop } = useAudioRecorder(sendAudio);
  const [testMessage, setTestMessage] = useState("");
  const [useStreaming, setUseStreaming] = useState(true);

  const isConnected = status === "connected";

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (testMessage.trim()) {
      const messageType = useStreaming ? "test_llm_stream" : "test_llm";
      sendMessage({ type: messageType, text: testMessage });
      setTestMessage("");
    }
  };

  return (
    <div className="min-h-screen bg-zinc-900 text-white p-8">
      <h1 className="text-2xl font-bold mb-6">Salary Dojo - Voice Test</h1>

      <div className="flex gap-4 mb-6">
        <button
          onClick={isConnected ? disconnect : connect}
          className="px-4 py-2 bg-zinc-700 rounded hover:bg-zinc-600"
        >
          {status === "connecting"
            ? "Connecting..."
            : isConnected
              ? "Disconnect"
              : "Connect"}
        </button>

        <button
          onClick={isRecording ? stop : start}
          disabled={!isConnected}
          className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-500 disabled:opacity-50"
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>


      </div>

      <div className="p-4 bg-zinc-800 rounded min-h-32 mb-6">
        <p className="text-zinc-400 text-sm mb-2">Transcript:</p>
        <p>{transcript || "(speak to see transcript)"}</p>
      </div>

      <div className="p-4 bg-zinc-800 rounded">
        <p className="text-zinc-400 text-sm mb-3">Test Marcus (type message):</p>

        <div className="mb-3 flex items-center gap-2">
          <input
            type="checkbox"
            id="streaming"
            checked={useStreaming}
            onChange={(e) => setUseStreaming(e.target.checked)}
            className="w-4 h-4"
          />
          <label htmlFor="streaming" className="text-sm text-zinc-300">
            Use streaming (faster response)
          </label>
        </div>

        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Type a message to Marcus..."
            disabled={!isConnected}
            className="flex-1 px-3 py-2 bg-zinc-700 rounded border border-zinc-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!isConnected || !testMessage.trim()}
            className="px-4 py-2 bg-green-600 rounded hover:bg-green-500 disabled:opacity-50"
          >
            Send to Marcus
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
