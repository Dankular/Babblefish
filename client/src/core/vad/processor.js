// VAD utterance boundary detection
import { SileroVAD } from './silero.js';

export class VADProcessor {
  constructor(onUtteranceComplete) {
    this.vad = new SileroVAD();
    this.onUtteranceComplete = onUtteranceComplete;

    // VAD configuration
    this.frameSize = 512; // Samples per VAD frame (32ms at 16kHz)
    this.threshold = 0.5; // Speech probability threshold
    this.minSpeechFrames = 3; // Minimum frames to consider speech start
    this.minSilenceFrames = 10; // Minimum silence frames to end utterance (320ms)

    // State
    this.buffer = [];
    this.utteranceBuffer = [];
    this.isSpeaking = false;
    this.speechFrameCount = 0;
    this.silenceFrameCount = 0;

    // Statistics
    this.lastSpeechTime = 0;
  }

  async processChunk(audioData) {
    // Add to buffer
    this.buffer.push(...audioData);

    // Process complete frames
    while (this.buffer.length >= this.frameSize) {
      const frame = this.buffer.splice(0, this.frameSize);
      await this.processFrame(new Float32Array(frame));
    }
  }

  async processFrame(frame) {
    // Get speech probability from VAD
    const speechProb = await this.vad.predict(frame);

    const isSpeech = speechProb > this.threshold;

    if (isSpeech) {
      this.speechFrameCount++;
      this.silenceFrameCount = 0;

      // Start utterance if enough speech frames
      if (!this.isSpeaking && this.speechFrameCount >= this.minSpeechFrames) {
        this.isSpeaking = true;
        console.log('Speech started');
      }

      // Collect audio during speech
      if (this.isSpeaking) {
        this.utteranceBuffer.push(...frame);
        this.lastSpeechTime = Date.now();
      }
    } else {
      this.silenceFrameCount++;
      this.speechFrameCount = 0;

      // Continue collecting audio during potential pause
      if (this.isSpeaking) {
        this.utteranceBuffer.push(...frame);
      }

      // End utterance after enough silence
      if (this.isSpeaking && this.silenceFrameCount >= this.minSilenceFrames) {
        await this.finalizeUtterance();
      }
    }
  }

  async finalizeUtterance() {
    if (this.utteranceBuffer.length > 0) {
      const utterance = new Float32Array(this.utteranceBuffer);
      const durationMs = (utterance.length / 16000) * 1000;

      console.log(`Utterance complete: ${durationMs.toFixed(0)}ms, ${utterance.length} samples`);

      // Reset state
      this.utteranceBuffer = [];
      this.isSpeaking = false;
      this.speechFrameCount = 0;
      this.silenceFrameCount = 0;

      // Callback with complete utterance
      if (this.onUtteranceComplete) {
        await this.onUtteranceComplete(utterance);
      }
    }
  }

  reset() {
    this.buffer = [];
    this.utteranceBuffer = [];
    this.isSpeaking = false;
    this.speechFrameCount = 0;
    this.silenceFrameCount = 0;
    this.vad.reset();
  }

  getState() {
    return {
      isSpeaking: this.isSpeaking,
      bufferSize: this.buffer.length,
      utteranceSize: this.utteranceBuffer.length,
      lastSpeechTime: this.lastSpeechTime
    };
  }
}
