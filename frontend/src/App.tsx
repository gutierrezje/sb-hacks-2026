import { useEffect, useState } from "react";
import { useWebSocket } from "./hooks/useWebSocket";
import { useAudioRecorder } from "./hooks/useAudioRecorder";

const WS_URL = "ws://localhost:8000/ws/negotiate";

function App() {
  const { status, transcript, marcusEmotion, marcusPatience, marcusCurrentOffer, connect, disconnect, sendAudio } =
    useWebSocket(WS_URL);

  const { isRecording, start, stop } = useAudioRecorder(sendAudio);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [waveformHeights, setWaveformHeights] = useState<number[]>(
    Array(20).fill(20)
  );



  const isConnected = status === "connected";

  // Animate waveform when recording
  useEffect(() => {
    if (!isRecording) {
      setWaveformHeights(Array(20).fill(20));
      return;
    }

    const interval = setInterval(() => {
      setWaveformHeights(
        Array(20)
          .fill(0)
          .map(() => Math.random() * 60 + 20)
      );
    }, 150);

    return () => clearInterval(interval);
  }, [isRecording]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  // Toggle recording with optimistic UI
  const handleRecordingClick = async () => {
    if (!isConnected || isTransitioning) return;

    setIsTransitioning(true);

    try {
      if (isRecording) {
        // Wait a moment for any final audio to be sent before stopping
        await new Promise(resolve => setTimeout(resolve, 500));
        stop();
      } else {
        await start();
      }
    } finally {
      setIsTransitioning(false);
    }
  };

  return (
    <div className="h-screen bg-zinc-900 text-white flex flex-col">
      {/* Header */}
      <header className="p-4 border-b border-zinc-800">
        <h1 className="text-2xl font-bold text-center">SALARY KOMBAT</h1>
      </header>

      {/* Split Screen Layout */}
      <div className="flex-1 grid grid-cols-2 divide-x divide-zinc-800">
        {/* User Side (Left) */}
        <div className="flex items-center justify-center p-8">
          <div className="flex flex-col items-center">
            {/* Current Offer Display */}
            <div className="mb-8">
              {marcusCurrentOffer ? (
                <div className="text-center">
                  <div className="text-sm text-zinc-400 mb-1">Current Offer</div>
                  <div className="text-2xl font-bold text-green-400">
                    ${marcusCurrentOffer.toLocaleString()}
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  <div className="text-sm text-zinc-400">No offer yet</div>
                </div>
              )}
            </div>

            <h2 className="text-lg font-semibold text-zinc-200 mb-12">You</h2>

            {/* Recording Button */}
            <button
              onClick={handleRecordingClick}
              disabled={!isConnected || isTransitioning}
              className={`
                w-32 h-32 rounded-full mb-8
                transition-all duration-150 ease-out
                flex items-center justify-center
                ${!isConnected || isTransitioning
                  ? "bg-zinc-800 cursor-not-allowed opacity-50"
                  : isRecording
                    ? "bg-red-600 hover:bg-red-700 scale-110"
                    : "bg-blue-600 hover:bg-blue-700 cursor-pointer active:scale-95"
                }
              `}
              style={
                isRecording && isConnected && !isTransitioning
                  ? { boxShadow: "0 0 40px 8px rgba(220, 38, 38, 0.6)" }
                  : undefined
              }
            >
              <div className="relative">
                {isTransitioning ? (
                  // Loading state
                  <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : isRecording ? (
                  // Recording state - solid square
                  <div className="w-6 h-6 bg-white rounded-sm" />
                ) : (
                  // Idle state - microphone icon
                  <div className="w-8 h-8 flex items-center justify-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth={2}
                      stroke="currentColor"
                      className="w-8 h-8 text-white"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"
                      />
                    </svg>
                  </div>
                )}
              </div>
            </button>

            {/* User Waveform */}
            <div className="h-16 w-64 flex items-center justify-center gap-1">
              {waveformHeights.map((height, i) => (
                <div
                  key={i}
                  className={`w-1 rounded-full transition-all duration-150 ${isRecording ? "bg-blue-500" : "bg-zinc-700"
                    }`}
                  style={{ height: `${height}%` }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* AI Side (Right) */}
        <div className="flex items-center justify-center p-8">
          <div className="flex flex-col items-center">
            {/* Patience Bar */}
            <div className="w-64 mb-6">
              <div className="h-4 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all duration-500 ease-out"
                  style={{
                    width: `${marcusPatience}%`,
                    background: marcusPatience > 66
                      ? 'linear-gradient(90deg, #10b981, #34d399)'
                      : marcusPatience > 33
                        ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                        : 'linear-gradient(90deg, #ef4444, #f87171)'
                  }}
                />
              </div>
            </div>

            <h2 className="text-lg font-semibold text-zinc-200 mb-12">Marcus</h2>

            {/* AI Avatar with Emoji */}
            <div className="w-32 h-32 rounded-full bg-zinc-800 mb-8 flex items-center justify-center text-6xl transition-transform duration-300 hover:scale-110">
              {{
                neutral: '😐',
                impressed: '😊',
                very_impressed: '😄',
                skeptical: '🤨',
                stressed: '😰',
                done: '😑',
              }[marcusEmotion] || '😐'}
            </div>

            {/* AI Waveform - will animate when AI is speaking */}
            <div className="h-16 w-64 flex items-center justify-center gap-1">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-zinc-700 rounded-full transition-all duration-150"
                  style={{ height: "20%" }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer - Status & Transcript */}
      <footer className="border-t border-zinc-800 bg-zinc-900">
        {/* Transcript Display - Always show, even if empty */}
        <div className="px-6 py-3 border-b border-zinc-800 min-h-[60px] flex items-center">
          {transcript ? (
            <p className="text-sm text-zinc-200 italic">
              "{transcript}"
            </p>
          ) : (
            <p className="text-sm text-zinc-500 italic">
              Click the microphone and speak to see transcript...
            </p>
          )}
        </div>

        {/* Status Bar */}
        <div className="px-6 py-2 flex items-center justify-between text-xs text-zinc-400">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${status === "connected"
                ? "bg-green-500"
                : status === "connecting"
                  ? "bg-yellow-500 animate-pulse"
                  : "bg-red-500"
                }`}
            />
            <span>
              {status === "connected"
                ? "Connected"
                : status === "connecting"
                  ? "Connecting..."
                  : "Disconnected"}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {isRecording && (
              <span className="text-red-400 flex items-center gap-1">
                <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse" />
                Recording
              </span>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
