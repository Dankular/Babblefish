# Changelog

All notable changes to Babblefish will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-02-09

### Added

**Server**:
- FastAPI + WebSocket server with async support
- Modular architecture (rooms, pipeline, transport, speakers packages)
- faster-whisper medium (CTranslate2, int8) for ASR
- NLLB-200-distilled-600M (CTranslate2, int8) for translation
- Support for 50+ languages with ISO 639-1 ↔ Flores-200 mapping
- Room management with multi-participant support
- Opus audio decoding
- Client capability detection framework (for Phase 2/3 adaptive TTS)
- WebSocket protocol with Pydantic message schemas
- Health check endpoint
- Auto-cleanup of empty and idle rooms

**Client**:
- React 19 + Vite development environment
- Silero VAD (ONNX) running in browser (~2MB)
- Audio capture at 16kHz mono with echo cancellation and noise suppression
- Opus encoding via MediaRecorder API
- Auto-reconnecting WebSocket manager with exponential backoff
- 25 pre-configured languages with search functionality
- Live transcript view displaying translations
- Real-time audio level visualization (20-bar indicator)
- Connection status bar
- Responsive dark gradient UI with Tailwind CSS
- Join page for room creation and language selection
- Main room page with participant list and translation display

**Documentation**:
- Comprehensive README with architecture overview
- WebSocket protocol specification (PROTOCOL.md)
- Deployment guide for non-Docker setups (DEPLOYMENT.md)
- Model download instructions (models/README.md)
- Contributing guidelines (CONTRIBUTING.md)
- Setup scripts for Linux/macOS (setup.sh) and Windows (setup.ps1)

**Infrastructure**:
- .gitignore for Python, Node.js, and models
- .env.example for server configuration
- MIT License with third-party license acknowledgments
- Model download script (models/download_server_models.py)

### Architecture

**Design Decisions**:
- CPU-only inference (no GPU required on server)
- Client-side VAD reduces server load
- Cascaded ASR + Translation (faster-whisper + NLLB) for flexibility
- Browser-based audio processing for scalability
- WebSocket for real-time bidirectional communication

**Performance**:
- End-to-end latency: ~1.5 seconds after utterance ends
- ASR latency: ~500ms (3-second audio)
- Translation latency: ~300ms per target language
- Server resources: ~3GB RAM, 4+ CPU cores recommended
- Client resources: Modern browser with microphone access

### Known Limitations (Phase 1)

- Text-only translations (no TTS)
- No speaker diarization (single speaker per utterance assumed)
- No room persistence (rooms deleted when empty)
- No authentication (open access)
- No rate limiting (minimal abuse prevention)

### Future Phases

**Phase 2** (Planned):
- Kokoro TTS integration (generic voices, client-side)
- Audio playback queue
- Server-side TTS fallback for older devices

**Phase 3** (Planned):
- F5-TTS integration (voice cloning, client-side)
- Voice enrollment flow
- Speaker diarization (ECAPA-TDNN)
- Adaptive TTS routing based on client capabilities

**Phase 4** (Planned):
- Production hardening (auth, rate limiting, monitoring)
- PWA support
- Room history and persistence
- Performance optimization

---

## [Unreleased]

### Planned

- Docker deployment (Dockerfile for server and client)
- docker-compose.yml for one-command deployment
- CI/CD pipeline (GitHub Actions)
- Automated testing
- WebSocket stress testing
- Multi-language UI localization

---

[0.1.0]: https://github.com/Dankular/Babblefish/releases/tag/v0.1.0
