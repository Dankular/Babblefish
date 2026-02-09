// Transcript view component
import { useEffect, useRef } from 'react';

export default function TranscriptView({ translations, language }) {
  const containerRef = useRef(null);

  // Auto-scroll to bottom on new translations
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [translations]);

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div ref={containerRef} className="transcript-view">
      {translations.length === 0 && (
        <div className="transcript-empty">
          <p>Waiting for translations...</p>
          <p className="transcript-hint">Start speaking to see translations appear here</p>
        </div>
      )}

      {translations.map((translation, index) => {
        const translatedText = translation.translations?.[language];
        const sourceText = translation.source_text;
        const sourceLang = translation.source_lang;
        const speakerName = translation.speaker_name;
        const timestamp = translation.timestamp;

        return (
          <div key={index} className="transcript-item">
            <div className="transcript-header">
              <span className="transcript-speaker">{speakerName}</span>
              <span className="transcript-lang">{sourceLang}</span>
              <span className="transcript-time">{formatTime(timestamp)}</span>
            </div>

            {translatedText && (
              <div className="transcript-translation">
                {translatedText}
              </div>
            )}

            <div className="transcript-source">
              {sourceText}
            </div>
          </div>
        );
      })}
    </div>
  );
}
