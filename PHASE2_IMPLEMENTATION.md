# Phase 2: Chatterbox Multilingual TTS - Implementation Complete

## Overview

This document describes the complete implementation of Phase 2: Chatterbox Multilingual TTS for the Babblefish real-time voice translation application.

## Architecture

### TTS Pipeline

```
Translation Received → TTS Manager → Chatterbox Engine → Audio Playback → Browser Audio
                           ↓
                    Synthesis Queue
                           ↓
                    WebGPU/WASM Inference
```

## Files Created

### Core TTS Components

#### 1. `client/src/core/tts/chatterbox.js`
- **Purpose**: Chatterbox Multilingual ONNX TTS engine
- **Key Features**:
  - Loads encoder and vocoder models from Hugging Face
  - Uses ONNX Runtime Web for inference
  - WebGPU execution provider with WASM fallback
  - Supports 23 languages
  - Generates 24kHz audio

**Supported Languages**:
- English (en), Spanish (es), French (fr), German (de), Italian (it)
- Portuguese (pt), Polish (pl), Turkish (tr), Russian (ru), Dutch (nl)
- Czech (cs), Arabic (ar), Chinese (zh), Japanese (ja), Korean (ko)
- Hindi (hi), Bengali (bn), Tamil (ta), Telugu (te), Ukrainian (uk)
- Vietnamese (vi), Thai (th), Indonesian (id)

**Key Methods**:
- `initialize(useWebGPU)` - Load models from Hugging Face
- `synthesize(text, language)` - Generate speech audio
- `isLanguageSupported(language)` - Check language support
- `dispose()` - Cleanup resources

#### 2. `client/src/core/tts/manager.js`
- **Purpose**: TTS strategy manager (supports multiple engines)
- **Key Features**:
  - Detects WebGPU support
  - Manages synthesis queue
  - Handles concurrent synthesis requests
  - Designed for Phase 3 (F5-TTS) integration

**Key Methods**:
- `initialize(preferredEngine)` - Initialize TTS engine
- `synthesize(text, language, options)` - Direct synthesis
- `queueSynthesis(request)` - Queued synthesis
- `clearQueue()` - Clear pending requests
- `dispose()` - Cleanup resources

#### 3. `client/src/core/tts/playback.js`
- **Purpose**: Audio playback manager
- **Key Features**:
  - Web Audio API integration
  - Playback queue management
  - Volume control
  - Handles multiple concurrent speakers
  - Automatic audio context management

**Key Methods**:
- `initialize()` - Create audio context
- `enqueue(audioData, sampleRate, metadata)` - Add to playback queue
- `stop()` - Stop current playback
- `clearQueue()` - Clear playback queue
- `setVolume(volume)` - Set volume (0.0-1.0)
- `dispose()` - Cleanup resources

### React Integration

#### 4. `client/src/hooks/useTTS.js`
- **Purpose**: React hook for TTS functionality
- **Key Features**:
  - Manages TTS lifecycle
  - Progress tracking for model download
  - Auto-initialization on first translation
  - Error handling and recovery

**Hook API**:
```javascript
const {
  status,           // 'uninitialized' | 'loading' | 'ready' | 'synthesizing' | 'error'
  progress,         // 0.0 - 1.0
  progressMessage,  // Loading message
  error,           // Error message
  queueSize,       // Number of queued items
  isPlaying,       // Currently playing audio
  engineType,      // 'chatterbox' | 'f5'

  initialize,      // () => Promise<void>
  speak,          // (text, language, metadata) => Promise<boolean>
  stop,           // () => void
  clearQueue,     // () => void
  setVolume,      // (volume: number) => void
} = useTTS(enabled);
```

### UI Components

#### 5. `client/src/components/TTSStatus.jsx`
- **Purpose**: Display TTS status and controls
- **Features**:
  - Loading progress bar
  - Engine type indicator
  - Queue size display
  - Playing indicator
  - Error messages
  - Toggle TTS on/off

**Visual States**:
- Uninitialized: Gray circle
- Loading: Blue rotating icon + progress bar
- Ready: Green checkmark
- Synthesizing: Yellow music note
- Playing: Green animated music note
- Error: Red X

### Page Updates

