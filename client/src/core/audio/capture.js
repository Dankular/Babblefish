// getUserMedia microphone capture
export class AudioCapture {
  constructor(onAudioData) {
    this.onAudioData = onAudioData;
    this.stream = null;
    this.audioContext = null;
    this.sourceNode = null;
    this.processorNode = null;
    this.isCapturing = false;

    // Audio settings
    this.sampleRate = 16000;
  }

  async start() {
    try {
      // Request microphone access
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: this.sampleRate,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      // Create audio context
      this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
      this.sourceNode = this.audioContext.createMediaStreamSource(this.stream);

      // Create ScriptProcessor for audio processing
      // Using 4096 buffer size for compatibility
      const bufferSize = 4096;
      this.processorNode = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

      this.processorNode.onaudioprocess = (event) => {
        if (!this.isCapturing) return;

        const inputData = event.inputBuffer.getChannelData(0);
        const audioData = new Float32Array(inputData);

        // Resample if needed (AudioContext may not respect requested sample rate)
        if (this.audioContext.sampleRate !== this.sampleRate) {
          const resampled = this.resample(audioData, this.audioContext.sampleRate, this.sampleRate);
          this.onAudioData(resampled);
        } else {
          this.onAudioData(audioData);
        }
      };

      // Connect nodes
      this.sourceNode.connect(this.processorNode);
      this.processorNode.connect(this.audioContext.destination);

      this.isCapturing = true;
      console.log(`Audio capture started: ${this.audioContext.sampleRate}Hz`);
    } catch (error) {
      console.error('Failed to start audio capture:', error);
      throw error;
    }
  }

  stop() {
    this.isCapturing = false;

    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode = null;
    }

    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    console.log('Audio capture stopped');
  }

  resample(audioData, fromRate, toRate) {
    if (fromRate === toRate) return audioData;

    const ratio = fromRate / toRate;
    const newLength = Math.round(audioData.length / ratio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
      const srcIndex = i * ratio;
      const srcIndexFloor = Math.floor(srcIndex);
      const srcIndexCeil = Math.min(srcIndexFloor + 1, audioData.length - 1);
      const frac = srcIndex - srcIndexFloor;

      result[i] = audioData[srcIndexFloor] * (1 - frac) + audioData[srcIndexCeil] * frac;
    }

    return result;
  }

  getState() {
    return {
      isCapturing: this.isCapturing,
      sampleRate: this.audioContext?.sampleRate || this.sampleRate
    };
  }
}
