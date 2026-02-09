// Room join page
import { useState } from 'react';
import LanguageSelector from '../components/LanguageSelector';

export default function JoinPage({ onJoin }) {
  const [name, setName] = useState('');
  const [roomId, setRoomId] = useState('');
  const [language, setLanguage] = useState('en');
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState('');

  const generateRoomId = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let result = '';
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const handleJoin = async () => {
    setError('');

    if (!name.trim()) {
      setError('Please enter your name');
      return;
    }

    if (!roomId.trim()) {
      setError('Please enter a room ID');
      return;
    }

    if (!language) {
      setError('Please select a language');
      return;
    }

    setIsJoining(true);

    try {
      await onJoin({
        name: name.trim(),
        roomId: roomId.trim().toUpperCase(),
        language: language
      });
    } catch (err) {
      setError(err.message || 'Failed to join room');
      setIsJoining(false);
    }
  };

  const handleCreateRoom = () => {
    setRoomId(generateRoomId());
  };

  return (
    <div className="join-page">
      <div className="join-container">
        <div className="join-header">
          <h1 className="join-title">BabbleFish</h1>
          <p className="join-subtitle">Realtime Voice Translation</p>
        </div>

        <div className="join-form">
          <div className="form-group">
            <label htmlFor="name">Your Name</label>
            <input
              id="name"
              type="text"
              placeholder="Enter your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isJoining}
              className="form-input"
              maxLength={50}
            />
          </div>

          <div className="form-group">
            <label htmlFor="roomId">Room ID</label>
            <div className="room-input-group">
              <input
                id="roomId"
                type="text"
                placeholder="Enter room ID"
                value={roomId}
                onChange={(e) => setRoomId(e.target.value.toUpperCase())}
                disabled={isJoining}
                className="form-input"
                maxLength={20}
              />
              <button
                onClick={handleCreateRoom}
                disabled={isJoining}
                className="btn-create-room"
                type="button"
              >
                Create New
              </button>
            </div>
          </div>

          <div className="form-group">
            <label>Your Language</label>
            <LanguageSelector
              value={language}
              onChange={setLanguage}
              disabled={isJoining}
            />
          </div>

          {error && (
            <div className="form-error">
              {error}
            </div>
          )}

          <button
            onClick={handleJoin}
            disabled={isJoining}
            className="btn-join"
          >
            {isJoining ? 'Joining...' : 'Join Room'}
          </button>
        </div>

        <div className="join-footer">
          <p className="join-info">
            Phase 1: Text translations only. Voice cloning coming soon!
          </p>
        </div>
      </div>
    </div>
  );
}
