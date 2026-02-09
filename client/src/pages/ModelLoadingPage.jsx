// Model Loading Page - Preload TTS models before joining rooms
import { useState, useEffect } from 'react';
import { TTSManager } from '../core/tts/manager';

export default function ModelLoadingPage({ onComplete }) {
  const [status, setStatus] = useState('initializing');
  const [progress, setProgress] = useState({
    chatterbox: { loaded: false, progress: 0, message: 'Waiting...' },
    f5tts: { loaded: false, progress: 0, message: 'Waiting...' },
  });
  const [error, setError] = useState(null);
  const [useF5, setUseF5] = useState(true);

  useEffect(() => {
    loadModels();
  }, [useF5]);

  const loadModels = async () => {
    setStatus('loading');
    setError(null);

    try {
      const ttsManager = new TTSManager((progressUpdate) => {
        // Progress callback from TTS engines
        // progressUpdate format: { message: string, progress: number }
        const engineName = progressUpdate.message?.toLowerCase().includes('f5') ? 'f5tts' : 'chatterbox';

        setProgress(prev => ({
          ...prev,
          [engineName]: {
            loaded: progressUpdate.progress >= 1.0,
            progress: progressUpdate.progress || 0,
            message: progressUpdate.message || 'Loading...',
          }
        }));
      });

      // Initialize with Chatterbox (always) and F5-TTS (if selected)
      const engineType = useF5 ? 'f5' : 'chatterbox';

      console.log(`[ModelLoadingPage] Loading ${engineType} engine...`);

      await ttsManager.initialize(engineType, true); // fallback enabled

      setStatus('complete');

      // Store TTS manager globally for app to use
      window.ttsManager = ttsManager;

      // Notify parent that models are ready
      if (onComplete) {
        setTimeout(() => onComplete({ engine: ttsManager.engineType }), 500);
      }

    } catch (err) {
      console.error('[ModelLoadingPage] Model loading failed:', err);
      setError(err.message || 'Failed to load models');
      setStatus('error');
    }
  };

  const handleRetry = () => {
    loadModels();
  };

  const handleSkip = () => {
    // Skip model loading, use text-only mode
    if (onComplete) {
      onComplete({ engine: 'text-only' });
    }
  };

  const totalProgress = useF5
    ? (progress.chatterbox.progress + progress.f5tts.progress) / 2
    : progress.chatterbox.progress;

  return (
    <div className="loading-page">
      <div className="loading-container">
        <h1>🐟 Babblefish</h1>
        <p className="subtitle">Preparing voice translation models...</p>

        {status === 'loading' && (
          <div className="loading-content">
            {/* Chatterbox Progress */}
            <div className="model-progress">
              <div className="model-header">
                <span className="model-name">
                  {progress.chatterbox.loaded ? '✓' : '⏳'} Chatterbox TTS
                </span>
                <span className="model-size">~500MB</span>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress.chatterbox.progress * 100}%` }}
                />
              </div>
              <div className="progress-message">{progress.chatterbox.message}</div>
            </div>

            {/* F5-TTS Progress (if enabled) */}
            {useF5 && (
              <div className="model-progress">
                <div className="model-header">
                  <span className="model-name">
                    {progress.f5tts.loaded ? '✓' : '⏳'} F5-TTS (Voice Cloning)
                  </span>
                  <span className="model-size">~200MB</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${progress.f5tts.progress * 100}%` }}
                  />
                </div>
                <div className="progress-message">{progress.f5tts.message}</div>
              </div>
            )}

            {/* Overall Progress */}
            <div className="overall-progress">
              <div className="progress-text">
                Overall: {Math.round(totalProgress * 100)}%
              </div>
              <div className="progress-bar progress-bar-large">
                <div
                  className="progress-fill"
                  style={{ width: `${totalProgress * 100}%` }}
                />
              </div>
            </div>

            <div className="loading-info">
              <p>
                <strong>First-time setup:</strong> Downloading voice models to your device.
                This only happens once - models are cached in your browser.
              </p>
              <p className="info-secondary">
                Using WebGPU for hardware acceleration (if available).
              </p>
            </div>

            {/* Option to disable F5-TTS if taking too long */}
            {useF5 && totalProgress < 0.5 && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setUseF5(false)}
              >
                Skip Voice Cloning (Faster)
              </button>
            )}
          </div>
        )}

        {status === 'complete' && (
          <div className="loading-complete">
            <div className="success-icon">✓</div>
            <h2>Models Ready!</h2>
            <p>Voice translation is ready to use</p>
          </div>
        )}

        {status === 'error' && (
          <div className="loading-error">
            <div className="error-icon">✗</div>
            <h2>Loading Failed</h2>
            <p className="error-message">{error}</p>
            <div className="error-actions">
              <button className="btn btn-primary" onClick={handleRetry}>
                Retry
              </button>
              <button className="btn btn-secondary" onClick={handleSkip}>
                Continue Without Voice (Text Only)
              </button>
            </div>
          </div>
        )}

        {status === 'initializing' && (
          <div className="loading-spinner">
            <div className="spinner" />
            <p>Initializing...</p>
          </div>
        )}
      </div>

      <style jsx>{`
        .loading-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 20px;
        }

        .loading-container {
          max-width: 600px;
          width: 100%;
          background: white;
          border-radius: 16px;
          padding: 40px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        h1 {
          font-size: 2.5rem;
          margin: 0 0 10px 0;
          text-align: center;
          color: #667eea;
        }

        .subtitle {
          text-align: center;
          color: #666;
          margin: 0 0 30px 0;
        }

        .model-progress {
          margin-bottom: 25px;
        }

        .model-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 14px;
        }

        .model-name {
          font-weight: 600;
          color: #333;
        }

        .model-size {
          color: #999;
        }

        .progress-bar {
          height: 8px;
          background: #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-bar-large {
          height: 12px;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
          transition: width 0.3s ease;
        }

        .progress-message {
          margin-top: 5px;
          font-size: 12px;
          color: #666;
        }

        .overall-progress {
          margin-top: 30px;
          padding-top: 20px;
          border-top: 2px solid #e0e0e0;
        }

        .progress-text {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 10px;
          color: #333;
        }

        .loading-info {
          margin-top: 25px;
          padding: 15px;
          background: #f5f5f5;
          border-radius: 8px;
          font-size: 14px;
        }

        .loading-info p {
          margin: 0 0 10px 0;
        }

        .loading-info p:last-child {
          margin: 0;
        }

        .info-secondary {
          color: #666;
          font-size: 13px;
        }

        .loading-complete, .loading-error {
          text-align: center;
          padding: 30px 0;
        }

        .success-icon {
          font-size: 64px;
          color: #4caf50;
          margin-bottom: 20px;
        }

        .error-icon {
          font-size: 64px;
          color: #f44336;
          margin-bottom: 20px;
        }

        .error-message {
          color: #d32f2f;
          margin: 10px 0 20px 0;
        }

        .error-actions {
          display: flex;
          gap: 10px;
          justify-content: center;
        }

        .loading-spinner {
          text-align: center;
          padding: 40px 0;
        }

        .spinner {
          width: 50px;
          height: 50px;
          border: 4px solid #e0e0e0;
          border-top-color: #667eea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px auto;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .btn {
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary {
          background: #667eea;
          color: white;
        }

        .btn-primary:hover {
          background: #5568d3;
        }

        .btn-secondary {
          background: #e0e0e0;
          color: #333;
        }

        .btn-secondary:hover {
          background: #d0d0d0;
        }

        .btn-sm {
          padding: 8px 16px;
          font-size: 13px;
          margin-top: 15px;
        }
      `}</style>
    </div>
  );
}
