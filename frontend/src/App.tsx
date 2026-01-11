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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  // Toggle recording with optimistic UI
  const handleRecordingClick = async () => {
    console.log('Button clicked - isConnected:', isConnected, 'isTransitioning:', isTransitioning, 'isRecording:', isRecording);

    if (!isConnected) {
      console.warn('Cannot record: WebSocket not connected');
      return;
    }

    if (isTransitioning) {
      console.warn('Cannot record: Already transitioning');
      return;
    }

    setIsTransitioning(true);

    try {
      if (isRecording) {
        console.log('Stopping recording...');
        // Wait a moment for any final audio to be sent before stopping
        await new Promise(resolve => setTimeout(resolve, 500));
        stop();
      } else {
        console.log('Starting recording...');
        await start();
      }
    } catch (error) {
      console.error('Error toggling recording:', error);
      // Reset state on error
      stop();
      alert('Microphone error. Please refresh the page and try again.');
    } finally {
      console.log('Transition complete');
      setIsTransitioning(false);
    }
  };

  return (
    <div className="h-screen bg-neutral-950 text-white flex flex-col">
      {/* Header */}
      <header className="p-6 border-b border-neutral-800/50 bg-neutral-900/50 backdrop-blur-sm">
        <h1 className="text-3xl font-black text-center tracking-[0.3em] text-red-500 uppercase" style={{ fontFamily: 'Impact, "Arial Black", sans-serif', textShadow: '2px 2px 0px rgba(0,0,0,0.5), 0 0 10px rgba(239, 68, 68, 0.3)' }}>
          SALARY KOMBAT
        </h1>
      </header>

      {/* Split Screen Layout */}
      <div className="flex-1 grid grid-cols-2 divide-x divide-red-900/30">
        {/* User Side (Left) */}
        <div className="flex items-center justify-center p-8">
          <div className="flex flex-col items-center">
            {/* Current Offer Display */}
            <div className="mb-8">
              {marcusCurrentOffer ? (
                <div className="text-center px-6 py-3 rounded-xl bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border border-emerald-500/20">
                  <div className="text-xs text-emerald-300/60 mb-1 uppercase tracking-wide">Current Offer</div>
                  <div className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-green-300 bg-clip-text text-transparent">
                    ${marcusCurrentOffer.toLocaleString()}
                  </div>
                </div>
              ) : (
                <div className="text-center px-6 py-3 rounded-xl bg-neutral-800/30 border border-neutral-700/30">
                  <div className="text-sm text-neutral-400">No offer yet</div>
                </div>
              )}
            </div>

            <h2 className="text-lg font-semibold text-neutral-200 mb-12">You</h2>

            {/* Recording Button */}
            <button
              onClick={handleRecordingClick}
              disabled={!isConnected || isTransitioning}
              className={`
                w-36 h-36 rounded-full mb-8
                transition-all duration-200 ease-out
                flex items-center justify-center
                border-2
                ${!isConnected || isTransitioning
                  ? "bg-neutral-800 border-neutral-700 cursor-not-allowed opacity-50"
                  : isRecording
                    ? "bg-gradient-to-br from-red-500 to-red-600 border-red-400/50 hover:from-red-600 hover:to-red-700 scale-110"
                    : "bg-gradient-to-br from-red-600 to-orange-600 border-red-500/50 hover:from-red-700 hover:to-orange-700 cursor-pointer active:scale-95"
                }
              `}
              style={
                isRecording && isConnected && !isTransitioning
                  ? { boxShadow: "0 0 60px 12px rgba(239, 68, 68, 0.5)" }
                  : !isTransitioning && isConnected
                  ? { boxShadow: "0 0 30px 6px rgba(220, 38, 38, 0.4)" }
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
            <div className="h-20 w-64 flex items-center justify-center gap-1">
              {waveformHeights.map((height, i) => (
                <div
                  key={i}
                  className={`w-1.5 rounded-full transition-all duration-150 ${isRecording ? "bg-gradient-to-t from-red-500 to-orange-400 shadow-lg shadow-red-500/50" : "bg-neutral-700/50"
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
              <div className="h-5 bg-neutral-800/50 rounded-full overflow-hidden border border-neutral-700/30 shadow-inner">
                <div
                  className="h-full transition-all duration-500 ease-out shadow-lg"
                  style={{
                    width: `${marcusPatience}%`,
                    background: marcusPatience > 66
                      ? 'linear-gradient(90deg, #10b981, #34d399)'
                      : marcusPatience > 33
                        ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                        : 'linear-gradient(90deg, #ef4444, #f87171)',
                    boxShadow: marcusPatience > 66
                      ? '0 0 20px rgba(16, 185, 129, 0.6)'
                      : marcusPatience > 33
                        ? '0 0 20px rgba(245, 158, 11, 0.6)'
                        : '0 0 20px rgba(239, 68, 68, 0.6)'
                  }}
                />
              </div>
            </div>

            <h2 className="text-lg font-semibold text-neutral-200 mb-12">Marcus</h2>

            {/* AI Avatar with Emoji */}
            <div className="w-36 h-36 rounded-full bg-gradient-to-br from-neutral-800 to-neutral-900 border-2 border-red-900/40 mb-8 flex items-center justify-center text-7xl transition-transform duration-300 hover:scale-110 shadow-xl shadow-red-950/30">
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
            <div className="h-20 w-64 flex items-center justify-center gap-1">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className="w-1.5 bg-neutral-700/50 rounded-full transition-all duration-150"
                  style={{ height: "20%" }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer - Status & Transcript */}
      <footer className="border-t border-neutral-800/50 bg-neutral-900/50 backdrop-blur-sm">
        {/* Transcript Display - Always show, even if empty */}
        <div className="px-6 py-4 border-b border-neutral-800/30 min-h-[60px] flex items-center">
          {transcript ? (
            <p className="text-sm text-neutral-200 italic leading-relaxed">
              "{transcript}"
            </p>
          ) : (
            <p className="text-sm text-neutral-500 italic">
              Click the microphone and speak to see transcript...
            </p>
          )}
        </div>

        {/* Status Bar */}
        <div className="px-6 py-2 flex items-center justify-between text-xs text-neutral-400">
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
