// Audio utilities
export function calculateRMS(audioData) {
  const sum = audioData.reduce((acc, val) => acc + val * val, 0);
  return Math.sqrt(sum / audioData.length);
}

export function normalizeAudio(audioData) {
  const max = Math.max(...audioData.map(Math.abs));
  if (max === 0) return audioData;
  return audioData.map(val => val / max);
}

export function applyGain(audioData, gainDb) {
  const gain = Math.pow(10, gainDb / 20);
  return audioData.map(val => val * gain);
}

export function detectClipping(audioData, threshold = 0.99) {
  return audioData.some(val => Math.abs(val) > threshold);
}

export function convertToInt16(float32Array) {
  const int16Array = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return int16Array;
}

export function convertToFloat32(int16Array) {
  const float32Array = new Float32Array(int16Array.length);
  for (let i = 0; i < int16Array.length; i++) {
    float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7FFF);
  }
  return float32Array;
}

export function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function bytesToSize(bytes) {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}
