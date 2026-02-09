// Volume indicator component
import { useEffect, useState } from 'react';

export default function VolumeIndicator({ level, isSpeaking }) {
  const [displayLevel, setDisplayLevel] = useState(0);

  // Smooth level transitions
  useEffect(() => {
    const smoothingFactor = 0.3;
    setDisplayLevel(prev => prev * (1 - smoothingFactor) + level * smoothingFactor);
  }, [level]);

  // Convert to dB scale for better visualization
  const dbLevel = displayLevel > 0 ? 20 * Math.log10(displayLevel) : -100;
  const normalizedLevel = Math.max(0, Math.min(1, (dbLevel + 60) / 60));
  const barCount = 20;
  const activeBars = Math.round(normalizedLevel * barCount);

  const getBarColor = (index) => {
    const percentage = (index + 1) / barCount;
    if (percentage < 0.5) return 'bar-green';
    if (percentage < 0.8) return 'bar-yellow';
    return 'bar-red';
  };

  return (
    <div className={`volume-indicator ${isSpeaking ? 'speaking' : ''}`}>
      <div className="volume-label">
        {isSpeaking ? 'Speaking...' : 'Listening'}
      </div>

      <div className="volume-bars">
        {Array.from({ length: barCount }, (_, i) => (
          <div
            key={i}
            className={`volume-bar ${i < activeBars ? 'active' : ''} ${getBarColor(i)}`}
          />
        ))}
      </div>

      {displayLevel > 0 && (
        <div className="volume-level-text">
          {Math.round(normalizedLevel * 100)}%
        </div>
      )}
    </div>
  );
}
