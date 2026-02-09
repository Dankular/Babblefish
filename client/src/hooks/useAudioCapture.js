// Audio capture hook with VAD
import { useState, useCallback, useRef, useEffect } from 'react';
import { AudioCapture } from '../core/audio/capture';
import { VADProcessor } from '../core/vad/processor';
import { OpusEncoder } from '../core/audio/opus';
import { calculateRMS } from '../core/audio/utils';
import { createAudioMessage, createUtteranceEndMessage } from '../network/protocol';

export function useAudioCapture(onAudio, enabled = true) {
  const [isCapturing, setIsCapturing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState(null);

  const captureRef = useRef(null);
  const vadRef = useRef(null);
  const encoderRef = useRef(null);

  const start = useCallback(async () => {
    if (isCapturing) {
      console.log('Audio capture already running');
      return;
    }

    try {
      setError(null);

      // Initialize encoder
      encoderRef.current = new OpusEncoder();

      // Initialize VAD processor
      vadRef.current = new VADProcessor(async (utterance) => {
        try {
          console.log('Encoding utterance...');
          const encoded = await encoderRef.current.encode(utterance);

          // Send audio data
          if (onAudio) {
            onAudio(createAudioMessage(encoded));
            // Signal utterance end
            onAudio(createUtteranceEndMessage());
          }

          setIsSpeaking(false);
        } catch (error) {
          console.error('Failed to encode utterance:', error);
          setError(error.message);
        }
      });

      // Load VAD model
      console.log('Loading VAD model...');
      await vadRef.current.vad.load();

      // Start audio capture
      captureRef.current = new AudioCapture((audioData) => {
        // Calculate audio level for UI
        const rms = calculateRMS(audioData);
        setAudioLevel(rms);

        // Process through VAD
        if (vadRef.current) {
          vadRef.current.processChunk(audioData);
          const vadState = vadRef.current.getState();
          setIsSpeaking(vadState.isSpeaking);
        }
      });

      await captureRef.current.start();
      setIsCapturing(true);
      console.log('Audio capture started successfully');
    } catch (error) {
      console.error('Failed to start audio capture:', error);
      setError(error.message);
      setIsCapturing(false);
    }
  }, [isCapturing, onAudio]);

  const stop = useCallback(() => {
    if (captureRef.current) {
      captureRef.current.stop();
      captureRef.current = null;
    }

    if (vadRef.current) {
      vadRef.current.reset();
      vadRef.current = null;
    }

    encoderRef.current = null;
    setIsCapturing(false);
    setAudioLevel(0);
    setIsSpeaking(false);
    console.log('Audio capture stopped');
  }, []);

  // Auto-start when enabled
  useEffect(() => {
    if (enabled && !isCapturing) {
      start();
    } else if (!enabled && isCapturing) {
      stop();
    }
  }, [enabled]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isCapturing) {
        stop();
      }
    };
  }, []);

  return {
    isCapturing,
    audioLevel,
    isSpeaking,
    error,
    start,
    stop
  };
}
