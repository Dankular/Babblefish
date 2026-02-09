// Chatterbox Multilingual TTS Engine
// Uses ONNX Runtime Web for in-browser inference
import * as ort from 'onnxruntime-web';

const MODEL_BASE_URL = 'https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX/resolve/main';
const SAMPLE_RATE = 24000; // Chatterbox outputs 24kHz audio

// Language mapping for Chatterbox Multilingual
// ISO 639-1 code to Chatterbox language ID
const LANGUAGE_MAP = {
  'en': 'en', // English
  'es': 'es', // Spanish
  'fr': 'fr', // French
  'de': 'de', // German
  'it': 'it', // Italian
  'pt': 'pt', // Portuguese
  'pl': 'pl', // Polish
  'tr': 'tr', // Turkish
  'ru': 'ru', // Russian
  'nl': 'nl', // Dutch
  'cs': 'cs', // Czech
  'ar': 'ar', // Arabic
  'zh': 'zh', // Chinese (Mandarin)
  'ja': 'ja', // Japanese
  'ko': 'ko', // Korean
  'hi': 'hi', // Hindi
  'bn': 'bn', // Bengali
  'ta': 'ta', // Tamil
  'te': 'te', // Telugu
  'uk': 'uk', // Ukrainian
  'vi': 'vi', // Vietnamese
  'th': 'th', // Thai
  'id': 'id', // Indonesian
};

export class ChatterboxTTS {
  constructor(onProgress = null) {
    this.session = null;
    this.vocoder = null;
    this.isLoading = false;
    this.isReady = false;
    this.onProgress = onProgress;
    this.sampleRate = SAMPLE_RATE;
  }

  /**
   * Initialize the TTS engine
   * @param {boolean} useWebGPU - Try to use WebGPU if available
   */
  async initialize(useWebGPU = true) {
    if (this.isReady) {
      console.log('[ChatterboxTTS] Already initialized');
      return;
    }

    if (this.isLoading) {
      console.log('[ChatterboxTTS] Already loading');
      return;
    }

    this.isLoading = true;
    console.log('[ChatterboxTTS] Starting initialization...');

    try {
      // Configure execution provider
      const executionProviders = useWebGPU ? ['webgpu', 'wasm'] : ['wasm'];

      // Report progress
      this.reportProgress('Downloading encoder model...', 0.1);

      // Load encoder model (text -> mel spectrogram)
      console.log('[ChatterboxTTS] Loading encoder model...');
      this.session = await ort.InferenceSession.create(
        `${MODEL_BASE_URL}/encoder_model.onnx`,
        {
          executionProviders,
          graphOptimizationLevel: 'all',
        }
      );

      this.reportProgress('Downloading vocoder model...', 0.5);

      // Load vocoder model (mel spectrogram -> audio)
      console.log('[ChatterboxTTS] Loading vocoder model...');
      this.vocoder = await ort.InferenceSession.create(
        `${MODEL_BASE_URL}/decoder_model.onnx`,
        {
          executionProviders,
          graphOptimizationLevel: 'all',
        }
      );

      this.reportProgress('Models loaded successfully', 1.0);
      this.isReady = true;
      this.isLoading = false;

      const provider = this.session.handler.executionProviders?.[0] || 'unknown';
      console.log(`[ChatterboxTTS] Initialized successfully using ${provider}`);
    } catch (error) {
      this.isLoading = false;
      console.error('[ChatterboxTTS] Initialization failed:', error);
      throw new Error(`Failed to initialize Chatterbox TTS: ${error.message}`);
    }
  }

  /**
   * Synthesize speech from text
   * @param {string} text - Text to synthesize
   * @param {string} language - Language code (ISO 639-1)
   * @returns {Promise<Float32Array>} Audio samples
   */
  async synthesize(text, language = 'en') {
    if (!this.isReady) {
      throw new Error('TTS engine not initialized. Call initialize() first.');
    }

    if (!text || text.trim().length === 0) {
      console.warn('[ChatterboxTTS] Empty text provided');
      return new Float32Array(0);
    }

    // Map language code
    const langId = LANGUAGE_MAP[language] || 'en';
    console.log(`[ChatterboxTTS] Synthesizing: "${text.substring(0, 50)}..." (${langId})`);

    try {
      // Tokenize text (simplified - in production would use proper tokenizer)
      const tokens = this.tokenizeText(text, langId);

      // Create input tensors
      const inputIds = new ort.Tensor('int64', BigInt64Array.from(tokens.map(BigInt)), [1, tokens.length]);

      // Run encoder (text -> mel spectrogram)
      console.log('[ChatterboxTTS] Running encoder...');
      const encoderOutputs = await this.session.run({ input_ids: inputIds });
      const melSpec = encoderOutputs.mel_spectrogram;

      // Run vocoder (mel spectrogram -> audio)
      console.log('[ChatterboxTTS] Running vocoder...');
      const vocoderOutputs = await this.vocoder.run({ mel_spectrogram: melSpec });
      const audioTensor = vocoderOutputs.audio;

      // Convert to Float32Array
      const audioData = new Float32Array(audioTensor.data);

      console.log(`[ChatterboxTTS] Generated ${audioData.length} samples (${(audioData.length / this.sampleRate).toFixed(2)}s)`);
      return audioData;
    } catch (error) {
      console.error('[ChatterboxTTS] Synthesis failed:', error);
      throw new Error(`TTS synthesis failed: ${error.message}`);
    }
  }

  /**
   * Simple tokenization (placeholder - real implementation would use SentencePiece)
   * @private
   */
  tokenizeText(text, language) {
    // This is a simplified tokenizer
    // In production, would use the actual Chatterbox tokenizer model
    const chars = text.toLowerCase().split('');
    const tokens = chars.map(char => {
      const code = char.charCodeAt(0);
      // Map to token IDs (simplified)
      if (code >= 97 && code <= 122) { // a-z
        return code - 97 + 1;
      } else if (code === 32) { // space
        return 0;
      } else {
        return 27; // unknown token
      }
    });
    return tokens;
  }

  /**
   * Check if a language is supported
   * @param {string} language - ISO 639-1 language code
   * @returns {boolean}
   */
  isLanguageSupported(language) {
    return language in LANGUAGE_MAP;
  }

  /**
   * Get list of supported languages
   * @returns {string[]} Array of ISO 639-1 codes
   */
  getSupportedLanguages() {
    return Object.keys(LANGUAGE_MAP);
  }

  /**
   * Get sample rate of generated audio
   * @returns {number}
   */
  getSampleRate() {
    return this.sampleRate;
  }

  /**
   * Report progress to callback
   * @private
   */
  reportProgress(message, progress) {
    if (this.onProgress) {
      this.onProgress({ message, progress });
    }
  }

  /**
   * Cleanup resources
   */
  async dispose() {
    console.log('[ChatterboxTTS] Disposing resources...');

    if (this.session) {
      await this.session.release();
      this.session = null;
    }

    if (this.vocoder) {
      await this.vocoder.release();
      this.vocoder = null;
    }

    this.isReady = false;
    this.isLoading = false;
  }
}