#### 6. `client/src/pages/RoomPage.jsx` (Updated)
- **Changes**:
  - Added `useTTS` hook integration
  - Auto-initialize TTS on first translation
  - Auto-synthesize incoming translations
  - Skip synthesis for own messages
  - Added TTS toggle button
  - Added TTSStatus component to sidebar

**Auto-Synthesis Logic**:
```javascript
// Only synthesize if:
1. TTS is enabled
2. TTS is ready
3. Translation is for user's language
4. Translation is NOT from the user (speaker_id !== participantId)
```

### Styling

#### 7. `client/src/styles/globals.css` (Updated)
- Added comprehensive TTS status component styles
- Color-coded status indicators
- Smooth animations for loading and playing states
- Responsive design

## Configuration

### Vite Configuration
Already configured in `client/vite.config.js`:
- ONNX Runtime Web excluded from optimizeDeps
- Separate chunk for ONNX vendor bundle

### Dependencies
Already installed in `client/package.json`:
- `onnxruntime-web`: ^1.24.1

## Usage Flow

### First-Time User Experience

1. User joins room
2. User receives first translation
3. TTS automatically initializes (lazy loading)
4. Progress bar shows model download (encoder + vocoder)
5. Models cached in browser (IndexedDB)
6. TTS ready - future translations auto-play

### Ongoing Usage

1. Translation received from another participant
2. Translation text extracted for user's language
3. Text queued for synthesis
4. Audio synthesized using Chatterbox
5. Audio queued for playback
6. Audio plays through browser speakers
7. Next translation in queue begins

## Error Handling

### Graceful Degradation
- If TTS initialization fails → Continue with text-only mode
- If synthesis fails → Log error, continue with next translation
- If playback fails → Log error, continue operation

### User Feedback
- Progress indicator during model download
- Status indicator shows current state
- Error messages displayed in TTS status panel
- Console logging for debugging

## Performance Optimizations

### Lazy Loading
- Models not downloaded until first translation received
- Reduces initial page load time
- User may browse/join without downloading TTS

### Caching
- Models cached in browser IndexedDB
- Subsequent page loads use cached models
- No re-download after first use

### Queue Management
- Maximum 10 items in synthesis queue
- Drops oldest if queue full
- Prevents memory issues with rapid translations

### Audio Context
- Resumes suspended audio context (browser autoplay policy)
- Automatically manages context lifecycle

## Testing Checklist

- [ ] TTS loads successfully on first translation
- [ ] Progress bar shows during model download
- [ ] Audio plays after synthesis
- [ ] Multiple translations queue correctly
- [ ] Volume control works
- [ ] TTS toggle enables/disables functionality
- [ ] Error states display correctly
- [ ] Own messages are not synthesized
- [ ] WebGPU detection works
- [ ] WASM fallback works on non-WebGPU devices

## Future Enhancements (Phase 3)

The architecture is designed to support F5-TTS:
- TTSManager already has engine selection strategy
- AudioPlayback supports any sample rate
- useTTS hook engine-agnostic
- Add F5Engine class alongside ChatterboxTTS
- Switch engines based on device capabilities

## Known Limitations

### Tokenization
Current implementation uses simplified tokenization. Production should use:
- Actual Chatterbox SentencePiece tokenizer
- Proper text normalization
- Language-specific preprocessing

### Model Loading
Current implementation loads full models. Consider:
- Streaming model loading for large files
- Partial model loading if supported
- Compression techniques

### Language Detection
Currently uses user's selected language. Could enhance with:
- Auto-detect source language
- Synthesize in source language for comprehension check

## Resources

- **Chatterbox ONNX Model**: https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX
- **ONNX Runtime Web**: https://onnxruntime.ai/docs/tutorials/web/
- **Web Audio API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API

## Summary

Phase 2 implementation is complete with:
- ✅ Chatterbox Multilingual TTS integration
- ✅ WebGPU/WASM execution
- ✅ 23 language support
- ✅ Automatic synthesis on translation
- ✅ Queue management
- ✅ Audio playback
- ✅ React integration
- ✅ UI status indicators
- ✅ Error handling
- ✅ Performance optimizations

The system is ready for testing and Phase 3 (F5-TTS) integration.
