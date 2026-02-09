// Main room page
import { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAudioCapture } from '../hooks/useAudioCapture';
import { useRoom } from '../hooks/useRoom';
import { useTTS } from '../hooks/useTTS';
import TranscriptView from '../components/TranscriptView';
import StatusBar from '../components/StatusBar';
import VolumeIndicator from '../components/VolumeIndicator';
import TTSStatus from '../components/TTSStatus';
import { createJoinMessage, createLeaveMessage, MessageType } from '../network/protocol';

const WS_URL = 'wss://gel-supervision-desirable-cant.trycloudflare.com/ws/client';

export default function RoomPage({ roomConfig, onLeave }) {
  const [translations, setTranslations] = useState([]);
  const [autoStarted, setAutoStarted] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);

  // WebSocket connection
  const { status, messages, send } = useWebSocket(WS_URL);

  // Room state management
  const room = useRoom(messages);

  // TTS system
  const tts = useTTS(ttsEnabled);

  // Audio capture with VAD
  const { isCapturing, audioLevel, isSpeaking, error: audioError, start: startAudio } = useAudioCapture(
    (message) => {
      send(message);
    },
    false // Don't auto-start
  );

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

  // Auto-synthesize new translations
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
        const metadata = {
          speaker: latest.speaker_name,
          sourceLanguage: latest.source_lang,
          timestamp: latest.timestamp,
        };

        console.log(`[RoomPage] Auto-synthesizing translation from ${latest.speaker_name}`);
        tts.speak(text, language, metadata);
      }
    }
  }, [translations, ttsEnabled, tts, roomConfig.language, room.participantId]);

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
                </li>
              ))}
            </ul>
          </div>

          <button onClick={handleLeave} className="btn-leave">
            Leave Room
          </button>
        </div>
      </div>
    </div>
  );
}
