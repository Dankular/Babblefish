# BabbleFish Real-time Translation Guide

Complete guide for the real-time speech translation system with VAD and WebSocket streaming.

## 🎯 Features

- **Real-time speech-to-speech translation**
- **Voice Activity Detection (VAD)** using Silero VAD
- **WebSocket streaming** for low latency
- **Automatic speech segmentation** based on pauses
- **10 target languages** supported
- **Browser-based client** - no app installation needed!

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_realtime.txt
```

### 2. Start the Server

**Windows:**
```bash
start_realtime.bat
```

**Linux/Mac:**
```bash
python realtime_server.py
```

### 3. Open the Client

Navigate to: **http://localhost:8001**

### 4. Start Translating!

1. Select target language
2. Click "Start"
3. Allow microphone access
4. **Speak naturally** - the system will detect when you pause
5. See transcription and translation in real-time!

---

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │
│  (Client)   │
└──────┬──────┘
       │ WebSocket
       │ (Audio Chunks: 100-300ms)
       │
┌──────▼──────────────────┐
│   FastAPI Server        │
│                         │
│  ┌──────────────────┐  │
│  │  Silero VAD      │  │
│  │ (Speech Detection)  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │  Audio Buffer    │  │
│  │  - Rolling buffer│  │
│  │  - 500ms silence │  │
│  │  - 5s force flush│  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │  Whisper (CT2)   │  │
│  │  Transcription   │  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │   NLLB (CT2)     │  │
│  │   Translation    │  │
│  └────────┬─────────┘  │
│           │             │
└───────────┼─────────────┘
            │
       Result (JSON)
            │
       ┌────▼────┐
       │ Browser │
       └─────────┘
```

---

## ⚙️ How It Works

### 1. Audio Capture (Client Side)

```javascript
// Capture microphone at 16kHz, mono
const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true
    }
});
```

### 2. WebSocket Streaming

- Client sends **100-300ms audio chunks** continuously
- Server receives and buffers audio
- Minimal latency (~50-100ms transport)

### 3. Voice Activity Detection

**Silero VAD** analyzes each chunk:
- Speech probability: 0-1
- Threshold: 0.5 (configurable)
- Detects speech start/end

### 4. Smart Segmentation

```python
if silence_duration >= 500ms:
    # End of utterance - send to Whisper
    process_segment()
elif segment_duration >= 5s:
    # Force flush to prevent lag
    process_segment()
```

### 5. Transcription

- **Whisper Medium** (CTranslate2 optimized)
- Automatic language detection
- ~1 second per segment

### 6. Translation

- **NLLB-200** (CTranslate2 optimized)
- 200+ language pairs
- ~1 second per segment

### 7. Results Streaming

```json
{
    "type": "result",
    "segment": 3,
    "transcription": "Hello, how are you?",
    "language": "en",
    "translation": "Hola, ¿cómo estás?",
    "timestamp": 1234567890.123
}
```

---

## 🎛️ Configuration

### VAD Settings

```python
SileroVAD(
    threshold=0.5  # 0-1, higher = stricter speech detection
)
```

### Buffer Settings

```python
AudioBuffer(
    chunk_duration_ms=300,      # Audio chunk size
    silence_threshold_ms=500,   # Pause to end segment
    max_segment_duration_s=5    # Force flush interval
)
```

### Latency Tuning

| Setting | Value | Effect |
|---------|-------|--------|
| **chunk_duration_ms** | 100 | Lower latency, more overhead |
| | 300 | **Balanced** (recommended) |
| | 500 | Higher latency, less overhead |
| **silence_threshold_ms** | 300 | Fast response, may cut off |
| | 500 | **Balanced** (recommended) |
| | 1000 | Patient, may feel slow |
| **max_segment_duration_s** | 3 | Frequent updates |
| | 5 | **Balanced** (recommended) |
| | 10 | Better for long monologues |

---

## 📊 Performance

### Latency Breakdown

| Component | Time | Notes |
|-----------|------|-------|
| **Audio Capture** | 100-300ms | Chunk duration |
| **VAD Processing** | <10ms | Very fast |
| **Network (WebSocket)** | 10-50ms | Local network |
| **Whisper Transcription** | 500-1500ms | Main bottleneck |
| **NLLB Translation** | 500-1000ms | Second bottleneck |
| **Total End-to-End** | **1.5-3s** | Typical |

### Optimizations Applied

✅ **CTranslate2** - 3x faster inference
✅ **INT8 Quantization** - 50% memory, minimal quality loss
✅ **VAD-based segmentation** - Only process speech
✅ **WebSocket streaming** - Minimal transport overhead
✅ **Async processing** - Non-blocking

### Expected Performance (CPU)

- **Throughput:** ~20 segments/minute
- **Latency:** 1.5-3 seconds per segment
- **CPU Usage:** 50-80% (single core)
- **Memory:** ~4GB RAM

