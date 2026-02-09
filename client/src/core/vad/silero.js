// Silero VAD ONNX model loading and inference
import * as ort from 'onnxruntime-web';

export class SileroVAD {
  constructor() {
    this.session = null;
    this.sampleRate = 16000;
    this.h = null;
    this.c = null;
    this.modelUrl = 'https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.7/dist/silero_vad.onnx';
  }

  async load() {
    try {
      this.session = await ort.InferenceSession.create(this.modelUrl);
      this.reset();
      console.log('Silero VAD model loaded successfully');
    } catch (error) {
      console.error('Failed to load Silero VAD model:', error);
      throw error;
    }
  }

  reset() {
    // Reset internal states (h and c are hidden states for LSTM)
    this.h = new Array(2 * 1 * 64).fill(0);
    this.c = new Array(2 * 1 * 64).fill(0);
  }

  async predict(audioData) {
    if (!this.session) {
      throw new Error('VAD model not loaded. Call load() first.');
    }

    // audioData: Float32Array of 512 samples at 16kHz
    if (audioData.length !== 512) {
      throw new Error(`Expected 512 samples, got ${audioData.length}`);
    }

    try {
      // Create input tensors
      const inputTensor = new ort.Tensor('float32', audioData, [1, audioData.length]);
      const srTensor = new ort.Tensor('int64', BigInt64Array.from([BigInt(this.sampleRate)]), [1]);
      const hTensor = new ort.Tensor('float32', Float32Array.from(this.h), [2, 1, 64]);
      const cTensor = new ort.Tensor('float32', Float32Array.from(this.c), [2, 1, 64]);

      // Run inference
      const output = await this.session.run({
        input: inputTensor,
        sr: srTensor,
        h: hTensor,
        c: cTensor
      });

      // Update hidden states for next call
      this.h = Array.from(output.hn.data);
      this.c = Array.from(output.cn.data);

      // Return speech probability (0-1)
      return output.output.data[0];
    } catch (error) {
      console.error('VAD prediction error:', error);
      throw error;
    }
  }

  isLoaded() {
    return this.session !== null;
  }
}
