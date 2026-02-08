# BabbleFish Project Context

## Project Overview

BabbleFish is a real-time multi-speaker translation system designed for conversations with multiple people speaking different languages. Think Babel Fish from Hitchhiker's Guide to the Galaxy - everyone speaks their native language and hears others in their preferred language.

## Current Architecture (v2 - Client-Server)

### Server (128-core CPU beast)
- **SeamlessM4T v2 Medium** - All-in-one ASR + Translation
- **Kokoro TTS (ONNX)** - Fast CPU-based speech synthesis
- **Pyannote.audio** - Speaker diarization via voiceprints
- **Multi-client WebSocket** - Handles multiple connected clients
- **Port:** 9000
- **Resource usage:** ~60-70 cores, ~5GB RAM
- **Location:** Powerful server with 2×64-core CPUs

### Thin Clients (Phones/Laptops)
- **Simple VAD** - Energy-based voice activity detection
- **Microphone capture** - Streams audio to server
- **Audio playback** - Receives and plays translated speech
- **WebSocket client** - Connects to server
- **Resource usage:** <10% CPU, GPU completely free
- **Devices:** Dan's phone, Marek's phone, Pierre's laptop (3050 GPU free for future F5-TTS)

## Design Principles

1. **Server does heavy lifting** - All ML models run on 128-core server
2. **Thin clients** - Minimal processing on client devices
3. **Multi-speaker support** - Automatic speaker identification
4. **Real-time performance** - ~1.5-2s latency target
5. **Scalable** - Server can handle multiple simultaneous conversations
6. **GPU-free** - Optimized for CPU inference (frees laptop GPU for F5-TTS later)

## Key Technologies

### Server Stack
- **FastAPI** - WebSocket server
- **Transformers** - SeamlessM4T v2 loading
- **PyTorch** - Model inference (CPU, 32 threads)
- **ONNX Runtime** - Kokoro TTS optimization
- **Pyannote.audio** - Speaker embeddings
- **Librosa** - Audio processing

### Client Stack
- **Web Audio API** - Microphone capture
- **WebSocket API** - Real-time streaming
- **Simple JavaScript** - VAD and playback
- **No dependencies** - Pure HTML/JS client

## Use Case Example

**Scenario:** Pierre (French), Dan (English), Marek (Polish) in a meeting

1. **Pierre speaks French:** "On devrait vérifier la proposition"
   - His laptop captures audio, sends to server
   - Server identifies: speaker_1 (Pierre)
   - Server transcribes: French detected
   - Server translates: EN: "We should check the proposal", PL: "Powinniśmy sprawdzić propozycję"
   - Server synthesizes TTS: Two audio streams (EN + PL)
   - Dan's phone plays English version
   - Marek's phone plays Polish version

2. **Dan speaks English:** "I agree, let's review it now"
   - Same process, translated to FR + PL
   - Pierre hears French
   - Marek hears Polish

3. **Marek speaks Polish:** "Mam kilka pytań"
   - Translated to EN + FR
   - Dan hears English: "I have some questions"
   - Pierre hears French: "J'ai quelques questions"

## Evolution History

### V1: Standalone Servers
- Port 8000: REST API (NLLB + Whisper)
- Port 8001: Real-time WebSocket (no TTS)
- Port 8002: Real-time + TTS (Kokoro + F5-TTS training)
- Port 8003: Multi-speaker + per-speaker voice training

**Problem:** All processing on laptop, maxing out 3050 GPU (4GB VRAM)

### V2: Client-Server (Current)
- Port 9000: CPU Server (SeamlessM4T + Kokoro + Pyannote)
- Thin clients: HTML/JS (minimal resources)

**Benefits:**
- Laptop GPU completely free (4GB available for F5-TTS voice cloning later)
- Server handles multiple clients
- Better scalability
- Lower latency (parallel processing)

## Future Roadmap

### Phase 1 (Current)
- ✅ Client-server architecture
- ✅ SeamlessM4T for ASR + translation
- ✅ Kokoro TTS for synthesis
- ✅ Speaker diarization
- ⏳ Production testing

### Phase 2 (Next)
- F5-TTS voice cloning on laptop GPU
- Server sends TEXT to laptop
- Laptop synthesizes with cloned voice locally
- Per-speaker voice training (passive collection)
- ~300-500ms added latency but authentic voices

### Phase 3 (Future)
- Mobile apps (iOS/Android)
- Multiple simultaneous conversations
- Advanced VAD (Silero on server)
- Opus encoding for bandwidth optimization
- End-to-end encryption

## Technical Constraints

