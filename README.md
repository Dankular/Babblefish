# 🐟 Babblefish

**Realtime Voice Translation in Your Browser**

*"The Babel Fish is small, yellow, leech-like, and probably the oddest thing in the universe."*
— Douglas Adams

---

## Vision

Open a URL on your phone. Select your language. Hear everyone speak to you in your language, in their voice. No app install. No dedicated hardware.

---

## Quick Start

```bash
# Clone
git clone https://github.com/Dankular/Babblefish.git
cd Babblefish

# Download models (~3GB)
python models/download_server_models.py

# Run server
cd server && python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Run client (separate terminal)
cd client && npm install && npm run dev

# Or use Docker
docker-compose up
```

Open http://localhost:3000 → Join room → Start speaking

---

## Architecture

```
📱 Browser Clients (React + WebGPU)
├── Silero VAD (2MB) - Voice activity detection
├── Opus Encoder - Audio compression
├── Chatterbox TTS (500MB) - Natural voice (23 langs)
├── F5-TTS (200MB) - Voice cloning
└── IndexedDB - Voice reference storage
        │ WebSocket (opus audio ↑, json text ↓)
        ▼
🖥️  Server (Python + FastAPI, CPU-only)
├── faster-whisper ASR (~1.5GB, int8) - Speech-to-text
├── NLLB Translation (~600MB, int8) - 200 languages
├── Room Manager - WebSocket orchestration
└── Pipeline Orchestrator - ASR → Translation flow
```

**Total Server:** ~3GB RAM, CPU-only
**Total Client:** ~700MB download (cached), WebGPU or WASM

---

## Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | Text translation (ASR + NLLB, 200 languages) |
| **Phase 2** | ✅ Complete | Chatterbox TTS (23 languages, natural voice) |
| **Phase 3** | ✅ Complete | F5-TTS voice cloning architecture |
| **Phase 4** | 🔄 In Progress | PWA, QR invites, speaker diarization |

---

## Tech Stack

### Server
- **Runtime:** Python 3.11 + FastAPI + uvicorn
- **ASR:** faster-whisper medium (CTranslate2 int8) - ~1.5GB
- **Translation:** NLLB-200-distilled-600M (CTranslate2 int8) - ~600MB
- **Protocol:** WebSocket + Opus codec

### Client
- **Framework:** React 19 + Vite + Tailwind CSS
- **TTS:** Chatterbox Multilingual ONNX (~500MB) + F5-TTS (~200MB)
- **VAD:** Silero VAD ONNX (~2MB)
- **Inference:** ONNX Runtime Web (WebGPU/WASM)
- **Storage:** IndexedDB (voice references)

---

## Key Features

- **200 Languages:** NLLB translation coverage
- **Voice Cloning:** F5-TTS with 5-15s enrollment
- **Browser-Based:** No app install, models cached in browser
- **CPU Server:** No GPU required, runs on any machine
- **Adaptive:** Auto-detects WebGPU, falls back to WASM or text-only
- **Privacy:** Voice references stored locally, shared only with room participants

---

## WebSocket Protocol

### Client → Server
```typescript
// Join room
{ type: "join", room_id: "abc123", language: "fr", name: "Pierre" }

// Audio chunk (VAD-gated)
{ type: "audio", data: "<base64_opus>", timestamp: 1707400000 }

// Utterance complete
{ type: "utterance_end", timestamp: 1707400002 }

// Leave
{ type: "leave" }
```

### Server → Client
```typescript
// Room joined
{ type: "joined", room_id: "abc123", participant_id: "P_01", participants: [...] }

// Translation result
{
  type: "translation",
  speaker_id: "P_01",
  speaker_name: "Pierre",
  source_lang: "fr",
  source_text: "Bonjour",
  translations: { "en": "Hello", "es": "Hola" },
  timestamp: 1707400002
}

// Participant events
{ type: "participant_joined", participant: {...} }
{ type: "participant_left", participant_id: "P_03" }
```

---

## Models

### Server Models (Required)
```bash
# Download with script
python models/download_server_models.py

# Or manually
# faster-whisper: Auto-downloads on first use
# NLLB: Download + convert to CTranslate2 format
```

### Client Models (Browser, Auto-Download)
- **Chatterbox Multilingual:** ~500MB (23 languages)
- **F5-TTS:** ~200MB (voice cloning, 3-stage pipeline)
- **Silero VAD:** ~2MB (voice activity detection)

---

## Project Structure

```
Babblefish/
├── server/              # FastAPI async server
│   ├── main.py         # Entry point
│   ├── config.py       # Configuration
│   ├── rooms/          # Room management
│   ├── pipeline/       # ASR + Translation
│   ├── transport/      # WebSocket + Opus
│   └── speakers/       # Speaker registry (stub)
│
├── client/             # React browser app
│   ├── src/
│   │   ├── core/       # TTS, VAD, audio, voice
│   │   ├── network/    # WebSocket, protocol
│   │   ├── pages/      # Join, Room
│   │   ├── components/ # UI components
│   │   └── hooks/      # React hooks
│   └── public/
│
├── models/             # Model download scripts
└── docs/               # Documentation
```

---

## Why These Technologies?

**faster-whisper + NLLB** over SeamlessM4T:
- Better CPU performance (CTranslate2 int8 optimization)
- 200 languages vs 96
- Independent ASR/translation swapping
- Easier debugging

**Chatterbox Multilingual:**
- Native 23-language support
- ONNX + WebGPU ready
- Natural prosody, reasonable size (~500MB)

**F5-TTS:**
- Browser-proven ONNX implementation
- Voice cloning with short reference (~5-10s)
- ~200MB, runs in browser via WebGPU

**Client-Side TTS:**
- No server GPU required
- Scales infinitely (compute on each client)
- Lower latency (local synthesis)
- Privacy (models cached locally)

---

## Performance

**End-to-End Latency:** ~1.5-2s after utterance ends

**Pipeline Breakdown:**
- VAD detection: 50-100ms
- Network transfer: 100-200ms
- Server ASR: 400-600ms
- Server translation: 200-400ms
- Client TTS: 300-500ms (Chatterbox) / 500-800ms (F5-TTS)

---

## Reference Implementations

| Component | Repository |
|-----------|------------|
| F5-TTS ONNX | [huggingfacess/F5-TTS-ONNX](https://huggingface.co/huggingfacess/F5-TTS-ONNX) |
| F5-TTS Browser | [nsarang/voice-cloning-f5-tts](https://github.com/nsarang/voice-cloning-f5-tts) |
| Chatterbox | [onnx-community/chatterbox-multilingual-ONNX](https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX) |
| faster-whisper | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| CTranslate2 | [OpenNMT/CTranslate2](https://github.com/OpenNMT/CTranslate2) |

---

## License

MIT — because language should have no barriers.
