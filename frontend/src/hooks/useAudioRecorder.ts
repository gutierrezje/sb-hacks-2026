import { useRef, useState, useEffect } from "react";

const SAMPLE_RATE = 16000;

export function useAudioRecorder(onAudioData: (data: ArrayBuffer) => void) {
  const [isRecording, setIsRecording] = useState(false);
  const contextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const isStartingRef = useRef(false);

  async function start() {
    // Prevent concurrent starts
    if (isStartingRef.current || isRecording) {
      console.warn('Recording already in progress');
      return;
    }

    isStartingRef.current = true;

    try {
      // Clean up any existing resources first
      stop();

      console.log('Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      console.log('Microphone access granted');

      // Create context - browser will resample to this rate
      const context = new AudioContext({ sampleRate: SAMPLE_RATE });
      contextRef.current = context;
      console.log('AudioContext created');

      // Load worklet for audio processing
      console.log('Loading audio worklet...');
      await context.audioWorklet.addModule("/audio-processor.js");
      console.log('Audio worklet loaded');

      const source = context.createMediaStreamSource(stream);
      const worklet = new AudioWorkletNode(context, "audio-processor");

      worklet.port.onmessage = (event) => {
        // event.data is Int16Array from worklet
        onAudioData(event.data.buffer);
      };

      source.connect(worklet);
      workletRef.current = worklet;

      setIsRecording(true);
      console.log('Recording started successfully');
    } catch (error) {
      console.error('Failed to start recording:', error);
      // Clean up on error
      stop();
      throw error;
    } finally {
      isStartingRef.current = false;
    }
  }

  function stop() {
    try {
      workletRef.current?.disconnect();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      contextRef.current?.close();
    } catch (error) {
      console.error('Error during cleanup:', error);
    } finally {
      workletRef.current = null;
      streamRef.current = null;
      contextRef.current = null;
      setIsRecording(false);
      isStartingRef.current = false;
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      console.log('useAudioRecorder unmounting - cleaning up resources');
      stop();
    };
  }, []);

  return { isRecording, start, stop };
}
