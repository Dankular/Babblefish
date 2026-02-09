// Main room page
import { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAudioCapture } from '../hooks/useAudioCapture';
import { useRoom } from '../hooks/useRoom';
import TranscriptView from '../components/TranscriptView';
import StatusBar from '../components/StatusBar';
import VolumeIndicator from '../components/VolumeIndicator';
import { createJoinMessage, createLeaveMessage, MessageType } from '../network/protocol';

const WS_URL = 'ws://localhost:8000/ws/client';

export default function RoomPage({ roomConfig, onLeave }) {
  const [translations, setTranslations] = useState([]);
  const [autoStarted, setAutoStarted] = useState(false);

  // WebSocket connection
  const { status, messages, send } = useWebSocket(WS_URL);

  // Room state management
  const room = useRoom(messages);

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

  // Handle translation messages
  useEffect(() => {
    const newTranslations = messages.filter(m => m.type === MessageType.TRANSLATION);
    if (newTranslations.length > 0) {
      setTranslations(prev => [...prev, ...newTranslations]);
    }
  }, [messages]);

  const handleLeave = () => {
    send(createLeaveMessage());
    if (onLeave) {
      onLeave();
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
