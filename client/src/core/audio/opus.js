// Opus encoding via MediaRecorder
export class OpusEncoder {
  constructor() {
    this.sampleRate = 16000;
    this.mimeType = 'audio/webm;codecs=opus';

    // Check if Opus is supported
    if (!MediaRecorder.isTypeSupported(this.mimeType)) {
      console.warn('Opus codec not supported, falling back to default');
      this.mimeType = 'audio/webm';
    }
  }

  async encode(audioData) {
    try {
      // Convert Float32Array to AudioBuffer
      const audioBuffer = this.createAudioBuffer(audioData);

      // Create MediaStream from AudioBuffer
      const mediaStream = this.audioBufferToMediaStream(audioBuffer);

      // Record to Opus
      const opusBlob = await this.recordToOpus(mediaStream);

      // Convert to base64 for WebSocket transmission
      const base64 = await this.blobToBase64(opusBlob);

      return base64;
    } catch (error) {
      console.error('Opus encoding error:', error);
      throw error;
    }
  }

  createAudioBuffer(audioData) {
    const audioContext = new OfflineAudioContext(1, audioData.length, this.sampleRate);
    const audioBuffer = audioContext.createBuffer(1, audioData.length, this.sampleRate);
    audioBuffer.getChannelData(0).set(audioData);
    return audioBuffer;
  }

  audioBufferToMediaStream(audioBuffer) {
    const audioContext = new AudioContext({ sampleRate: this.sampleRate });
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;

    const destination = audioContext.createMediaStreamDestination();
    source.connect(destination);
    source.start();

    return destination.stream;
  }

  recordToOpus(mediaStream) {
    return new Promise((resolve, reject) => {
      const chunks = [];
      const mediaRecorder = new MediaRecorder(mediaStream, {
        mimeType: this.mimeType
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: this.mimeType });
        resolve(blob);
      };

      mediaRecorder.onerror = (error) => {
        reject(error);
      };

      mediaRecorder.start();

      // Stop after a short delay to capture the audio
      setTimeout(() => {
        mediaRecorder.stop();
        mediaStream.getTracks().forEach(track => track.stop());
      }, 100);
    });
  }

  blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
}
