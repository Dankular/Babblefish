# TTS Core Module

This module provides Text-to-Speech functionality for Babblefish using Chatterbox Multilingual ONNX models.

## Architecture

```
TTSManager (Strategy Pattern)
    ↓
ChatterboxTTS (ONNX Engine)
    ↓
AudioPlayback (Web Audio API)
```

## Components

### ChatterboxTTS (`chatterbox.js`)
- ONNX Runtime Web inference
- Encoder model: text → mel spectrogram
- Vocoder model: mel spectrogram → audio
- 23 language support
- 24kHz audio output
- WebGPU/WASM execution

### TTSManager (`manager.js`)
- Engine selection strategy
- WebGPU detection
- Synthesis queue management
- Concurrent request handling
- Designed for multiple engines (Phase 3: F5-TTS)

### AudioPlayback (`playback.js`)
- Web Audio API wrapper
- Playback queue management
- Volume control
- Multi-speaker support
- Audio context lifecycle management

## Usage Examples

### Basic Usage (via Hook)
```javascript
import { useTTS } from '../../hooks/useTTS';

function MyComponent() {
  const tts = useTTS(true);

  useEffect(() => {
    tts.initialize();
  }, []);

  const handleSpeak = async () => {
    await tts.speak("Hello, world!", "en");
  };

  return (
    <div>
      <p>Status: {tts.status}</p>
      <button onClick={handleSpeak}>Speak</button>
    </div>
  );
}
```

### Advanced Usage (Direct API)
```javascript
import { TTSManager } from './manager';
import { AudioPlayback } from './playback';

// Initialize
const manager = new TTSManager((progress) => {
  console.log(`Loading: ${progress.message} (${progress.progress * 100}%)`);
});
await manager.initialize();

const playback = new AudioPlayback();
await playback.initialize();

// Synthesize
const audio = await manager.synthesize("Bonjour le monde", "fr");

// Play
await playback.enqueue(audio, manager.getSampleRate(), {
  speaker: "Marie",
  language: "fr"
});

// Cleanup
await manager.dispose();
await playback.dispose();
```

### Queue Multiple Synthesis
```javascript
const requests = [
  { text: "Hello", language: "en" },
  { text: "Hola", language: "es" },
  { text: "Bonjour", language: "fr" },
];

for (const req of requests) {
  manager.queueSynthesis(req).then(audio => {
    playback.enqueue(audio, manager.getSampleRate());
  });
}
```

## API Reference

### ChatterboxTTS

#### Constructor
```javascript
new ChatterboxTTS(onProgress?: (progress: {message: string, progress: number}) => void)
```

#### Methods
- `initialize(useWebGPU?: boolean): Promise<void>`
- `synthesize(text: string, language: string): Promise<Float32Array>`
- `isLanguageSupported(language: string): boolean`
- `getSupportedLanguages(): string[]`
- `getSampleRate(): number`
- `dispose(): Promise<void>`

### TTSManager

#### Constructor
```javascript
new TTSManager(onProgress?: (progress: {message: string, progress: number}) => void)
```

#### Methods
- `initialize(preferredEngine?: string): Promise<void>`
- `synthesize(text: string, language: string, options?: object): Promise<Float32Array>`
- `queueSynthesis(request: {text, language, options}): Promise<Float32Array>`
- `clearQueue(): void`
- `getQueueSize(): number`
- `getEngineType(): string`
- `getSampleRate(): number`
- `isLanguageSupported(language: string): boolean`
- `getSupportedLanguages(): string[]`
- `dispose(): Promise<void>`

### AudioPlayback

#### Constructor
```javascript
new AudioPlayback()
```

#### Methods
- `initialize(): Promise<void>`
- `enqueue(audioData: Float32Array, sampleRate: number, metadata?: object): Promise<void>`
- `stop(): void`
- `clearQueue(): void`
- `setVolume(volume: number): void` (0.0 - 1.0)
- `getVolume(): number`
- `getQueueSize(): number`
- `getIsPlaying(): boolean`
- `getState(): string`
- `dispose(): Promise<void>`

#### Callbacks
- `onPlaybackStart: (metadata: object, duration: number) => void`
- `onPlaybackEnd: (metadata: object) => void`
- `onQueueChange: (size: number) => void`

## Supported Languages

en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, ko, hi, bn, ta, te, uk, vi, th, id

## Performance Considerations

### Model Loading
- First load: ~500MB download
- Cached in IndexedDB
- Lazy loading recommended

### Synthesis
- WebGPU: ~100-200ms per sentence
- WASM: ~500-1000ms per sentence
- Queue prevents blocking

### Memory
- Models: ~500MB
- Audio buffer: ~2MB per minute
- Queue limit: 10 items (configurable)

## Error Handling

All methods that return Promises can throw errors. Always wrap in try-catch:

```javascript
try {
  await tts.initialize();
  await tts.speak("Hello", "en");
} catch (error) {
  console.error("TTS failed:", error);
  // Fallback to text-only mode
}
```

## Browser Compatibility

- Chrome/Edge: Full support (WebGPU + WASM)
- Firefox: WASM only (no WebGPU)
- Safari: WASM only (no WebGPU)
- Mobile: WASM support varies

## Debugging

Enable verbose logging:
```javascript
// All TTS modules log to console with [ComponentName] prefix
// Check browser console for:
// - [ChatterboxTTS] - Engine logs
// - [TTSManager] - Manager logs
// - [AudioPlayback] - Playback logs
```

## Future Extensions (Phase 3)

### F5-TTS Integration
```javascript
import { TTSManager, TTS_ENGINE } from './manager';

const manager = new TTSManager();
await manager.initialize(TTS_ENGINE.F5);

// Voice cloning with reference audio
await manager.synthesize(text, language, {
  referenceAudio: audioData,
  speakerId: "speaker123"
});
```

## Testing

Run unit tests (when available):
```bash
npm test -- tts
```

Manual testing:
```javascript
// Test in browser console
import { ChatterboxTTS } from './core/tts/chatterbox';

const tts = new ChatterboxTTS(console.log);
await tts.initialize();
const audio = await tts.synthesize("Test", "en");
console.log("Generated", audio.length, "samples");
```

## License

Part of Babblefish real-time translation application.