### With GPU (if available)

- **Throughput:** ~60 segments/minute
- **Latency:** 0.5-1 seconds per segment
- **GPU Usage:** 20-40%

---

## 🌍 Supported Languages

### Source Languages (Auto-detected)
- English, Spanish, French, German, Italian, Portuguese
- Russian, Japanese, Korean, Chinese, Arabic
- Hindi, Vietnamese, Thai, Indonesian, Turkish
- Dutch, Polish, Ukrainian, Romanian
- **90+ languages total** (Whisper support)

### Target Languages (Selectable)
- Spanish (Español)
- French (Français)
- German (Deutsch)
- Italian (Italiano)
- Portuguese (Português)
- Russian (Русский)
- Japanese (日本語)
- Korean (한국어)
- Chinese (中文)
- Arabic (العربية)

**Easy to add more** - just edit the dropdown in `realtime_client.html`!

---

## 🔧 Troubleshooting

### Microphone Not Working

1. **Check browser permissions** - Allow microphone access
2. **Use HTTPS or localhost** - Modern browsers require secure context
3. **Test microphone** - Try recording in another app

### High Latency

1. **Reduce chunk duration** - Set to 100ms for faster response
2. **Reduce silence threshold** - Set to 300ms
3. **Use GPU** - 3-5x faster inference
4. **Use smaller models** - Whisper Small instead of Medium

### Connection Issues

1. **Check firewall** - Allow port 8001
2. **Check server logs** - Look for errors
3. **Restart server** - Kill and restart

### Transcription Errors

1. **Speak clearly** - Close to microphone
2. **Reduce background noise** - Quiet environment
3. **Check VAD threshold** - May be too strict
4. **Try different language** - Ensure correct language

---

## 🚀 Advanced Usage

### Use GPU for Faster Processing

Edit `realtime_server.py`:
```python
whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
nllb_translator = NLLBTranslatorCT2(device="cuda", compute_type="float16")
```

### Add Opus Compression (Bandwidth Saving)

Client side:
```javascript
// Install opus-recorder library
// Encode to Opus before sending
```

Server side:
```python
# Decode Opus using ffmpeg or libopus
```

### Custom VAD Threshold

```python
self.vad = SileroVAD(threshold=0.7)  # Stricter
```

### Batch Processing

For multiple simultaneous users, use async/await pattern (already implemented).

---

## 📱 Mobile Support

The client works on mobile browsers!

**Tested on:**
- ✅ Chrome (Android)
- ✅ Safari (iOS 15+)
- ✅ Firefox (Android)

**Note:** iOS Safari requires user interaction before microphone access.

---

## 🔐 Security Considerations

### Production Deployment

1. **Use HTTPS/WSS** - Encrypt WebSocket traffic
2. **Add authentication** - Require API keys or tokens
3. **Rate limiting** - Prevent abuse
4. **Input validation** - Sanitize all inputs

### Privacy

- Audio is **not stored** on server
- Temporary files are **deleted immediately**
- All processing is **local** (no third-party APIs)

---

## 🎯 Use Cases

- **Live Event Translation** - Conferences, meetings
- **Customer Support** - Multilingual support calls
- **Language Learning** - Practice speaking with instant feedback
- **Accessibility** - Real-time subtitles for deaf/hard-of-hearing
- **Travel Assistant** - Speak in your language, get translations
- **Content Creation** - Podcast/video translation

---

## 📈 Future Enhancements

- [ ] Multiple simultaneous translations
- [ ] Conversation mode (back-and-forth)
- [ ] Opus audio compression
- [ ] Speaker diarization (who's speaking)
- [ ] Custom vocabulary/terms
- [ ] Save conversation history
- [ ] Mobile app (React Native)
- [ ] Docker deployment
- [ ] Cloud GPU support

---

## 💡 Tips for Best Results

1. **Speak naturally** - Don't rush or speak robotically
2. **Pause between thoughts** - Helps VAD detect boundaries
3. **Quiet environment** - Reduces noise interference
4. **Good microphone** - Better audio = better transcription
5. **Clear articulation** - Especially for non-native languages
6. **One speaker at a time** - System works best with single speaker

---

## 🐛 Known Limitations

- **~2-3 second latency** - Not truly "real-time" conversation
- **Single speaker only** - No multi-speaker support yet
- **CPU-bound** - Inference is main bottleneck
- **No context** - Each segment translated independently
- **Language mixing** - Struggles with code-switching

---

## 📚 Resources

- [Silero VAD](https://github.com/snakers4/silero-vad)
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper)
- [NLLB-200](https://ai.meta.com/research/no-language-left-behind/)
- [CTranslate2](https://github.com/OpenNMT/CTranslate2)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

**Enjoy real-time translation with BabbleFish! 🐟💬✨**
