import { useRef, useState } from "react";

const SAMPLE_RATE = 16000;

export function useAudioRecorder(onAudioData: (data: ArrayBuffer) => void) {
  const [isRecording, setIsRecording] = useState(false);
  const contextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;

    const context = new AudioContext({ sampleRate: SAMPLE_RATE });
    contextRef.current = context;

    // Load worklet for audio processing
    await context.audioWorklet.addModule("/audio-processor.js");

    const source = context.createMediaStreamSource(stream);
    const worklet = new AudioWorkletNode(context, "audio-processor");

    worklet.port.onmessage = (event) => {
      // event.data is Int16Array from worklet
      onAudioData(event.data.buffer);
    };

    source.connect(worklet);
    workletRef.current = worklet;

    setIsRecording(true);
  }

  function stop() {
    workletRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    contextRef.current?.close();

    workletRef.current = null;
    streamRef.current = null;
    contextRef.current = null;

    setIsRecording(false);
  }

  return { isRecording, start, stop };
}
