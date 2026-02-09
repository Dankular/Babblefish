// Status bar component
export default function StatusBar({ status, participants, roomId, language }) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'status-connected';
      case 'connecting':
      case 'reconnecting':
        return 'status-connecting';
      case 'disconnected':
        return 'status-disconnected';
      default:
        return 'status-unknown';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return 'Reconnecting...';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="status-bar">
      <div className="status-left">
        <div className={`status-indicator ${getStatusColor()}`}>
          <span className="status-dot"></span>
          <span className="status-text">{getStatusText()}</span>
        </div>

        {roomId && (
          <div className="status-room">
            Room: <span className="status-room-id">{roomId}</span>
          </div>
        )}

        {language && (
          <div className="status-language">
            Language: <span className="status-language-code">{language.toUpperCase()}</span>
          </div>
        )}
      </div>

      <div className="status-right">
        <div className="status-participants">
          <span className="status-participants-icon">👥</span>
          <span className="status-participants-count">{participants?.length || 0}</span>
        </div>
      </div>
    </div>
  );
}
