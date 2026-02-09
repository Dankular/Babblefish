// Audio playback manager for TTS
// Handles queuing, mixing, and playback of synthesized speech

export class AudioPlayback {
  constructor() {
    this.audioContext = null;
    this.queue = [];
    this.currentSource = null;
    this.isPlaying = false;
    this.volume = 1.0;
    this.gainNode = null;
    this.onPlaybackStart = null;
    this.onPlaybackEnd = null;
    this.onQueueChange = null;
  }

  /**
   * Initialize audio context
   */
  async initialize() {
    if (this.audioContext) {
      console.log('[AudioPlayback] Already initialized');
      return;
    }

    try {
      // Create audio context
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

      // Create gain node for volume control
      this.gainNode = this.audioContext.createGain();
      this.gainNode.gain.value = this.volume;
      this.gainNode.connect(this.audioContext.destination);

      console.log(`[AudioPlayback] Initialized (sample rate: ${this.audioContext.sampleRate}Hz)`);
    } catch (error) {
      console.error('[AudioPlayback] Initialization failed:', error);
      throw new Error(`Failed to initialize audio playback: ${error.message}`);
    }
  }

  /**
   * Add audio to playback queue
   * @param {Float32Array} audioData - Audio samples
   * @param {number} sampleRate - Sample rate of audio
   * @param {Object} metadata - Additional metadata (speaker, language, etc.)
   */
  async enqueue(audioData, sampleRate, metadata = {}) {
    if (!this.audioContext) {
      await this.initialize();
    }

    // Resume audio context if suspended (browser autoplay policy)
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    const queueItem = {
      audioData,
      sampleRate,
      metadata,
      timestamp: Date.now(),
    };

    this.queue.push(queueItem);
    console.log(`[AudioPlayback] Enqueued audio (${audioData.length} samples, queue size: ${this.queue.length})`);

    this.notifyQueueChange();

    // Start playback if not already playing
    if (!this.isPlaying) {
      this.playNext();
    }
  }

  /**
   * Play next item in queue
   * @private
   */
  async playNext() {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      console.log('[AudioPlayback] Queue empty, stopping playback');
      return;
    }

    this.isPlaying = true;
    const item = this.queue.shift();
    this.notifyQueueChange();

    try {
      await this.playAudio(item.audioData, item.sampleRate, item.metadata);
    } catch (error) {
      console.error('[AudioPlayback] Playback error:', error);
    }

    // Play next item
    this.playNext();
  }

  /**
   * Play audio data
   * @private
   */
  async playAudio(audioData, sampleRate, metadata = {}) {
    if (!this.audioContext) {
      throw new Error('Audio context not initialized');
    }

    return new Promise((resolve) => {
      try {
        // Create audio buffer
        const audioBuffer = this.audioContext.createBuffer(
          1, // mono
          audioData.length,
          sampleRate
        );

        // Copy audio data to buffer
        audioBuffer.getChannelData(0).set(audioData);

        // Create source node
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.gainNode);

        // Set current source
        this.currentSource = source;

        // Handle playback end
        source.onended = () => {
          this.currentSource = null;
          if (this.onPlaybackEnd) {
            this.onPlaybackEnd(metadata);
          }
          resolve();
        };

        // Start playback
        source.start(0);

        const duration = audioData.length / sampleRate;
        console.log(`[AudioPlayback] Playing audio (${duration.toFixed(2)}s, ${metadata.speaker || 'unknown'})`);

        if (this.onPlaybackStart) {
          this.onPlaybackStart(metadata, duration);
        }
      } catch (error) {
        console.error('[AudioPlayback] Play error:', error);
        resolve();
      }
    });
  }

  /**
   * Stop current playback
   */
  stop() {
    if (this.currentSource) {
      try {
        this.currentSource.stop();
        this.currentSource = null;
      } catch (error) {
        console.error('[AudioPlayback] Stop error:', error);
      }
    }
    this.isPlaying = false;
  }

  /**
   * Clear playback queue
   */
  clearQueue() {
    console.log(`[AudioPlayback] Clearing queue (${this.queue.length} items)`);
    this.queue = [];
    this.notifyQueueChange();
  }

  /**
   * Set volume (0.0 to 1.0)
   */
  setVolume(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    if (this.gainNode) {
      this.gainNode.gain.value = this.volume;
    }
    console.log(`[AudioPlayback] Volume set to ${(this.volume * 100).toFixed(0)}%`);
  }

  /**
   * Get current volume
   */
  getVolume() {
    return this.volume;
  }

  /**
   * Get queue size
   */
  getQueueSize() {
    return this.queue.length;
  }

  /**
   * Check if audio is playing
   */
  getIsPlaying() {
    return this.isPlaying;
  }

  /**
   * Get audio context state
   */
  getState() {
    return this.audioContext ? this.audioContext.state : 'closed';
  }

  /**
   * Notify queue change
   * @private
   */
  notifyQueueChange() {
    if (this.onQueueChange) {
      this.onQueueChange(this.queue.length);
    }
  }

  /**
   * Cleanup resources
   */
  async dispose() {
    console.log('[AudioPlayback] Disposing...');

    this.stop();
    this.clearQueue();

    if (this.gainNode) {
      this.gainNode.disconnect();
      this.gainNode = null;
    }

    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }
  }
}
