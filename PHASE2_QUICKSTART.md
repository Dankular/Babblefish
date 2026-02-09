# Phase 2: Chatterbox TTS - Quick Start Guide

## Overview
Phase 2 adds Text-to-Speech (TTS) functionality to Babblefish using Chatterbox Multilingual ONNX models.

## Files Created

### Core TTS Engine (`client/src/core/tts/`)
```
tts/
├── chatterbox.js    - Chatterbox ONNX TTS engine (encoder + vocoder)
├── manager.js       - TTS strategy manager (supports multiple engines)
├── playback.js      - Audio playback queue manager
└── index.js         - Module exports
```

### React Integration
```
hooks/
└── useTTS.js        - React hook for TTS functionality

components/
└── TTSStatus.jsx    - TTS status display component
```

### Updated Files
- `client/src/pages/RoomPage.jsx` - Added TTS integration
- `client/src/styles/globals.css` - Added TTS status styles

## How It Works

### 1. User Flow
```
User joins room
  ↓
First translation received
  ↓
TTS auto-initializes (shows progress)
  ↓
Models downloaded from Hugging Face
  ↓
Models cached in browser
  ↓
Future translations auto-play
```

### 2. Technical Flow
```
Translation → TTS Manager → Chatterbox Engine → Audio Playback → Browser
                 ↓              ↓                     ↓
              Queue        WebGPU/WASM          Web Audio API
```

## Quick Test

### 1. Start the Application
```bash
cd client
npm install  # If not already done
npm run dev
```

### 2. Join a Room
- Open browser to `http://localhost:3000`
- Enter room ID, name, and select language
- Click "Join Room"

### 3. Test TTS
- Have another user join the same room (different browser/device)
- Have them speak in their language
- Your browser should:
  1. Show "Loading TTS models..." (first time only)
  2. Display progress bar
  3. Show "TTS ready" when complete
  4. Auto-play translated audio

### 4. Toggle TTS
- Click the "ON/OFF" button in the TTS Status panel
- When OFF: translations display as text only
- When ON: translations are synthesized and played

## API Reference

### useTTS Hook

```javascript
import { useTTS } from '../hooks/useTTS';

const {
  // State
  status,           // 'uninitialized' | 'loading' | 'ready' | 'synthesizing' | 'error'
  progress,         // 0.0 - 1.0 (model download progress)
  progressMessage,  // Loading message
  error,           // Error message if failed
  queueSize,       // Number of queued synthesis requests
  isPlaying,       // Currently playing audio
  engineType,      // 'chatterbox' | 'f5' (Phase 3)

  // Methods
  initialize,      // () => Promise<void> - Initialize TTS engine
  speak,          // (text, language, metadata) => Promise<boolean> - Synthesize & play
  stop,           // () => void - Stop current playback
  clearQueue,     // () => void - Clear synthesis queue
  setVolume,      // (volume: number) => void - Set volume (0.0-1.0)
  getSupportedLanguages,  // () => string[] - Get supported language codes
  isLanguageSupported,    // (language: string) => boolean - Check language support
} = useTTS(enabled);
```

### Direct TTS Usage (Advanced)

```javascript
import { TTSManager } from '../core/tts/manager';
import { AudioPlayback } from '../core/tts/playback';

// Initialize TTS Manager
const ttsManager = new TTSManager((progress) => {
  console.log(progress.message, progress.progress);
});
await ttsManager.initialize();

// Synthesize speech
const audioData = await ttsManager.synthesize(
  "Hello, world!",
  "en",
  { speaker: "John" }
);

// Play audio
const playback = new AudioPlayback();
await playback.initialize();
await playback.enqueue(audioData, 24000, { speaker: "John" });
```

## Supported Languages (23)

| Code | Language    | Code | Language   | Code | Language    |
|------|-------------|------|------------|------|-------------|
| en   | English     | es   | Spanish    | fr   | French      |
| de   | German      | it   | Italian    | pt   | Portuguese  |
| pl   | Polish      | tr   | Turkish    | ru   | Russian     |
| nl   | Dutch       | cs   | Czech      | ar   | Arabic      |
| zh   | Chinese     | ja   | Japanese   | ko   | Korean      |
| hi   | Hindi       | bn   | Bengali    | ta   | Tamil       |
| te   | Telugu      | uk   | Ukrainian  | vi   | Vietnamese  |
| th   | Thai        | id   | Indonesian |      |             |

## Configuration

### Model Source
Models are loaded from:
```
https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX
```

Files:
- `encoder_model.onnx` - Text to mel spectrogram (~250MB)
- `decoder_model.onnx` - Mel spectrogram to audio (~250MB)

### Browser Caching
Models are automatically cached in browser IndexedDB:
- First load: Downloads ~500MB
- Subsequent loads: Instant (cached)
- Cache persists across sessions

### WebGPU vs WASM
- Automatically detects WebGPU support
- Uses WebGPU if available (faster)
- Falls back to WASM if not
- No configuration needed

## Troubleshooting

### TTS Not Initializing
**Problem**: TTS status shows "uninitialized"
**Solution**:
- Ensure you've received at least one translation
- TTS lazy-loads on first translation to save bandwidth

### Models Not Loading
**Problem**: Loading stuck at 0%
**Solution**:
- Check browser console for errors
- Verify internet connection
- Check Hugging Face is accessible
- Clear browser cache and reload

### No Audio Playing
**Problem**: TTS shows "ready" but no sound
**Solution**:
- Check browser audio permissions
- Verify volume is not muted
- Click somewhere on page first (browser autoplay policy)
- Check browser console for audio context errors

### Wrong Language Audio
**Problem**: Audio in unexpected language
**Solution**:
- Verify language code is correct
- Check language is in supported list
- If unsupported, fallback is English

### Performance Issues
**Problem**: Slow synthesis or playback
**Solution**:
- Check WebGPU support (chrome://gpu)
- Close other browser tabs
- Reduce synthesis queue size
- Check CPU/memory usage

## Testing Checklist

- [ ] TTS initializes on first translation
- [ ] Progress bar displays during model download
- [ ] Models cache correctly (reload is instant)
- [ ] Audio plays after synthesis completes
- [ ] Multiple translations queue correctly
- [ ] Own messages are NOT synthesized
- [ ] Toggle button enables/disables TTS
- [ ] Volume control works
- [ ] Error messages display for failures
- [ ] WebGPU detection works
- [ ] WASM fallback works (disable WebGPU to test)

## Next Steps

### Phase 3: F5-TTS Voice Cloning
The architecture is ready for F5-TTS integration:
- TTSManager already supports multiple engines
- Add F5Engine class alongside ChatterboxTTS
- Implement voice cloning from reference audio
- Switch engines based on device capabilities

### Potential Enhancements
- [ ] Add proper Chatterbox tokenizer (SentencePiece)
- [ ] Implement text normalization
- [ ] Add voice selection/customization
- [ ] Support SSML for prosody control
- [ ] Implement speaker diarization → voice mapping
- [ ] Add speaking rate control
- [ ] Implement audio ducking for simultaneous speakers

## Resources

- **Implementation Docs**: `PHASE2_IMPLEMENTATION.md`
- **Chatterbox Model**: https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX
- **ONNX Runtime Web**: https://onnxruntime.ai/docs/tutorials/web/
- **Web Audio API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API

## Support

For issues or questions:
1. Check browser console for errors
2. Review `PHASE2_IMPLEMENTATION.md` for architecture details
3. Examine component source code comments
4. Test with minimal example before complex scenarios
