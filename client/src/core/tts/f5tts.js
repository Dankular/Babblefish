// F5-TTS ONNX Engine for Voice Cloning
import * as ort from 'onnxruntime-web';

/**
 * F5-TTS Voice Cloning Engine
 *
 * Uses ONNX Runtime Web to run F5-TTS models in the browser.
 * Supports voice cloning with reference audio.
 *
 * Architecture:
 * - Text Encoder: Converts text to embeddings
 * - Duration Predictor: Predicts phoneme durations
 * - Acoustic Model: Generates mel spectrogram with voice conditioning
 * - Vocoder: Converts mel spectrogram to audio waveform
 */
export class F5TTS {
  constructor(onProgress = null) {
    this.preprocess = null;
    this.transformer = null;
    this.decoder = null;
    this.isInitialized = false;
    this.onProgress = onProgress;
    this.sampleRate = 24000;

    // F5-TTS ONNX Model URLs from huggingfacess/F5-TTS-ONNX
    // Three-stage pipeline: Preprocess → Transformer → Decode
    this.modelUrls = {
      preprocess: 'https://huggingface.co/huggingfacess/F5-TTS-ONNX/resolve/main/F5_Preprocess.ort',
      transformer: 'https://huggingface.co/huggingfacess/F5-TTS-ONNX/resolve/main/F5_Transformer.ort',
      decoder: 'https://huggingface.co/huggingfacess/F5-TTS-ONNX/resolve/main/F5_Decode.ort',
    };
  }

  /**
   * Initialize F5-TTS models
   * @param {boolean} useWebGPU - Whether to use WebGPU execution provider
   */
  async initialize(useWebGPU = true) {
    if (this.isInitialized) {
      console.log('[F5TTS] Already initialized');
      return;
    }

    console.log('[F5TTS] Initializing F5-TTS models...');
    this.reportProgress('Initializing F5-TTS...', 0.0);

    try {
      // Configure execution providers
      const executionProviders = useWebGPU
        ? ['webgpu', 'wasm']
        : ['wasm'];

      console.log(`[F5TTS] Using execution providers: ${executionProviders.join(', ')}`);

      // Load F5-TTS three-stage pipeline
      // Stage 1: Preprocess (text → preprocessed features)
      this.reportProgress('Loading F5-TTS preprocessor...', 0.1);
      console.log('[F5TTS] Loading F5_Preprocess model...');
      this.preprocess = await ort.InferenceSession.create(
        this.modelUrls.preprocess,
        { executionProviders }
      );

      // Stage 2: Transformer (main model with voice conditioning)
      this.reportProgress('Loading F5-TTS transformer...', 0.4);
      console.log('[F5TTS] Loading F5_Transformer model (~1281 nodes)...');
      this.transformer = await ort.InferenceSession.create(
        this.modelUrls.transformer,
        { executionProviders }
      );

      // Stage 3: Decoder (mel spectrogram → audio waveform)
      this.reportProgress('Loading F5-TTS decoder...', 0.8);
      console.log('[F5TTS] Loading F5_Decode model...');
      this.decoder = await ort.InferenceSession.create(
        this.modelUrls.decoder,
        { executionProviders }
      );

      this.reportProgress('F5-TTS ready', 1.0);
      this.isInitialized = true;
      console.log('[F5TTS] F5-TTS ONNX models loaded successfully');

    } catch (error) {
      console.error('[F5TTS] Initialization failed:', error);
      throw new Error(`F5-TTS initialization failed: ${error.message}`);
    }
  }

