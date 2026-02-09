// TTS Status Component
// Displays TTS loading, synthesis, and playback status

export default function TTSStatus({
  status,
  progress,
  progressMessage,
  engineType,
  queueSize,
  isPlaying,
  error,
  onToggle,
  enabled
}) {
  const getStatusColor = () => {
    switch (status) {
      case 'ready': return 'text-green-600';
      case 'loading': return 'text-blue-600';
      case 'synthesizing': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'ready': return '✓';
      case 'loading': return '↻';
      case 'synthesizing': return '♪';
      case 'error': return '✗';
      default: return '○';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'uninitialized': return 'TTS not initialized';
      case 'loading': return progressMessage || 'Loading TTS models...';
      case 'ready': return isPlaying ? 'Playing audio' : 'TTS ready';
      case 'synthesizing': return 'Synthesizing speech...';
      case 'error': return 'TTS error';
      default: return 'Unknown status';
    }
  };

  const getEngineName = () => {
    switch (engineType) {
      case 'chatterbox': return 'Chatterbox Multilingual';
      case 'f5': return 'F5-TTS';
      default: return 'Unknown';
    }
  };

  return (
    <div className="tts-status">
      <div className="tts-status-header">
        <h4>Text-to-Speech</h4>
        {onToggle && (
          <button
            onClick={onToggle}
            className="tts-toggle"
            title={enabled ? 'Disable TTS' : 'Enable TTS'}
          >
            {enabled ? 'ON' : 'OFF'}
          </button>
        )}
      </div>

      {enabled && (
        <>
          <div className={`tts-status-info ${getStatusColor()}`}>
            <span className="tts-status-icon">{getStatusIcon()}</span>
            <span className="tts-status-text">{getStatusText()}</span>
          </div>

          {status === 'loading' && (
            <div className="tts-progress">
              <div
                className="tts-progress-bar"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
          )}

          {engineType && status === 'ready' && (
            <div className="tts-engine-info">
              <span className="tts-engine-label">Engine:</span>
              <span className="tts-engine-name">{getEngineName()}</span>
            </div>
          )}

          {queueSize > 0 && (
            <div className="tts-queue-info">
              <span className="tts-queue-label">Queue:</span>
              <span className="tts-queue-count">{queueSize}</span>
            </div>
          )}

          {isPlaying && (
            <div className="tts-playing-indicator">
              <span className="tts-playing-icon">♪</span>
              <span className="tts-playing-text">Playing...</span>
            </div>
          )}

          {error && (
            <div className="tts-error">
              <p className="tts-error-title">Error:</p>
              <p className="tts-error-message">{error}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
