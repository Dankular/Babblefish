// React hook for TTS functionality
import { useState, useEffect, useRef, useCallback } from 'react';
import { TTSManager } from '../core/tts/manager';
import { AudioPlayback } from '../core/tts/playback';

export function useTTS(enabled = true) {
  const [status, setStatus] = useState('uninitialized'); // uninitialized, loading, ready, error, synthesizing
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [error, setError] = useState(null);
  const [queueSize, setQueueSize] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [engineType, setEngineType] = useState(null);

  const ttsManager = useRef(null);
  const audioPlayback = useRef(null);
  const isInitializing = useRef(false);

  /**
   * Initialize TTS system
   */
  const initialize = useCallback(async () => {
    if (!enabled) {
      console.log('[useTTS] TTS disabled');
      return;
    }

    if (isInitializing.current) {
      console.log('[useTTS] Already initializing');
      return;
    }

    if (ttsManager.current && status === 'ready') {
      console.log('[useTTS] Already initialized');
      return;
    }

    isInitializing.current = true;
    setStatus('loading');
    setError(null);

    try {
      console.log('[useTTS] Initializing TTS system...');

      // Initialize TTS manager
      ttsManager.current = new TTSManager((progressInfo) => {
        setProgressMessage(progressInfo.message);
        setProgress(progressInfo.progress);
      });

      await ttsManager.current.initialize();

      // Initialize audio playback
      audioPlayback.current = new AudioPlayback();
      await audioPlayback.current.initialize();

      // Set up playback callbacks
      audioPlayback.current.onPlaybackStart = (metadata, duration) => {
        console.log(`[useTTS] Playback started: ${metadata.speaker || 'unknown'} (${duration.toFixed(2)}s)`);
        setIsPlaying(true);
      };

      audioPlayback.current.onPlaybackEnd = (metadata) => {
        console.log(`[useTTS] Playback ended: ${metadata.speaker || 'unknown'}`);
        setIsPlaying(false);
      };

      audioPlayback.current.onQueueChange = (size) => {
        setQueueSize(size);
      };

      setEngineType(ttsManager.current.getEngineType());
      setStatus('ready');
      setProgress(1.0);
      console.log('[useTTS] TTS system ready');
    } catch (err) {
      console.error('[useTTS] Initialization failed:', err);
      setError(err.message);
      setStatus('error');
    } finally {
      isInitializing.current = false;
    }
  }, [enabled, status]);

  /**
   * Synthesize and play text
   */
  const speak = useCallback(async (text, language = 'en', metadata = {}) => {
    if (!ttsManager.current || status !== 'ready') {
      console.warn('[useTTS] TTS not ready, cannot speak');
      return false;
    }

    if (!text || text.trim().length === 0) {
      console.warn('[useTTS] Empty text provided');
      return false;
    }

    try {
      setStatus('synthesizing');
      console.log(`[useTTS] Synthesizing: "${text.substring(0, 50)}..." (${language})`);

      // Synthesize audio
      const audioData = await ttsManager.current.queueSynthesis({
        text,
        language,
        options: metadata,
      });

      // Enqueue for playback
      const sampleRate = ttsManager.current.getSampleRate();
      await audioPlayback.current.enqueue(audioData, sampleRate, {
        ...metadata,
        text,
        language,
      });

      setStatus('ready');
      return true;
    } catch (err) {
      console.error('[useTTS] Synthesis failed:', err);
      setError(err.message);
      setStatus('ready'); // Return to ready state
      return false;
    }
  }, [status]);

  /**
   * Stop current playback
   */
  const stop = useCallback(() => {
    if (audioPlayback.current) {
      audioPlayback.current.stop();
      setIsPlaying(false);
    }
  }, []);

  /**
   * Clear playback queue
   */
  const clearQueue = useCallback(() => {
    if (audioPlayback.current) {
      audioPlayback.current.clearQueue();
      setQueueSize(0);
    }
  }, []);

  /**
   * Set volume (0.0 to 1.0)
   */
  const setVolume = useCallback((volume) => {
    if (audioPlayback.current) {
      audioPlayback.current.setVolume(volume);
    }
  }, []);

  /**
   * Get supported languages
   */
  const getSupportedLanguages = useCallback(() => {
    if (ttsManager.current) {
      return ttsManager.current.getSupportedLanguages();
    }
    return [];
  }, []);

  /**
   * Check if language is supported
   */
  const isLanguageSupported = useCallback((language) => {
    if (ttsManager.current) {
      return ttsManager.current.isLanguageSupported(language);
    }
    return false;
  }, []);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (ttsManager.current) {
        ttsManager.current.dispose();
        ttsManager.current = null;
      }
      if (audioPlayback.current) {
        audioPlayback.current.dispose();
        audioPlayback.current = null;
      }
    };
  }, []);

  return {
    // State
    status,
    progress,
    progressMessage,
    error,
    queueSize,
    isPlaying,
    engineType,

    // Methods
    initialize,
    speak,
    stop,
    clearQueue,
    setVolume,
    getSupportedLanguages,
    isLanguageSupported,
  };
}
