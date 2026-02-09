// React hook for voice registry operations
import { useState, useEffect, useCallback, useRef } from 'react';
import { getVoiceRegistry } from '../core/voice/registry';

/**
 * Hook for managing voice references
 *
 * Provides access to voice registry with automatic loading and WebSocket sync
 */
export function useVoiceRegistry(roomId = null, messages = []) {
  const [voiceReferences, setVoiceReferences] = useState(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const registryRef = useRef(null);
  const processedMessagesRef = useRef(new Set());

  /**
   * Initialize voice registry
   */
  useEffect(() => {
    const initRegistry = async () => {
      try {
        console.log('[useVoiceRegistry] Initializing...');
        const registry = await getVoiceRegistry();
        registryRef.current = registry;

        // Load existing voice references
        if (roomId) {
          const references = await registry.getVoiceReferencesForRoom(roomId);
          const refMap = new Map();
          references.forEach(ref => {
            refMap.set(ref.speaker_id, ref);
          });
          setVoiceReferences(refMap);
          console.log(`[useVoiceRegistry] Loaded ${references.length} voice references for room ${roomId}`);
        }

        setIsLoading(false);
      } catch (err) {
        console.error('[useVoiceRegistry] Initialization failed:', err);
        setError(err.message);
        setIsLoading(false);
      }
    };

    initRegistry();
  }, [roomId]);

  /**
   * Process incoming voice reference messages from WebSocket
   */
  useEffect(() => {
    if (!registryRef.current || !messages || messages.length === 0) {
      return;
    }

    const processMessages = async () => {
      for (const message of messages) {
        // Only process voice_reference_broadcast messages
        if (message.type !== 'voice_reference_broadcast') {
          continue;
        }

        // Check if already processed
        const messageId = `${message.speaker_id}_${message.timestamp}`;
        if (processedMessagesRef.current.has(messageId)) {
          continue;
        }

        try {
          console.log(`[useVoiceRegistry] Processing voice reference from ${message.speaker_name}`);

          // Decode base64 audio data
          const binaryString = atob(message.voice_data);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const audioData = bytes.buffer;

          // Store in registry
          await registryRef.current.storeVoiceReference(message.speaker_id, {
            audioData,
            sampleRate: message.sample_rate,
            duration: audioData.byteLength / (message.sample_rate * 4), // Assuming float32
            samples: audioData.byteLength / 4,
            roomId: roomId,
            speakerName: message.speaker_name,
          });

          // Update state
          setVoiceReferences(prev => {
            const newMap = new Map(prev);
            newMap.set(message.speaker_id, {
              speaker_id: message.speaker_id,
              voice_reference: audioData,
              sample_rate: message.sample_rate,
              speaker_name: message.speaker_name,
            });
            return newMap;
          });

          // Mark as processed
          processedMessagesRef.current.add(messageId);

          console.log(`[useVoiceRegistry] Stored voice reference for ${message.speaker_name}`);
        } catch (err) {
          console.error('[useVoiceRegistry] Failed to process voice reference:', err);
        }
      }
    };

    processMessages();
  }, [messages, roomId]);

  /**
   * Store voice reference for current user
   */
  const storeMyVoiceReference = useCallback(async (speakerId, voiceData) => {
    if (!registryRef.current) {
      throw new Error('Voice registry not initialized');
    }

    try {
      console.log('[useVoiceRegistry] Storing own voice reference...');

      await registryRef.current.storeVoiceReference(speakerId, {
        ...voiceData,
        roomId,
      });

      // Update state
      setVoiceReferences(prev => {
        const newMap = new Map(prev);
        newMap.set(speakerId, {
          speaker_id: speakerId,
          voice_reference: voiceData.audioData,
          sample_rate: voiceData.sampleRate,
        });
        return newMap;
      });

      console.log('[useVoiceRegistry] Own voice reference stored');
    } catch (err) {
      console.error('[useVoiceRegistry] Failed to store voice reference:', err);
      throw err;
    }
  }, [roomId]);

  /**
   * Get voice reference for a speaker
   */
  const getVoiceReference = useCallback((speakerId) => {
    return voiceReferences.get(speakerId) || null;
  }, [voiceReferences]);

  /**
   * Check if voice reference exists for a speaker
   */
  const hasVoiceReference = useCallback((speakerId) => {
    return voiceReferences.has(speakerId);
  }, [voiceReferences]);

  /**
   * Clear all voice references
   */
  const clearAll = useCallback(async () => {
    if (!registryRef.current) {
      return;
    }

    try {
      await registryRef.current.clearAll();
      setVoiceReferences(new Map());
      processedMessagesRef.current.clear();
      console.log('[useVoiceRegistry] All voice references cleared');
    } catch (err) {
      console.error('[useVoiceRegistry] Failed to clear voice references:', err);
      throw err;
    }
  }, []);

  /**
   * Get storage statistics
   */
  const getStats = useCallback(async () => {
    if (!registryRef.current) {
      return null;
    }

    try {
      return await registryRef.current.getStats();
    } catch (err) {
      console.error('[useVoiceRegistry] Failed to get stats:', err);
      return null;
    }
  }, []);

  return {
    voiceReferences,
    isLoading,
    error,
    storeMyVoiceReference,
    getVoiceReference,
    hasVoiceReference,
    clearAll,
    getStats,
  };
}
