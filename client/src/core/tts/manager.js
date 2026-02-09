// TTS Manager - Strategy pattern for multiple TTS engines
import { ChatterboxTTS } from './chatterbox.js';
import { F5TTS } from './f5tts.js';

const TTS_ENGINE = {
  CHATTERBOX: 'chatterbox',
  F5: 'f5', // Phase 3: Voice cloning
};

export class TTSManager {
  constructor(onProgress = null) {
    this.engine = null;
    this.engineType = null;
    this.isInitialized = false;
    this.isInitializing = false;
    this.queue = [];
    this.isProcessing = false;
    this.onProgress = onProgress;
    this.maxQueueSize = 10;
  }

  /**
   * Initialize TTS engine based on device capabilities
   * @param {string} preferredEngine - Preferred engine type
   * @param {boolean} fallbackOnError - Fallback to Chatterbox if F5 fails
   */
  async initialize(preferredEngine = TTS_ENGINE.CHATTERBOX, fallbackOnError = true) {
    if (this.isInitialized) {
      console.log('[TTSManager] Already initialized');
      return;
    }

    if (this.isInitializing) {
      console.log('[TTSManager] Already initializing');
      return;
    }

    this.isInitializing = true;
    console.log(`[TTSManager] Initializing with engine: ${preferredEngine}`);

    try {
      // Detect WebGPU support
      const hasWebGPU = await this.detectWebGPU();
      console.log(`[TTSManager] WebGPU available: ${hasWebGPU}`);

      // Detect device capabilities for F5-TTS
      const hasF5Support = await this.detectF5Support(hasWebGPU);

      // Initialize appropriate engine
      let actualEngine = preferredEngine;

      // If F5 requested but not supported, fallback to Chatterbox
      if (preferredEngine === TTS_ENGINE.F5 && !hasF5Support && fallbackOnError) {
        console.warn('[TTSManager] F5-TTS not supported, falling back to Chatterbox');
        actualEngine = TTS_ENGINE.CHATTERBOX;
      }

      switch (actualEngine) {
        case TTS_ENGINE.CHATTERBOX:
          this.engine = new ChatterboxTTS(this.onProgress);
          await this.engine.initialize(hasWebGPU);
          this.engineType = TTS_ENGINE.CHATTERBOX;
          break;

        case TTS_ENGINE.F5:
          // Phase 3: F5-TTS implementation
          try {
            this.engine = new F5TTS(this.onProgress);
            await this.engine.initialize(hasWebGPU);
            this.engineType = TTS_ENGINE.F5;
          } catch (error) {
            if (fallbackOnError) {
              console.warn('[TTSManager] F5-TTS failed, falling back to Chatterbox:', error);
              this.engine = new ChatterboxTTS(this.onProgress);
              await this.engine.initialize(hasWebGPU);
              this.engineType = TTS_ENGINE.CHATTERBOX;
            } else {
              throw error;
            }
          }
          break;

        default:
          throw new Error(`Unknown TTS engine: ${preferredEngine}`);
      }

      this.isInitialized = true;
      this.isInitializing = false;
      console.log(`[TTSManager] Successfully initialized ${this.engineType} engine`);
    } catch (error) {
      this.isInitializing = false;
      console.error('[TTSManager] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Detect WebGPU support
   * @private
   */
  async detectWebGPU() {
    if (!navigator.gpu) {
      return false;
    }

    try {
      const adapter = await navigator.gpu.requestAdapter();
      return adapter !== null;
    } catch (error) {
      console.warn('[TTSManager] WebGPU detection failed:', error);
      return false;
    }
  }

  /**
   * Detect F5-TTS support (requires WebGPU + sufficient memory)
   * @private
   */
  async detectF5Support(hasWebGPU) {
    // F5-TTS requires:
    // 1. WebGPU for reasonable performance
    // 2. At least 4GB RAM (models are ~300MB, need memory for inference)

    if (!hasWebGPU) {
      console.log('[TTSManager] F5-TTS requires WebGPU');
      return false;
    }

    // Check memory (if available)
    if (navigator.deviceMemory && navigator.deviceMemory < 4) {
      console.log(`[TTSManager] F5-TTS requires 4GB+ RAM (detected: ${navigator.deviceMemory}GB)`);
      return false;
    }

    console.log('[TTSManager] Device meets F5-TTS requirements');
    return true;
  }

  /**
   * Synthesize text to speech
   * @param {string} text - Text to synthesize
   * @param {string} language - Language code
   * @param {Object} options - Additional options
   * @returns {Promise<Float32Array>} Audio samples
   */
  async synthesize(text, language, options = {}) {
    if (!this.isInitialized) {
      throw new Error('TTS Manager not initialized. Call initialize() first.');
    }

    if (!text || text.trim().length === 0) {
      console.warn('[TTSManager] Empty text provided');
      return new Float32Array(0);
    }

    // Check language support
    if (this.engine.isLanguageSupported && !this.engine.isLanguageSupported(language)) {
      console.warn(`[TTSManager] Language ${language} not supported, falling back to English`);
      language = 'en';
    }

    try {
      const audioData = await this.engine.synthesize(text, language, options);
      return audioData;
    } catch (error) {
      console.error('[TTSManager] Synthesis failed:', error);
      throw error;
    }
  }

  /**
   * Add synthesis request to queue
   * @param {Object} request - Synthesis request
   * @returns {Promise<Float32Array>}
   */
  async queueSynthesis(request) {
    return new Promise((resolve, reject) => {
      // Check queue size
      if (this.queue.length >= this.maxQueueSize) {
        console.warn('[TTSManager] Queue full, dropping oldest request');
        this.queue.shift();
      }

      // Add to queue
      this.queue.push({
        ...request,
        resolve,
        reject,
      });

      console.log(`[TTSManager] Queued synthesis request (queue size: ${this.queue.length})`);

      // Process queue
      this.processQueue();
    });
  }

  /**
   * Process synthesis queue
   * @private
   */
  async processQueue() {
    if (this.isProcessing || this.queue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.queue.length > 0) {
      const request = this.queue.shift();

      try {
        console.log(`[TTSManager] Processing queued request (${this.queue.length} remaining)`);
        const audioData = await this.synthesize(
          request.text,
          request.language,
          request.options
        );
        request.resolve(audioData);
      } catch (error) {
        console.error('[TTSManager] Queued synthesis failed:', error);
        request.reject(error);
      }
    }

    this.isProcessing = false;
  }

  /**
   * Clear synthesis queue
   */
  clearQueue() {
    console.log(`[TTSManager] Clearing queue (${this.queue.length} items)`);
    this.queue.forEach(request => {
      request.reject(new Error('Queue cleared'));
    });
    this.queue = [];
  }

  /**
   * Get queue size
   */
  getQueueSize() {
    return this.queue.length;
  }

  /**
   * Get current engine type
   */
  getEngineType() {
    return this.engineType;
  }

  /**
   * Get sample rate
   */
  getSampleRate() {
    if (!this.engine) {
      return 24000; // Default for Chatterbox
    }
    return this.engine.getSampleRate ? this.engine.getSampleRate() : 24000;
  }

  /**
   * Check if language is supported
   */
  isLanguageSupported(language) {
    if (!this.engine) {
      return false;
    }
    return this.engine.isLanguageSupported ? this.engine.isLanguageSupported(language) : false;
  }

  /**
   * Get supported languages
   */
  getSupportedLanguages() {
    if (!this.engine) {
      return [];
    }
    return this.engine.getSupportedLanguages ? this.engine.getSupportedLanguages() : [];
  }

  /**
   * Cleanup resources
   */
  async dispose() {
    console.log('[TTSManager] Disposing...');

    this.clearQueue();

    if (this.engine && this.engine.dispose) {
      await this.engine.dispose();
    }

    this.engine = null;
    this.engineType = null;
    this.isInitialized = false;
    this.isInitializing = false;
  }
}

export { TTS_ENGINE };