### Performance Targets
- Latency: <2s end-to-end
- CPU usage (server): <60% (leave headroom)
- Memory: <10GB total
- Bandwidth: <100KB/s per client

### Hardware
- **Server:** 2×64-core CPUs, 256GB RAM, no GPU
- **Laptop:** 3050 GPU (4GB VRAM), decent CPU
- **Phones:** Modern smartphones with good mics

### Model Choices
- **SeamlessM4T v2 Medium** - Best CPU performance vs quality
- **Kokoro TTS** - Fast, 82M params, ONNX optimized
- **Pyannote embedding** - Standard speaker diarization
- **F5-TTS** (future) - Voice cloning, ~4GB VRAM

## File Structure

```
BabbleFish/
├── server_cpu.py                        # Main CPU server (port 9000)
├── client_thin.html                     # Thin client (browser)
├── requirements_server.txt              # Server dependencies
│
├── Legacy servers (v1):
│   ├── main.py                          # REST API (port 8000)
│   ├── realtime_server.py               # Real-time (port 8001)
│   ├── realtime_server_tts.py           # TTS (port 8002)
│   ├── realtime_server_multispeaker.py  # Multi-speaker (port 8003)
│   └── requirements*.txt                # Legacy dependencies
│
├── Core libraries:
│   ├── nllb_ct2_fixed.py               # NLLB with CTranslate2
│   ├── tts_engine.py                   # TTS + speaker training
│   ├── speaker_diarization.py          # Pyannote integration
│   └── config.py                       # Configuration
│
├── Documentation:
│   ├── README.md                       # Main documentation
│   ├── CLAUDE.md                       # This file (project context)
│   ├── ARCHITECTURE.md                 # Detailed architecture
│   ├── TTS_SETUP.md                    # TTS guide (legacy)
│   └── MULTISPEAKER_SETUP.md           # Multi-speaker guide (legacy)
│
└── Testing:
    ├── quick_benchmark.py              # Performance testing
    └── benchmark_suite.py              # Comprehensive benchmarks
```

## Common Tasks

### Start Production Server
```bash
# On server
cd /path/to/BabbleFish
source venv/bin/activate  # or Windows: venv\Scripts\activate
python server_cpu.py
```

### Connect Client
```bash
# On laptop/phone browser
# Open: client_thin.html
# Enter server URL: ws://192.168.1.100:9000/ws/client
# Select target language
# Start speaking
```

### Monitor Performance
```bash
# On server
htop  # Watch CPU usage (target: <60%)
```

### Debugging
```bash
# Server logs
tail -f server.log

# Test WebSocket connection
# Browser console: should see "Connected to server"

# Test speaker identification
curl http://server-ip:9000/speakers
```

## Known Issues & Solutions

### Issue: High latency (>3s)
**Solution:** Check SeamlessM4T thread count, ensure 32+ threads allocated

### Issue: TTS not playing on client
**Solution:** Ensure browser allows audio playback (user must interact with page first)

### Issue: Speaker identification not working
**Solution:** Verify Hugging Face authentication, check pyannote model loaded

### Issue: WebSocket disconnects
**Solution:** Check firewall, ensure port 9000 open, verify server IP address

## Important Notes

1. **Hugging Face Auth:** Pyannote models require HF login and accepting terms
2. **Thread Allocation:** SeamlessM4T needs 32 threads minimum for good performance
3. **Audio Format:** 16kHz mono, int16 PCM over WebSocket
4. **Language Codes:** Use 3-letter codes (eng, spa, fra, deu, pol)
5. **Client VAD:** Simple energy-based, 500ms silence detection
6. **Server VAD:** Not implemented (assumes client sends complete utterances)

## Performance Benchmarks

### Target Metrics (Server with 128 cores)
- SeamlessM4T inference: ~800ms (3s audio)
- Kokoro TTS synthesis: ~300ms (one sentence)
- Speaker identification: ~50ms
- Total pipeline: ~1.5s

### Actual Performance (to be measured)
- TODO: Run production tests
- TODO: Measure concurrent client performance
- TODO: Stress test with 5+ simultaneous speakers

## Development Workflow

1. **Make changes** to server_cpu.py or client_thin.html
2. **Restart server** if server-side changes
3. **Refresh browser** if client-side changes
4. **Test with real audio** (not synthetic)
5. **Monitor latency** in browser console
6. **Check server logs** for errors

## Contact & Support

- **Developer:** Claude (AI Assistant)
- **User:** Dan (+ Marek, Pierre)
- **Primary use case:** Multi-lingual business meetings
- **Deployment:** Local network (no cloud)

---

**Last Updated:** 2026-02-08
**Architecture Version:** 2.0 (Client-Server)
**Status:** Active Development
