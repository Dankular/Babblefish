// Voice Enrollment Logic
// Handles recording and processing of voice reference audio for F5-TTS

/**
 * Voice Enrollment Manager
 *
 * Manages the process of recording, validating, and processing
 * voice reference audio for voice cloning.
 */
export class VoiceEnrollment {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.audioContext = null;
    this.analyser = null;
    this.isRecording = false;
    this.recordingStartTime = null;
    this.minDuration = 5000; // 5 seconds minimum
    this.maxDuration = 15000; // 15 seconds maximum
    this.targetSampleRate = 24000; // F5-TTS expects 24kHz
  }

  /**
   * Start recording voice reference
   * @returns {Promise<void>}
   */
  async startRecording() {
    if (this.isRecording) {
      console.warn('[VoiceEnrollment] Already recording');
      return;
    }

    try {
      console.log('[VoiceEnrollment] Starting voice enrollment recording...');

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 48000, // Request high quality, will downsample later
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Create audio context for analysis
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 48000,
      });

      const source = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      source.connect(this.analyser);

      // Set up media recorder
      const mimeType = this.selectMimeType();
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.start(100); // Collect data every 100ms
      this.isRecording = true;
      this.recordingStartTime = Date.now();

      console.log('[VoiceEnrollment] Recording started');
    } catch (error) {
      console.error('[VoiceEnrollment] Failed to start recording:', error);
      throw new Error(`Failed to start recording: ${error.message}`);
    }
  }

  /**
   * Stop recording and return audio blob
   * @returns {Promise<Blob>} Recorded audio as Blob
   */
  async stopRecording() {
    if (!this.isRecording || !this.mediaRecorder) {
      console.warn('[VoiceEnrollment] Not currently recording');
      return null;
    }

    return new Promise((resolve, reject) => {
      this.mediaRecorder.onstop = async () => {
        try {
          const duration = Date.now() - this.recordingStartTime;
          console.log(`[VoiceEnrollment] Recording stopped (${duration}ms)`);

          // Create blob from chunks
          const mimeType = this.mediaRecorder.mimeType;
          const audioBlob = new Blob(this.audioChunks, { type: mimeType });

          // Stop all tracks
          this.mediaRecorder.stream.getTracks().forEach(track => track.stop());

          // Cleanup
          if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
          }

          this.isRecording = false;
          this.mediaRecorder = null;
          this.analyser = null;
          this.audioChunks = [];

          resolve(audioBlob);
        } catch (error) {
          console.error('[VoiceEnrollment] Error stopping recording:', error);
          reject(error);
        }
      };

      this.mediaRecorder.stop();
    });
  }

  /**
   * Cancel recording without saving
   */
  async cancelRecording() {
    if (!this.isRecording || !this.mediaRecorder) {
      return;
    }

    console.log('[VoiceEnrollment] Canceling recording...');

    // Stop all tracks
    if (this.mediaRecorder.stream) {
      this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }

    // Cleanup
    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }

    this.isRecording = false;
    this.mediaRecorder = null;
    this.analyser = null;
    this.audioChunks = [];
  }

  /**
   * Get current recording duration in milliseconds
   * @returns {number}
   */
  getRecordingDuration() {
    if (!this.isRecording || !this.recordingStartTime) {
      return 0;
    }
    return Date.now() - this.recordingStartTime;
  }

  /**
   * Get current audio level for visualization (0.0 to 1.0)
   * @returns {number}
   */
  getAudioLevel() {
    if (!this.analyser) {
      return 0.0;
    }

    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteTimeDomainData(dataArray);

    // Calculate RMS
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      const normalized = (dataArray[i] - 128) / 128;
      sum += normalized * normalized;
    }
    const rms = Math.sqrt(sum / dataArray.length);

    return Math.min(1.0, rms * 3); // Scale up for visibility
  }

  /**
   * Validate recorded audio
   * @param {Blob} audioBlob - Recorded audio blob
   * @returns {Promise<Object>} Validation result
   */
  async validateAudio(audioBlob) {
    console.log('[VoiceEnrollment] Validating audio...');

    const validation = {
      valid: true,
      duration: 0,
      sampleRate: 0,
      channels: 0,
      issues: [],
    };

    try {
      // Decode audio to get metadata
      const audioBuffer = await this.decodeAudioBlob(audioBlob);

      validation.duration = audioBuffer.duration * 1000; // Convert to ms
      validation.sampleRate = audioBuffer.sampleRate;
      validation.channels = audioBuffer.numberOfChannels;

      // Check duration
      if (validation.duration < this.minDuration) {
        validation.valid = false;
        validation.issues.push(`Recording too short (${(validation.duration / 1000).toFixed(1)}s, minimum ${this.minDuration / 1000}s)`);
      }

      if (validation.duration > this.maxDuration) {
        validation.valid = false;
        validation.issues.push(`Recording too long (${(validation.duration / 1000).toFixed(1)}s, maximum ${this.maxDuration / 1000}s)`);
      }

      // Check for silence
      const channelData = audioBuffer.getChannelData(0);
      const avgLevel = this.calculateAverageLevel(channelData);

      if (avgLevel < 0.01) {
        validation.valid = false;
        validation.issues.push('Recording is too quiet or silent');
      }

      if (validation.valid) {
        console.log('[VoiceEnrollment] Audio validation passed');
      } else {
        console.warn('[VoiceEnrollment] Audio validation failed:', validation.issues);
      }

      return validation;
    } catch (error) {
      console.error('[VoiceEnrollment] Validation error:', error);
      return {
        valid: false,
        issues: [`Validation error: ${error.message}`],
      };
    }
  }

  /**
   * Process audio for F5-TTS format
   * @param {Blob} audioBlob - Recorded audio blob
   * @returns {Promise<Object>} Processed audio data
   */
  async processAudio(audioBlob) {
    console.log('[VoiceEnrollment] Processing audio for F5-TTS...');

    try {
      // Decode audio
      const audioBuffer = await this.decodeAudioBlob(audioBlob);

      // Get mono channel data
      const channelData = audioBuffer.getChannelData(0);

      // Resample to target sample rate if needed
      let processedData = channelData;
      if (audioBuffer.sampleRate !== this.targetSampleRate) {
        console.log(`[VoiceEnrollment] Resampling from ${audioBuffer.sampleRate}Hz to ${this.targetSampleRate}Hz`);
        processedData = await this.resample(channelData, audioBuffer.sampleRate, this.targetSampleRate);
      }

      // Normalize audio
      processedData = this.normalizeAudio(processedData);

      // Convert to ArrayBuffer for storage
      const arrayBuffer = processedData.buffer.slice(
        processedData.byteOffset,
        processedData.byteOffset + processedData.byteLength
      );

      console.log(`[VoiceEnrollment] Processed ${processedData.length} samples @ ${this.targetSampleRate}Hz`);

      return {
        audioData: arrayBuffer,
        sampleRate: this.targetSampleRate,
        duration: processedData.length / this.targetSampleRate,
        samples: processedData.length,
      };
    } catch (error) {
      console.error('[VoiceEnrollment] Processing error:', error);
      throw new Error(`Failed to process audio: ${error.message}`);
    }
  }

  /**
   * Decode audio blob to AudioBuffer
   * @private
   */
  async decodeAudioBlob(blob) {
    const arrayBuffer = await blob.arrayBuffer();
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    await audioContext.close();
    return audioBuffer;
  }

  /**
   * Resample audio data
   * @private
   */
  async resample(inputData, inputRate, outputRate) {
    if (inputRate === outputRate) {
      return inputData;
    }

    const ratio = outputRate / inputRate;
    const outputLength = Math.floor(inputData.length * ratio);
    const outputData = new Float32Array(outputLength);

    // Simple linear interpolation
    for (let i = 0; i < outputLength; i++) {
      const srcIndex = i / ratio;
      const srcIndexFloor = Math.floor(srcIndex);
      const srcIndexCeil = Math.min(srcIndexFloor + 1, inputData.length - 1);
      const t = srcIndex - srcIndexFloor;

      outputData[i] = inputData[srcIndexFloor] * (1 - t) + inputData[srcIndexCeil] * t;
    }

    return outputData;
  }

  /**
   * Normalize audio to -1.0 to 1.0 range
   * @private
   */
  normalizeAudio(audioData) {
    // Find max absolute value without spread operator (avoids stack overflow)
    let maxAbs = 0;
    for (let i = 0; i < audioData.length; i++) {
      const abs = Math.abs(audioData[i]);
      if (abs > maxAbs) {
        maxAbs = abs;
      }
    }

    if (maxAbs === 0 || maxAbs === 1.0) {
      return audioData;
    }

    const normalized = new Float32Array(audioData.length);
    const scale = 0.95 / maxAbs; // Leave some headroom

    for (let i = 0; i < audioData.length; i++) {
      normalized[i] = audioData[i] * scale;
    }

    return normalized;
  }

  /**
   * Calculate average audio level
   * @private
   */
  calculateAverageLevel(audioData) {
    let sum = 0;
    for (let i = 0; i < audioData.length; i++) {
      sum += Math.abs(audioData[i]);
    }
    return sum / audioData.length;
  }

  /**
   * Select best available MIME type for recording
   * @private
   */
  selectMimeType() {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/ogg',
      'audio/mp4',
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        console.log(`[VoiceEnrollment] Using MIME type: ${type}`);
        return type;
      }
    }

    console.warn('[VoiceEnrollment] No preferred MIME types supported, using default');
    return '';
  }

  /**
   * Check if recording is in progress
   * @returns {boolean}
   */
  get recording() {
    return this.isRecording;
  }
}
