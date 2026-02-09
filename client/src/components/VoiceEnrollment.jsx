// Voice Enrollment UI Component
import { useState, useEffect, useRef } from 'react';
import { VoiceEnrollment } from '../core/voice/enrollment';

export default function VoiceEnrollmentModal({ isOpen, onComplete, onSkip }) {
  const [recordingState, setRecordingState] = useState('idle'); // idle, recording, processing, preview
  const [duration, setDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [error, setError] = useState(null);
  const [validationMessage, setValidationMessage] = useState('');

  const enrollmentRef = useRef(null);
  const animationFrameRef = useRef(null);
  const durationIntervalRef = useRef(null);
  const audioUrlRef = useRef(null);

  // Initialize enrollment manager
  useEffect(() => {
    if (!enrollmentRef.current) {
      enrollmentRef.current = new VoiceEnrollment();
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
      if (enrollmentRef.current) {
        enrollmentRef.current.cancelRecording();
      }
    };
  }, []);

  // Update audio level during recording
  useEffect(() => {
    if (recordingState === 'recording') {
      const updateLevel = () => {
        if (enrollmentRef.current && enrollmentRef.current.recording) {
          const level = enrollmentRef.current.getAudioLevel();
          setAudioLevel(level);
          animationFrameRef.current = requestAnimationFrame(updateLevel);
        }
      };
      updateLevel();
    } else {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      setAudioLevel(0);
    }
  }, [recordingState]);

  // Update duration during recording
  useEffect(() => {
    if (recordingState === 'recording') {
      durationIntervalRef.current = setInterval(() => {
        if (enrollmentRef.current) {
          const dur = enrollmentRef.current.getRecordingDuration();
          setDuration(dur);

          // Auto-stop at max duration
          if (dur >= 15000) {
            handleStopRecording();
          }
        }
      }, 100);
    } else {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
    }

    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [recordingState]);

  const handleStartRecording = async () => {
    try {
      setError(null);
      setValidationMessage('');
      setDuration(0);
      await enrollmentRef.current.startRecording();
      setRecordingState('recording');
    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Failed to access microphone. Please grant permission and try again.');
    }
  };

  const handleStopRecording = async () => {
    try {
      setRecordingState('processing');
      const blob = await enrollmentRef.current.stopRecording();

      if (!blob) {
        setError('Failed to capture audio');
        setRecordingState('idle');
        return;
      }

      // Validate audio
      const validation = await enrollmentRef.current.validateAudio(blob);

      if (!validation.valid) {
        setError(validation.issues.join('. '));
        setValidationMessage('Please try again');
        setRecordingState('idle');
        setDuration(0);
        return;
      }

      // Create audio URL for preview
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
      audioUrlRef.current = URL.createObjectURL(blob);

      setRecordedBlob(blob);
      setDuration(validation.duration);
      setRecordingState('preview');
    } catch (err) {
      console.error('Failed to stop recording:', err);
      setError('Failed to process recording');
      setRecordingState('idle');
    }
  };

  const handleReRecord = () => {
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
    setRecordedBlob(null);
    setDuration(0);
    setError(null);
    setValidationMessage('');
    setRecordingState('idle');
  };

  const handleConfirm = async () => {
    if (!recordedBlob) {
      return;
    }

    try {
      setRecordingState('processing');
      setValidationMessage('Processing audio...');

      // Process audio for F5-TTS
      const processedAudio = await enrollmentRef.current.processAudio(recordedBlob);

      // Complete enrollment
      if (onComplete) {
        await onComplete(processedAudio);
      }
    } catch (err) {
      console.error('Failed to process audio:', err);
      const errorMsg = err.message || err.toString();
      setError(`Failed to process audio: ${errorMsg}`);
      setRecordingState('preview');

      // Report error to server for logging
      if (window.ws && window.ws.readyState === WebSocket.OPEN) {
        try {
          window.ws.send(JSON.stringify({
            type: 'client_error',
            error_type: 'voice_enrollment_failed',
            error_message: errorMsg,
            context: {
              stage: 'processing',
              stack: err.stack ? err.stack.substring(0, 500) : 'no stack'
            }
          }));
        } catch (sendErr) {
          console.error('Failed to send error to server:', sendErr);
        }
      }
    }
  };

  const handleSkip = () => {
    if (onSkip) {
      onSkip();
    }
  };

  if (!isOpen) {
    return null;
  }

  const durationSeconds = (duration / 1000).toFixed(1);
  const isRecordingComplete = recordingState === 'recording' && duration >= 5000;

  return (
    <div className="modal-overlay">
      <div className="modal-content voice-enrollment-modal">
        <h2>Voice Enrollment</h2>

        <div className="enrollment-instructions">
          <p>
            To enable voice cloning, record a 5-10 second voice sample.
            Speak naturally and clearly in a quiet environment.
          </p>
          <p className="instruction-examples">
            <strong>Example phrases:</strong><br />
            "Hello, this is my voice sample for Babblefish."<br />
            "I'm recording this so others can hear translations in my voice."
          </p>
        </div>

        {/* Recording Visualizer */}
        {recordingState === 'recording' && (
          <div className="recording-visualizer">
            <div className="waveform-container">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className="waveform-bar"
                  style={{
                    height: `${Math.max(10, audioLevel * 100 * (0.5 + Math.random() * 0.5))}%`,
                    animationDelay: `${i * 0.05}s`,
                  }}
                />
              ))}
            </div>
            <div className="recording-timer">
              {durationSeconds}s / 15.0s
            </div>
            {duration < 5000 && (
              <div className="recording-hint">Keep speaking... (minimum 5s)</div>
            )}
            {isRecordingComplete && (
              <div className="recording-hint ready">Ready to stop!</div>
            )}
          </div>
        )}

        {/* Preview Player */}
        {recordingState === 'preview' && audioUrlRef.current && (
          <div className="preview-container">
            <audio
              controls
              src={audioUrlRef.current}
              className="preview-audio"
            />
            <div className="preview-info">
              Duration: {durationSeconds}s
            </div>
          </div>
        )}

        {/* Processing State */}
        {recordingState === 'processing' && (
          <div className="processing-container">
            <div className="spinner" />
            <p>Processing audio...</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-message">
            {error}
            {validationMessage && <div className="validation-hint">{validationMessage}</div>}
          </div>
        )}

        {/* Action Buttons */}
        <div className="enrollment-actions">
          {recordingState === 'idle' && (
            <>
              <button
                className="btn btn-primary btn-large"
                onClick={handleStartRecording}
              >
                Start Recording
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleSkip}
              >
                Skip for Now
              </button>
            </>
          )}

          {recordingState === 'recording' && (
            <button
              className={`btn btn-danger btn-large ${isRecordingComplete ? 'btn-pulse' : ''}`}
              onClick={handleStopRecording}
              disabled={duration < 5000}
            >
              {duration < 5000 ? `Keep Speaking (${(5 - duration / 1000).toFixed(1)}s)` : 'Stop Recording'}
            </button>
          )}

          {recordingState === 'preview' && (
            <>
              <button
                className="btn btn-primary"
                onClick={handleConfirm}
              >
                Confirm and Use This Recording
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleReRecord}
              >
                Re-record
              </button>
            </>
          )}
        </div>

        <div className="enrollment-footer">
          <small>
            Your voice sample is stored locally and shared only with participants in your room.
          </small>
        </div>
      </div>
    </div>
  );
}
