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

# Configure GPU acceleration (optional, requires NVIDIA GPU)
echo "DEVICE=cuda" > .env
echo "COMPUTE_TYPE=int8" >> .env

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
├── 3-Tier TTS (adaptive fallback):
│   ├── F5-TTS (200MB) - Voice cloning (primary)
│   ├── Kokoro-82M (160MB) - Lightweight fallback
│   └── Server Chatterbox API - GPU-accelerated final fallback
└── IndexedDB - Voice reference storage
        │ WebSocket (opus audio ↑, json text ↓)
        ▼
🖥️  Server (Python + FastAPI)
├── faster-whisper ASR (~1.5GB, int8) - Speech-to-text
├── NLLB Translation (~600MB, int8) - 200 languages
├── Chatterbox TTS (~1.5GB, GPU) - 23 languages (optional)
├── Room Manager - WebSocket orchestration
└── Pipeline Orchestrator - ASR → Translation flow
```

**Total Server:** ~3GB RAM (CPU-only) or ~5GB RAM + GPU (with Chatterbox TTS)
**Total Client:** ~360MB download (cached), WebGPU or WASM

---

## Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | Text translation (ASR + NLLB, 200 languages) |
| **Phase 2** | ✅ Complete | 3-tier TTS architecture (F5 → Kokoro → Server) |
| **Phase 3** | ✅ Complete | F5-TTS voice cloning + enrollment UI |
| **Phase 4** | 🔄 In Progress | PWA, QR invites, speaker diarization |

---

## Tech Stack

### Server
- **Runtime:** Python 3.11 + FastAPI + uvicorn
- **ASR:** faster-whisper medium (CTranslate2 int8, GPU-accelerated) - ~1.5GB
- **Translation:** NLLB-200-distilled-600M (CTranslate2 int8, GPU-accelerated) - ~600MB
- **TTS:** Kokoro-82M + Chatterbox Multilingual ONNX (optional, with voice profiles, GPU-accelerated)
- **GPU:** CUDA support with int8 quantization (4GB VRAM sufficient)
- **Protocol:** WebSocket + Opus codec
- **Storage:** Voice profiles saved as .npy files with JSON metadata

### Client
- **Framework:** React 19 + Vite + Tailwind CSS
- **TTS (3-Tier):** F5-TTS (~200MB) → Kokoro-82M (~160MB) → Server Chatterbox API
- **VAD:** Silero VAD ONNX (~2MB)
- **Inference:** ONNX Runtime Web (WebGPU/WASM)
- **Storage:** IndexedDB (voice references)

---

## Key Features

- **200 Languages:** NLLB translation coverage
- **Voice Cloning:** F5-TTS with 5-15s enrollment
- **Custom Voice Profiles:** Server-side Chatterbox voice profiles from audio URLs
- **3-Tier TTS:** Adaptive fallback (F5-TTS → Kokoro → Server Chatterbox)
- **Browser-Based:** No app install, models cached in browser
- **CPU Server:** No GPU required for basic operation
- **Adaptive:** Auto-detects WebGPU, falls back to WASM or text-only
- **Privacy:** Voice references stored locally, shared only with room participants

---

## Voice Profile API

Create custom voice profiles for Chatterbox voice cloning:

```bash
# Create a voice profile from URL (reference audio is trimmed to 2 seconds)
curl -X POST http://localhost:8000/api/voice_profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "charlie",
    "url": "https://example.com/audio.mp3",
    "description": "Charlie'\''s voice",
    "max_duration": 2.0
  }'

# List all voice profiles
curl http://localhost:8000/api/voice_profiles

# Synthesize with voice profile
curl -X POST http://localhost:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello World",
    "language": "en",
    "voice_profile": "charlie"
  }'

# Delete a voice profile
curl -X DELETE http://localhost:8000/api/voice_profiles/charlie
```

**Note:** Chatterbox works best with short reference audio (1.5-2 seconds). Longer audio may cause ONNX model errors.

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

## GPU Acceleration

BabbleFish supports NVIDIA GPU acceleration for 2-3x faster processing:

**Requirements:**
- NVIDIA GPU with CUDA support (4GB VRAM minimum)
- CUDA 11.8+ installed
- CUDAExecutionProvider for ONNX Runtime

**Configuration:**
```bash
# Create .env file in project root
DEVICE=cuda
COMPUTE_TYPE=int8  # Optimal for 4GB VRAM

# Or CPU-only mode
DEVICE=cpu
COMPUTE_TYPE=int8
```

**Performance Gains:**
- ASR: 2-3x faster (400ms → 150ms on RTX 3050)
- Translation: 2-3x faster (300ms → 100ms)
- TTS: 1.5-2x faster with GPU inference
- Total latency: ~1.5s → ~0.8s end-to-end

**VRAM Usage (int8 quantization):**
- ASR: ~1.2GB
- Translation: ~800MB
- TTS (optional): ~1.5GB
- **Total:** ~2.5GB (fits comfortably in 4GB)

**Why int8?**
- 40% less VRAM than float16
- Faster inference than float16 on consumer GPUs
- Minimal quality loss (imperceptible for speech)

---

## Performance

**End-to-End Latency:**
- CPU-only: ~1.5-2s after utterance ends
- GPU-accelerated: ~0.8-1.2s after utterance ends

**Pipeline Breakdown (GPU-accelerated):**
- VAD detection: 50-100ms
- Network transfer: 100-200ms
- Server ASR: 150-250ms (2-3x faster with GPU)
- Server translation: 100-200ms (2-3x faster with GPU)
- Client TTS: 300-500ms (Chatterbox) / 500-800ms (F5-TTS)

**CPU-only (for comparison):**
- Server ASR: 400-600ms
- Server translation: 200-400ms

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
