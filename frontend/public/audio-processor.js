// This AudioWorkletProcessor captures audio input, converts it from Float32 that 
// it gets from the browswer and transforms it to Int16, which is the format 
// we require for Deepgram.

class AudioProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input.length > 0) {
      const float32 = input[0];
      const int16 = new Int16Array(float32.length);

      // Convert float32 [-1, 1] to int16 [-32768, 32767]
      for (let i = 0; i < float32.length; i++) {
        const s = Math.max(-1, Math.min(1, float32[i]));
        int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }

      this.port.postMessage(int16);
    }
    return true;
  }
}

registerProcessor("audio-processor", AudioProcessor);
