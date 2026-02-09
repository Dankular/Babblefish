# 🐟 Babblefish

**A Realtime Voice Translation Tool**

*"The Babel Fish is small, yellow, leech-like, and probably the oddest thing in the universe."*
— Douglas Adams, The Hitchhiker's Guide to the Galaxy

---

## Vision

Open a URL on your phone. Select your language. Hear everyone in the room speak to you in your language, in their voice. No app install. No dedicated hardware. Just a browser.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PARTICIPANT PHONES                       │
│                                                             │
│  📱 Pierre (FR)       📱 Marek (PL)       📱 Dan (EN)      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Silero VAD   │    │ Silero VAD   │    │ Silero VAD   │  │
│  │ Opus Encode  │    │ Opus Encode  │    │ Opus Encode  │  │
│  │ F5-TTS(WebGPU│    │ F5-TTS(WebGPU│    │ F5-TTS(WebGPU│  │
│  │ Voice Refs   │    │ Voice Refs   │    │ Voice Refs   │  │
│  │ Cache (A,C)  │    │ Cache (A,C)  │    │ Cache (A,B)  │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
└─────────┼───────────────────┼───────────────────┼───────────┘
          │   WebSocket       │   WebSocket       │   WebSocket
          │   (opus audio ↑)  │   (opus audio ↑)  │   (opus audio ↑)
          │   (json text  ↓)  │   (json text  ↓)  │   (json text  ↓)
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    BABBLEFISH SERVER                         │
│                    (128-core CPU, no GPU)                    │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Room Manager │  │ Speaker      │  │ ASR + Translation │  │
│  │             │  │ Diarization  │  │                   │  │
│  │ WebSocket   │  │ ECAPA-TDNN   │  │ faster-whisper    │  │
│  │ Hub         │  │ (~80MB, CPU) │  │ medium (int8)     │  │
│  │             │  │              │  │ (~1.5GB, CPU)     │  │
│  │ Routing     │  │ Speaker      │  │                   │  │
│  │ Matrix      │  │ Registry     │  │ NLLB-600M         │  │
│  │             │  │              │  │ (~1.2GB, CPU)     │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│                                                             │
│  Total: ~40 threads, ~3GB RAM                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Babblefish/
│
├── README.md
├── LICENSE                          # MIT
├── docker-compose.yml               # Full stack orchestration
├── .env.example                     # Configuration template
│
├── server/                          # Python async server
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   │
│   ├── main.py                      # FastAPI + WebSocket entry point
│   ├── config.py                    # Server configuration / env vars
│   │
│   ├── rooms/                       # Room & session management
│   │   ├── __init__.py
│   │   ├── manager.py               # Room lifecycle (create/join/leave)
│   │   ├── room.py                  # Room state (participants, routing matrix)
│   │   └── participant.py           # Participant model (speaker_id, language, ws)
│   │
│   ├── pipeline/                    # ML inference pipeline
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Pipeline coordinator (audio in → text out)
│   │   ├── vad.py                   # Server-side Silero VAD (backup/validation)
│   │   ├── diarization.py           # SpeechBrain ECAPA-TDNN speaker embeddings
│   │   ├── asr.py                   # faster-whisper (CTranslate2, int8)
│   │   ├── translate.py             # NLLB-200-distilled-600M (CTranslate2)
│   │   └── language.py              # Language detection + code mapping
│   │
│   ├── speakers/                    # Speaker registry & voice management
│   │   ├── __init__.py
│   │   ├── registry.py              # Speaker tracking across sessions
│   │   ├── embeddings.py            # Speaker embedding comparison / matching
│   │   └── enrolment.py             # Enrolment flow (accumulate clean speech)
│   │
│   ├── transport/                   # WebSocket protocol
│   │   ├── __init__.py
│   │   ├── handler.py               # WS connection lifecycle
│   │   ├── protocol.py              # Message types & serialisation
│   │   └── audio_codec.py           # Opus decode on server side
│   │
│   └── tests/
│       ├── test_pipeline.py
│       ├── test_rooms.py
│       ├── test_diarization.py
│       └── conftest.py
│
├── client/                          # Browser client (React + Vite)
│   ├── Dockerfile                   # Static file server (nginx)
│   ├── package.json
│   ├── vite.config.js
│   ├── tsconfig.json
│   ├── index.html
│   │
│   ├── public/
│   │   ├── favicon.ico
│   │   └── manifest.json            # PWA manifest
│   │
│   ├── src/
│   │   ├── main.jsx                 # App entry point
│   │   ├── App.jsx                  # Root component + routing
│   │   │
│   │   ├── core/                    # ML inference (runs in Web Worker)
│   │   │   ├── f5tts/               # F5-TTS ONNX inference
│   │   │   │   ├── model.js         # F5-TTS 3-stage pipeline (encoder→transformer→decoder)
│   │   │   │   ├── processor.js     # Audio preprocessing (mel spectrogram, normalisation)
│   │   │   │   └── config.js        # Model paths, NFE steps, chunk sizes
│   │   │   │
│   │   │   ├── vad/                 # Voice Activity Detection
│   │   │   │   ├── silero.js        # Silero VAD (ONNX/WASM, ~2MB)
│   │   │   │   └── processor.js     # Utterance boundary detection + buffering
│   │   │   │
│   │   │   ├── audio/               # Audio capture & processing
│   │   │   │   ├── capture.js       # Mic access (getUserMedia)
│   │   │   │   ├── opus.js          # Opus encode via MediaRecorder / manual encoder
│   │   │   │   ├── playback.js      # Audio output queue + Web Audio API
│   │   │   │   └── utils.js         # RMS normalisation, resampling, silence detection
│   │   │   │
│   │   │   ├── device.js            # WebGPU capability detection + WASM fallback
│   │   │   └── worker.js            # Web Worker entry (F5-TTS + VAD inference)
│   │   │
│   │   ├── engine/                  # Model lifecycle & communication
│   │   │   ├── ModelProvider.jsx    # React context for model state
│   │   │   ├── adapters.js          # Model adapter registry (F5-TTS, Kokoro fallback)
│   │   │   └── serialization.js     # Tensor serialisation for Worker ↔ Main thread
│   │   │
│   │   ├── network/                 # Server communication
│   │   │   ├── websocket.js         # WebSocket connection manager (reconnect, heartbeat)
│   │   │   ├── protocol.js          # Message types matching server protocol
│   │   │   └── room.js              # Room join/leave/state sync
│   │   │
│   │   ├── speakers/                # Speaker management (client-side)
│   │   │   ├── registry.js          # Local speaker voice reference cache
│   │   │   ├── enrolment.js         # Guided enrolment flow (record 15s, upload)
│   │   │   └── voiceref.js          # Voice reference storage (IndexedDB)
│   │   │
│   │   ├── pages/                   # UI screens
│   │   │   ├── JoinPage.jsx         # Room code entry + language selection
│   │   │   ├── EnrolPage.jsx        # "Please speak for 15 seconds" enrolment
│   │   │   ├── RoomPage.jsx         # Main translation view (active session)
│   │   │   └── LoadingPage.jsx      # Model download progress
│   │   │
│   │   ├── components/              # Reusable UI components
│   │   │   ├── LanguageSelector.jsx # Language picker dropdown
│   │   │   ├── SpeakerIndicator.jsx # "Pierre is speaking..." visual indicator
│   │   │   ├── TranscriptView.jsx   # Live transcript with translations
│   │   │   ├── StatusBar.jsx        # Connection status, model status, latency
│   │   │   ├── VolumeIndicator.jsx  # Mic input level visualiser
│   │   │   └── QRInvite.jsx         # QR code to invite others to room
│   │   │
│   │   ├── hooks/                   # Custom React hooks
│   │   │   ├── useAudioCapture.js   # Mic capture + VAD integration
│   │   │   ├── useWebSocket.js      # WS connection with auto-reconnect
│   │   │   ├── useTTS.js            # F5-TTS synthesis trigger
│   │   │   ├── useRoom.js           # Room state management
│   │   │   └── useSpeakers.js       # Speaker registry + voice refs
│   │   │
│   │   ├── utils/
│   │   │   ├── constants.js         # App-wide constants
│   │   │   └── logger.js            # Structured logging
│   │   │
│   │   └── styles/
│   │       └── globals.css          # Tailwind + custom styles
│   │
│   └── tests/
│       ├── core/
│       │   └── f5tts.test.js
│       └── network/
│           └── websocket.test.js
│
├── models/                          # Model download & caching scripts
│   ├── download_server_models.py    # Script to pull faster-whisper + NLLB
│   └── README.md                    # Model versions, sizes, licenses
│
└── docs/
    ├── ARCHITECTURE.md              # Detailed architecture documentation
    ├── PROTOCOL.md                  # WebSocket message protocol specification
    ├── MODELS.md                    # Model selection rationale & benchmarks
    ├── DEPLOYMENT.md                # Deployment guide (Docker, bare metal)
    └── CONTRIBUTING.md
```

---

## WebSocket Protocol

### Client → Server Messages

```typescript
// Join a room
{
  type: "join",
  room_id: "abc123",
  language: "fr",         // ISO 639-1
  name: "Pierre"
}

// Audio chunk (during speech, gated by client-side VAD)
{
  type: "audio",
  data: "<base64 opus>",  // Opus-encoded audio chunk (~200ms)
  timestamp: 1707400000   // Client timestamp for latency tracking
}

// Utterance boundary (client VAD detected pause)
{
  type: "utterance_end",
  timestamp: 1707400002
}

// Speaker enrolment audio
{
  type: "enrol",
  audio: "<base64 PCM>",  // 15s of clean speech, 16kHz mono
}

// Leave room
{
  type: "leave"
}
```

### Server → Client Messages

```typescript
// Room joined confirmation
{
  type: "joined",
  room_id: "abc123",
  participant_id: "P_01",
  participants: [
    { id: "P_02", name: "Marek", language: "pl", enrolled: true }
  ]
}

// New speaker enrolled — distribute voice reference
{
  type: "speaker_enrolled",
  participant_id: "P_01",
  name: "Pierre",
  language: "fr",
  reference_audio: "<base64 PCM>",   // ~200KB for 15s @ 16kHz
  reference_text: "Bonjour, je m'appelle Pierre..."  // Whisper transcription
}

// Translation result — the core message
{
  type: "translation",
  speaker_id: "P_01",               // Who said it
  speaker_name: "Pierre",
  source_lang: "fr",
  source_text: "On devrait vérifier la proposition",
  translations: {
    "en": "We should check the proposal",
    "pl": "Powinniśmy sprawdzić propozycję"
  },
  timestamp: 1707400002
}

// Participant joined/left
{
  type: "participant_joined",
  participant: { id: "P_03", name: "Dan", language: "en" }
}

{
  type: "participant_left",
  participant_id: "P_03"
}
```

---

## Data Flow — Single Utterance

```
Timeline (ms)     Phone (Pierre)         Server                  Phone (Marek)
─────────────────────────────────────────────────────────────────────────────

0                  Pierre starts
                   speaking French

50                 Silero VAD: speech
                   detected (local)
                   Opus encode begins

100-1500           Streaming opus        Receiving audio
                   chunks via WS →       chunks, buffering
                                         with speaker ID

1500               VAD: pause detected
                   sends utterance_end →

1600                                     ECAPA-TDNN:
                                         match → "P_01" (Pierre)

1800                                     faster-whisper (int8):
                                         "On devrait vérifier
                                          la proposition"
                                         lang: "fr"

2200                                     NLLB-600M:
                                         → en: "We should check..."
                                         → pl: "Powinniśmy..."

2300                                     Push translation        Receives:
                                         to all phones →         { speaker: P_01,
                                                                   text: "Powinniśmy...",
                                                                   lang: "pl" }

2400                                                             Lookup P_01 voice ref
                                                                 (cached from enrolment)

2500                                                             F5-TTS (WebGPU):
                                                                 Synthesise Polish text
                                                                 in Pierre's voice
                                                                 (~500ms on modern phone)

3000                                                             🔊 Marek hears Pierre
                                                                    speaking Polish,
                                                                    in Pierre's voice
```

**End-to-end: ~1.5 seconds after utterance ends**

---

## Phase Plan

### Phase 1 — MVP: Text Translation Only (No TTS)

**Goal:** Prove the server pipeline works. Phones display translated text.

- [ ] Server: WebSocket room management
- [ ] Server: Opus decode
- [ ] Server: faster-whisper ASR + language detection
- [ ] Server: NLLB translation to all target languages
- [ ] Client: Mic capture + Opus encode + WebSocket stream
- [ ] Client: Silero VAD (client-side, only send speech)
- [ ] Client: Join room, select language, display translated text
- [ ] Docker: Server containerisation

**Deliverable:** Open URL → join room → speak → see translations as text on all phones.

### Phase 2 — TTS: Hear Translations (Generic Voice) ✅ COMPLETE

**Goal:** Add audio output using Chatterbox Multilingual (23 languages, no cloning).

- [x] Client: Chatterbox Multilingual ONNX via ONNX Runtime Web + WebGPU/WASM
- [x] Client: Auto-synthesise incoming translations
- [x] Client: Audio playback queue (handle overlapping utterances)
- [x] Client: WebGPU detection + WASM fallback
- [x] Client: Model download progress UI with loading states
- [x] Client: useTTS hook with status tracking
- [x] Client: TTSStatus component for user feedback

**Deliverable:** Open URL → join room → speak → hear translations in a natural voice (23 languages).

### Phase 3 — Voice Cloning: Hear Their Voice

**Goal:** Replace Kokoro with F5-TTS. Each person sounds like themselves.

- [ ] Client: F5-TTS ONNX integration (based on nsarang/voice-cloning-f5-tts)
- [ ] Client: Enrolment flow ("Please speak for 15 seconds")
- [ ] Server: Enrolment pipeline (clean speech extraction, transcription)
- [ ] Server: Broadcast voice references to all participants
- [ ] Client: Voice reference cache (IndexedDB)
- [ ] Client: F5-TTS synthesis with speaker-specific voice reference
- [ ] Client: Graceful degradation (F5-TTS → Kokoro → text-only)

**Deliverable:** Open URL → enrol voice → join room → hear everyone in their voice, in your language.

### Phase 4 — Production Hardening

**Goal:** Make it robust for real-world use.

- [ ] Server: Speaker diarization (handle turn-taking, overlapping speech)
- [ ] Server: Translation caching (same text + same target = cached)
- [ ] Client: Adaptive model selection (detect phone GPU capability)
- [ ] Client: PWA support (installable, offline model cache)
- [ ] Client: QR code room invite
- [ ] Server: Latency monitoring + metrics
- [ ] Server: Rate limiting + abuse prevention
- [ ] Docs: Deployment guide for self-hosting
- [ ] Tests: End-to-end integration tests

### Phase 5 — Future

- [ ] SeamlessStreaming integration (simultaneous translation, lower latency)
- [ ] Chatterbox Multilingual as alternative TTS (if ONNX port becomes available)
- [ ] Multi-room support on single server
- [ ] Recording / transcript export
- [ ] Noise cancellation preprocessing
- [ ] Whisper fine-tuning for specific accents/domains

---

## Tech Stack Summary

### Server

| Component | Technology | Size | Purpose |
|---|---|---|---|
| Runtime | Python 3.11 + FastAPI + uvicorn | — | Async WebSocket server |
| ASR | faster-whisper medium (CTranslate2 int8) | ~1.5 GB RAM | Speech-to-text + lang ID |
| Translation | NLLB-200-distilled-600M (CTranslate2) | ~1.2 GB RAM | Text translation (200 langs) |
| Speaker ID | SpeechBrain ECAPA-TDNN | ~80 MB RAM | Speaker embeddings |
| VAD (backup) | Silero VAD | ~2 MB RAM | Server-side validation |
| Audio codec | Opus via opuslib | — | Decode incoming audio |
| **Total** | | **~3 GB RAM, ~40 threads** | |

### Client (Browser)

| Component | Technology | Size (download) | Purpose |
|---|---|---|---|
| TTS (Phase 2) ✅ | Chatterbox Multilingual ONNX | ~500 MB (cached) | Natural TTS, 23 languages |
| TTS (Phase 3) | F5-TTS ONNX (fp16) | ~200 MB (cached) | Voice cloning TTS |
| VAD | Silero VAD ONNX | ~2 MB | Speech/silence detection |
| Inference | ONNX Runtime Web | ~5 MB | WebGPU/WASM model execution |
| Audio | Web Audio API + MediaRecorder | — | Capture + playback |
| UI | React 19 + Tailwind CSS | — | Interface |
| Build | Vite | — | Dev server + bundling |

### Infrastructure

| Component | Requirement |
|---|---|
| Server hardware | Any machine with 4+ CPU cores, 8+ GB RAM (128-core is luxury) |
| GPU | Not required anywhere |
| Network | LAN for lowest latency; works over internet too |
| Client devices | Any phone/laptop with Chrome 121+ / Safari 26+ / Firefox 141+ |
| Docker | Optional but recommended for deployment |

---

## Model Decisions & Rationale

### Why faster-whisper + NLLB (cascaded) over SeamlessM4T (unified)?

- **CPU performance:** CTranslate2 models are specifically optimised for CPU inference with int8 quantisation. SeamlessM4T on CPU is significantly slower.
- **Flexibility:** Can swap ASR or translation model independently. Can add language-pair-specific models (Helsinki-NLP Opus-MT) for better quality on specific pairs.
- **Language coverage:** NLLB covers 200 languages vs SeamlessM4T's ~96 for text output.
- **Debuggability:** Can inspect ASR output before translation. Easier to identify where errors occur.

### Why F5-TTS over Chatterbox Multilingual?

- **Browser-proven:** F5-TTS has a working ONNX + WebGPU implementation (nsarang/voice-cloning-f5-tts). Chatterbox has no ONNX port yet.
- **Size:** F5-TTS at ~200MB fp16 is manageable as a browser download. Chatterbox Multilingual at 500M would be ~500MB+.
- **Voice cloning quality:** F5-TTS and Chatterbox are comparable in voice cloning quality. F5-TTS wins on availability.
- **Trade-off acknowledged:** Chatterbox has better multilingual coverage (23 languages natively). F5-TTS multilingual capability is more limited. If/when Chatterbox gets an ONNX port, it becomes the better choice.

### Why Chatterbox Multilingual for Phase 2?

- **Native 23-language support** — English, French, Spanish, German, Italian, Portuguese, Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Japanese, Hungarian, Korean, Hindi, Finnish, Vietnamese, Thai, Danish, Swedish, Ukrainian
- **ONNX + WebGPU support** — runs in browser with hardware acceleration
- **~500MB model size** — reasonable one-time download with browser caching
- **Natural prosody** — better quality than Kokoro for multilingual use case
- No voice cloning, but provides high-quality audio output while F5-TTS integration is developed

---

## Key Reference Implementations

| What | Repo | Relevance |
|---|---|---|
| F5-TTS in browser (WebGPU) | [nsarang/voice-cloning-f5-tts](https://github.com/nsarang/voice-cloning-f5-tts) | Core TTS implementation to adapt |
| Chatterbox Multilingual | [onnx-community/chatterbox-multilingual-ONNX](https://huggingface.co/onnx-community/chatterbox-multilingual-ONNX) | Phase 2 TTS (23 languages) ✅ |
| Transformers.js | [huggingface/transformers.js](https://github.com/huggingface/transformers.js) | ONNX Runtime Web + model loading |
| faster-whisper | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Server-side ASR |
| CTranslate2 | [OpenNMT/CTranslate2](https://github.com/OpenNMT/CTranslate2) | CPU-optimised inference for NLLB |
| Silero VAD | [snakers4/silero-vad](https://github.com/snakers4/silero-vad) | Voice activity detection |
| SpeechBrain | [speechbrain/speechbrain](https://github.com/speechbrain/speechbrain) | Speaker embeddings (ECAPA-TDNN) |

---

## Supported Languages (Server Translation — NLLB-200)

200 languages. Notable coverage for the Babel Fish use case:

**European:** English, French, German, Spanish, Portuguese, Italian, Dutch, Polish, Czech, Slovak, Romanian, Hungarian, Greek, Swedish, Norwegian, Danish, Finnish, Bulgarian, Croatian, Serbian, Slovenian, Lithuanian, Latvian, Estonian, Ukrainian, Russian

**Asian:** Mandarin, Cantonese, Japanese, Korean, Hindi, Bengali, Tamil, Thai, Vietnamese, Indonesian, Malay, Tagalog, Burmese, Khmer

**Middle Eastern / African:** Arabic, Hebrew, Turkish, Persian, Swahili, Amharic, Yoruba, Igbo, Hausa, Zulu

**F5-TTS voice output:** English primary, with emerging multilingual support. The cloned voice speaks in the target language with the source speaker's vocal characteristics. Quality varies by language — best results for languages with similar phonetic systems.

---

## Getting Started (Development)

```bash
# Clone
git clone https://github.com/Dankular/Babblefish.git
cd Babblefish

# Server
cd server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python models/download_server_models.py   # Downloads ~3GB of models
uvicorn main:app --host 0.0.0.0 --port 8000

# Client (separate terminal)
cd client
npm install
npm run dev
# Opens at http://localhost:5173

# Or with Docker
docker-compose up
```

---

## License

MIT — because language should have no barriers.
