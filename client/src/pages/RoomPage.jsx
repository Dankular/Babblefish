// Main room page
import { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAudioCapture } from '../hooks/useAudioCapture';
import { useRoom } from '../hooks/useRoom';
import { useTTS } from '../hooks/useTTS';
import { useVoiceRegistry } from '../hooks/useVoiceRegistry';
import TranscriptView from '../components/TranscriptView';
import StatusBar from '../components/StatusBar';
import VolumeIndicator from '../components/VolumeIndicator';
import TTSStatus from '../components/TTSStatus';
import VoiceEnrollmentModal from '../components/VoiceEnrollment';
import { createJoinMessage, createLeaveMessage, createVoiceReferenceMessage, MessageType } from '../network/protocol';

const WS_URL = 'wss://roland-dresses-cubic-earned.trycloudflare.com/ws/client';

export default function RoomPage({ roomConfig, onLeave }) {
  const [translations, setTranslations] = useState([]);
  const [autoStarted, setAutoStarted] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [showVoiceEnrollment, setShowVoiceEnrollment] = useState(false);
  const [voiceEnrolled, setVoiceEnrolled] = useState(false);

  // WebSocket connection
  const { status, messages, send } = useWebSocket(WS_URL);

  // Room state management
  const room = useRoom(messages);

  // Voice registry (Phase 3)
  const voiceRegistry = useVoiceRegistry(roomConfig.roomId, messages);

  // TTS system
  const tts = useTTS(ttsEnabled);

  // Audio capture with VAD
  const { isCapturing, audioLevel, isSpeaking, error: audioError, start: startAudio } = useAudioCapture(
    (message) => {
      send(message);
    },
    false // Don't auto-start
  );

  // Show voice enrollment modal when joined (Phase 3)
  useEffect(() => {
    if (room.isJoined && !voiceEnrolled && !voiceRegistry.isLoading) {
      // Check if user already has a voice reference
      const hasVoice = voiceRegistry.hasVoiceReference(room.participantId);
      if (!hasVoice) {
        console.log('[RoomPage] Showing voice enrollment modal');
        setShowVoiceEnrollment(true);
      } else {
        console.log('[RoomPage] Voice reference already exists');
        setVoiceEnrolled(true);
      }
    }
  }, [room.isJoined, room.participantId, voiceEnrolled, voiceRegistry]);

  // Join room when connected
  useEffect(() => {
    if (status === 'connected' && !autoStarted) {
      const joinMsg = createJoinMessage(
        roomConfig.roomId,
        roomConfig.language,
        roomConfig.name
      );
      send(joinMsg);
      setAutoStarted(true);
    }
  }, [status, autoStarted, roomConfig, send]);

  // Start audio capture when joined
  useEffect(() => {
    if (room.isJoined && !isCapturing && autoStarted) {
      startAudio();
    }
  }, [room.isJoined, isCapturing, autoStarted, startAudio]);

  // Initialize TTS on first translation
  useEffect(() => {
    if (ttsEnabled && tts.status === 'uninitialized' && translations.length > 0) {
      console.log('[RoomPage] Initializing TTS on first translation');
      tts.initialize();
    }
  }, [ttsEnabled, tts.status, translations.length, tts]);

  // Handle translation messages
  useEffect(() => {
    const newTranslations = messages.filter(m => m.type === MessageType.TRANSLATION);
    if (newTranslations.length > 0) {
      setTranslations(prev => [...prev, ...newTranslations]);
    }
  }, [messages]);

  // Auto-synthesize new translations (Phase 3: with voice cloning)
  useEffect(() => {
    if (!ttsEnabled || tts.status !== 'ready') {
      return;
    }

    // Process latest translation
    if (translations.length > 0) {
      const latest = translations[translations.length - 1];

      // Only synthesize if it's for our language and not from us
      if (latest.translations && latest.translations[roomConfig.language] && latest.speaker_id !== room.participantId) {
        const text = latest.translations[roomConfig.language];
        const language = roomConfig.language;

        // Get voice reference for speaker (Phase 3)
        const voiceRef = voiceRegistry.getVoiceReference(latest.speaker_id);

        const metadata = {
          speaker: latest.speaker_name,
          speakerId: latest.speaker_id,
          sourceLanguage: latest.source_lang,
          timestamp: latest.timestamp,
        };

        // Add voice reference if available
        if (voiceRef) {
          metadata.voiceReference = voiceRef.voice_reference;
          metadata.voiceReferenceRate = voiceRef.sample_rate;
          console.log(`[RoomPage] Auto-synthesizing translation from ${latest.speaker_name} with voice cloning`);
        } else {
          console.log(`[RoomPage] Auto-synthesizing translation from ${latest.speaker_name} (no voice reference)`);
        }

        tts.speak(text, language, metadata);
      }
    }
  }, [translations, ttsEnabled, tts, roomConfig.language, room.participantId, voiceRegistry]);

  const handleLeave = () => {
    send(createLeaveMessage());
    if (onLeave) {
      onLeave();
    }
  };

  const toggleTTS = () => {
    setTtsEnabled(prev => !prev);
    if (!ttsEnabled) {
      tts.clearQueue();
      tts.stop();
    }
  };

  // Handle voice enrollment completion (Phase 3)
  const handleVoiceEnrollmentComplete = async (processedAudio) => {
    try {
      console.log('[RoomPage] Voice enrollment completed');

      // Store in local registry
      await voiceRegistry.storeMyVoiceReference(room.participantId, {
        ...processedAudio,
        roomId: roomConfig.roomId,
        speakerName: roomConfig.name,
        language: roomConfig.language,
      });

      // Convert to base64 for WebSocket transmission
      const float32Array = new Float32Array(processedAudio.audioData);
      const uint8Array = new Uint8Array(float32Array.buffer);
      let binary = '';
      for (let i = 0; i < uint8Array.length; i++) {
        binary += String.fromCharCode(uint8Array[i]);
      }
      const base64Data = btoa(binary);

      // Broadcast to other participants
      const voiceMsg = createVoiceReferenceMessage(
        room.participantId,
        base64Data,
        processedAudio.sampleRate
      );
      send(voiceMsg);

      setVoiceEnrolled(true);
      setShowVoiceEnrollment(false);

      console.log('[RoomPage] Voice reference broadcast to room');
    } catch (err) {
      console.error('[RoomPage] Failed to complete voice enrollment:', err);
      alert('Failed to save voice reference. Please try again.');
    }
  };

  // Handle voice enrollment skip (Phase 3)
  const handleVoiceEnrollmentSkip = () => {
    console.log('[RoomPage] Voice enrollment skipped');
    setVoiceEnrolled(true); // Mark as enrolled to not show again
    setShowVoiceEnrollment(false);
  };

  return (
    <div className="room-page">
      <StatusBar
        status={status}
        participants={room.participants}
        roomId={roomConfig.roomId}
        language={roomConfig.language}
      />

      <div className="room-content">
        <div className="room-main">
          <TranscriptView
            translations={translations}
            language={roomConfig.language}
          />
        </div>

        <div className="room-sidebar">
          <div className="room-info">
            <h3>Room: {roomConfig.roomId}</h3>
            <p>Name: {roomConfig.name}</p>
            <p>Language: {roomConfig.language.toUpperCase()}</p>
          </div>

          <VolumeIndicator
            level={audioLevel}
            isSpeaking={isSpeaking}
          />

          <TTSStatus
            status={tts.status}
            progress={tts.progress}
            progressMessage={tts.progressMessage}
            engineType={tts.engineType}
            queueSize={tts.queueSize}
            isPlaying={tts.isPlaying}
            error={tts.error}
            onToggle={toggleTTS}
            enabled={ttsEnabled}
          />

          {audioError && (
            <div className="audio-error">
              <p>Audio Error:</p>
              <p>{audioError}</p>
            </div>
          )}

          <div className="room-participants">
            <h4>Participants ({room.participantCount})</h4>
            <ul>
              {room.participants.map(p => (
                <li key={p.id}>
                  <span className="participant-name">{p.name}</span>
                  <span className="participant-lang">{p.language}</span>
                  {voiceRegistry.hasVoiceReference(p.id) && (
                    <span className="voice-badge" title="Voice enrolled">🎤</span>
                  )}
                </li>
              ))}
            </ul>
          </div>

          <button onClick={handleLeave} className="btn-leave">
            Leave Room
          </button>
        </div>
      </div>

      {/* Voice Enrollment Modal (Phase 3) */}
      <VoiceEnrollmentModal
        isOpen={showVoiceEnrollment}
        onComplete={handleVoiceEnrollmentComplete}
        onSkip={handleVoiceEnrollmentSkip}
      />
    </div>
  );
}