  /**
   * Synthesize speech with voice cloning
   * @param {string} text - Text to synthesize
   * @param {string} language - Language code (ISO 639-1)
   * @param {Object} options - Synthesis options
   * @param {ArrayBuffer|Float32Array} options.voiceReference - Voice reference audio
   * @param {number} options.voiceReferenceRate - Sample rate of voice reference
   * @returns {Promise<Float32Array>} Audio samples at 24kHz
   */
  async synthesize(text, language = 'en', options = {}) {
    if (!this.isInitialized) {
      throw new Error('F5-TTS not initialized. Call initialize() first.');
    }

    if (!text || text.trim().length === 0) {
      console.warn('[F5TTS] Empty text provided');
      return new Float32Array(0);
    }

    const { voiceReference, voiceReferenceRate = 24000 } = options;

    if (!voiceReference) {
      console.warn('[F5TTS] No voice reference provided, voice cloning may not work properly');
    }

    try {
      console.log(`[F5TTS] Synthesizing: "${text.substring(0, 50)}..." (${language})`);

      // F5-TTS Three-Stage Pipeline:

      // Stage 1: Preprocess text and voice reference
      const preprocessInputs = this.preparePreprocessInputs(text, voiceReference);
      const preprocessOutputs = await this.preprocess.run(preprocessInputs);

      // Stage 2: Transformer with voice conditioning
      const transformerInputs = {
        // Map preprocess outputs to transformer inputs
        // Input names depend on actual model - may need adjustment
        ...preprocessOutputs
      };
      const transformerOutputs = await this.transformer.run(transformerInputs);

      // Stage 3: Decode mel spectrogram to audio waveform
      const decoderInputs = {
        // Map transformer outputs to decoder inputs
        ...transformerOutputs
      };
      const decoderOutputs = await this.decoder.run(decoderInputs);

      // Extract audio data from decoder output
      // Output tensor name may vary - typically 'audio' or 'waveform'
      const outputTensor = decoderOutputs[Object.keys(decoderOutputs)[0]];
      const audioData = new Float32Array(outputTensor.data);

      console.log(`[F5TTS] Generated ${(audioData.length / this.sampleRate).toFixed(2)}s of audio`);
      return audioData;

    } catch (error) {
      console.error('[F5TTS] Synthesis error:', error);
      throw new Error(`F5-TTS synthesis failed: ${error.message}`);
    }
  }

  /**
   * Prepare inputs for F5-TTS preprocessing stage
   * @private
   */
  preparePreprocessInputs(text, voiceReference) {
    // TODO: Implement proper input preparation based on actual F5_Preprocess.ort requirements
    // Refer to: https://github.com/DakeQQ/F5-TTS-ONNX for input specification

    console.warn('[F5TTS] preparePreprocessInputs needs implementation for actual model input format');

    // Placeholder structure - needs adjustment based on actual model spec
    return {
      text: new ort.Tensor('int64', new BigInt64Array([]), [1, 0]),
      voice_ref: new ort.Tensor('float32', new Float32Array(voiceReference || []), [1, -1]),
    };
  }

  /**
   * Process voice reference audio
   * @param {Float32Array} audioData - Audio samples
   * @param {number} sampleRate - Sample rate of input audio
   * @returns {Promise<Float32Array>} Voice embedding
   */
  async extractVoiceEmbedding(audioData, sampleRate = 24000) {
    if (!this.isInitialized) {
      throw new Error('F5-TTS not initialized');
    }

    console.log(`[F5TTS] Extracting voice embedding from ${audioData.length} samples @ ${sampleRate}Hz`);

    // In production:
    // 1. Resample to 24kHz if needed
    // 2. Extract mel spectrogram
    // 3. Run speaker encoder to get embedding
    // 4. Return embedding vector

    // For now, return a dummy embedding
    const embeddingSize = 256;
    const embedding = new Float32Array(embeddingSize);
    for (let i = 0; i < embeddingSize; i++) {
      embedding[i] = Math.random();
    }

    return embedding;
  }

  /**
   * Check if language is supported
   * @param {string} language - ISO 639-1 language code
   * @returns {boolean}
   */
  isLanguageSupported(language) {
    // F5-TTS is multilingual and supports many languages
    // In production, this would check against actual supported languages
    const supportedLanguages = [
      'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl',
      'cs', 'ar', 'zh', 'ja', 'ko', 'hi', 'bn', 'ta', 'te', 'uk',
      'vi', 'th', 'id'
    ];
    return supportedLanguages.includes(language);
  }

  /**
   * Get supported languages
   * @returns {string[]} Array of ISO 639-1 language codes
   */
  getSupportedLanguages() {
    return [
      'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl',
      'cs', 'ar', 'zh', 'ja', 'ko', 'hi', 'bn', 'ta', 'te', 'uk',
      'vi', 'th', 'id'
    ];
  }

  /**
   * Get audio sample rate
   * @returns {number} Sample rate in Hz
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
    console.log('[F5TTS] Disposing F5-TTS models...');

    if (this.preprocess) {
      await this.preprocess.release();
      this.preprocess = null;
    }

    if (this.transformer) {
      await this.transformer.release();
      this.transformer = null;
    }

    if (this.decoder) {
      await this.decoder.release();
      this.decoder = null;
    }

    this.isInitialized = false;
    console.log('[F5TTS] All F5-TTS models disposed');
  }
}
