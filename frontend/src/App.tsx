import { useWebSocket } from "./hooks/useWebSocket";
import { useAudioRecorder } from "./hooks/useAudioRecorder";

const WS_URL = "ws://localhost:8000/ws/negotiate";

function App() {
  const { status, transcript, connect, disconnect, sendAudio } =
    useWebSocket(WS_URL);

  const { isRecording, start, stop } = useAudioRecorder(sendAudio);

  const isConnected = status === "connected";

  return (
    <div className="min-h-screen bg-zinc-900 text-white p-8">
      <h1 className="text-2xl font-bold mb-6">Salary Dojo - STT Test</h1>

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

      <div className="p-4 bg-zinc-800 rounded min-h-32">
        <p className="text-zinc-400 text-sm mb-2">Transcript:</p>
        <p>{transcript || "(speak to see transcript)"}</p>
      </div>
    </div>
  );
}

export default App;
