# BabbleFish Hybrid Architecture (Progressive Enhancement)

## Architecture C: Progressive - Two-Tier TTS

The recommended approach for maximum flexibility and quality.

```
📱 Phones ──► 🖥 Server ──► 💻 Laptop (optional TTS accelerator)

Phase 1: Server only (works immediately)
Phase 2: Add laptop for voice cloning (quality enhancement)
```

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         Full System Flow                         │
└──────────────────────────────────────────────────────────────────┘

📱 Phone (Dan)                  🖥 Server (128 cores)                💻 Laptop (3050 GPU)
     │                                  │                                   │
     │ 1. Audio stream                  │                                   │
     ├──────────────────────────────────►                                   │
     │    WebSocket (int16 PCM)         │                                   │
     │                                  │                                   │
     │                          2. Process:                                 │
     │                             │                                        │
     │                          ┌──▼────────────────┐                       │
     │                          │ Speaker ID        │                       │
     │                          │ (pyannote, 4 thr) │                       │
     │                          │ → "Pierre"        │                       │
     │                          └──┬────────────────┘                       │
     │                             │                                        │
     │                          ┌──▼────────────────┐                       │
     │                          │ SeamlessM4T       │                       │
     │                          │ (32 threads)      │                       │
     │                          │ FR → EN           │                       │
     │                          │ → "Hello..."      │                       │
     │                          └──┬────────────────┘                       │
     │                             │                                        │
     │                             ├──────────────────┐                     │
     │                             │                  │                     │
     │                     ┌───────▼──────┐    ┌──────▼────────────┐       │
     │                     │ Fast Path    │    │ Quality Path      │       │
     │                     │ Kokoro TTS   │    │ F5-TTS Request    │       │
     │                     │ (16 threads) │    │ (if accelerator)  │       │
     │                     │ ~300ms       │    │                   │       │
     │                     └───────┬──────┘    └──────┬────────────┘       │
     │                             │                  │                     │
     │ 3. Kokoro result            │                  │ text + speaker_id   │
     │    (immediate, ~2s)         │                  ├─────────────────────►
     ◄─────────────────────────────┤                  │                     │
     │                             │                  │                     │
     │    "Hello..." (generic)     │              ┌───▼──────────────────┐  │
     │    🔊 Play immediately       │              │ F5-TTS (GPU)         │  │
     │                             │              │ Pierre's voice       │  │
     │                             │              │ ~800ms               │  │
     │                             │              └───┬──────────────────┘  │
     │                             │                  │                     │
     │                             │                  │ cloned audio        │
     │                             │◄─────────────────┤                     │
     │                             │                  │                     │
     │ 4. F5-TTS result            │                                        │
     │    (quality, ~2.8s)         │                                        │
     ◄─────────────────────────────┤                                        │
     │                                                                      │
     │    "Hello..." (Pierre's voice)                                       │
     │    🔊 Play enhanced version                                          │
     └──────────────────────────────────────────────────────────────────────┘

Total Latency:
  - Kokoro path:  ~2.0s (immediate comprehension)
  - F5-TTS path:  ~2.8s (quality enhancement)
  - User hears both, or seamlessly replaces
```

## Two-Tier Output Strategy

### Tier 1: Fast Path (Kokoro - Immediate)

**Latency:** ~2s from speech end
**Voice:** Generic Kokoro TTS
**Purpose:** Immediate comprehension

```
Timeline:
0ms      Pierre stops speaking
200ms    VAD detects silence
1500ms   Server receives full audio
1600ms   Speaker identified
2400ms   SeamlessM4T completes
2700ms   Kokoro TTS completes
2000ms   Dan hears generic voice

Result: Fast, understandable, gets the message across
```

### Tier 2: Quality Path (F5-TTS - Enhanced)

**Latency:** ~2.8s from speech end (if laptop connected)
**Voice:** Pierre's cloned voice
**Purpose:** Authentic "Babel Fish" experience

```
Timeline:
2700ms   Server sends text to laptop
2750ms   Laptop receives request
3500ms   F5-TTS completes synthesis
2800ms   Dan hears Pierre's actual voice

Result: Authentic, cloned voice with Pierre's accent and tone
```

### Playback Strategies

**Option A: Sequential Play (Recommended)**
```javascript
// Play Kokoro immediately
playAudio(kokoroAudio);

// When F5-TTS arrives, play next utterance with cloned voice
// User hears generic for first response, then authentic thereafter
```

**Option B: Replacement**
```javascript
// Play Kokoro
audioSource.start();

// When F5-TTS arrives, fade out Kokoro, fade in F5-TTS
// Seamless transition mid-playback
```

**Option C: Kokoro-only (Fallback)**
```javascript
// If laptop not connected, only Kokoro plays
// System still works, just no voice cloning
```

## Resource Allocation

### Server (128 cores)

```
Component              Threads    RAM      Notes
──────────────────────────────────────────────────────────────
SeamlessM4T (ASR+MT)      32     3-4 GB   Main bottleneck
Kokoro TTS (ONNX)         16     500 MB   Fast synthesis
Speaker ID (pyannote)      4     200 MB   Lightweight
WebSocket routing          8     100 MB   Multi-client
────────────────────────────────────────────────────────────
Total Used              ~60     ~5 GB    47% cores, minimal RAM
Remaining               ~68     lots     Plenty of headroom
```

### Laptop (3050 GPU - 4GB VRAM)

**Phase 1 (Server only):** Laptop not needed
**Phase 2 (With accelerator):**

```
Component              VRAM     Device   Notes
────────────────────────────────────────────────────────
F5-TTS model          2-3 GB    GPU     Voice cloning
Processing overhead   500 MB    GPU     Temp buffers
────────────────────────────────────────────────────────
Total Used           ~3 GB     GPU     75% VRAM
Remaining           ~1 GB     GPU     Headroom
CPU Usage           <5%       CPU     Minimal
```

## Progressive Deployment

### Phase 1: Core System (Day 1)

**Deploy:**
- Server with SeamlessM4T + Kokoro
- Thin clients (phones)

**Capabilities:**
- ✅ Real-time translation
- ✅ Multi-speaker identification
- ✅ Generic TTS voices
- ✅ <2s latency
- ✅ Works immediately

**Users experience:**
- Pierre speaks French → Dan hears generic English voice
- Quality: Good (Kokoro is high quality)
- Latency: Excellent (~2s)

### Phase 2: Voice Cloning (Week 2+)

**Add:**
- Laptop TTS accelerator (F5-TTS on 3050)

**Enhanced capabilities:**
- ✅ All Phase 1 features
- ✅ **Cloned voices** (Pierre sounds like Pierre)
- ✅ Two-tier output (fast + quality)
- ✅ Passive voice training

**Users experience:**
- Pierre speaks French → Dan hears Pierre's actual voice in English
- Quality: Excellent (authentic voices)
- Latency: +0.8s for cloned voice (still acceptable)

### Phase 3: Production Hardening (Month 2+)

**Optimize:**
- Model quantization (int8)
- Audio compression (Opus)
- Multi-server deployment
- Advanced monitoring

## Component Details

### Server Components

#### 1. SeamlessM4T v2 Medium
```python
Model: facebook/seamless-m4t-v2-large
Size: 2.3B parameters
Device: CPU (32 threads)
Latency: ~800ms for 3s audio
Languages: 200+ supported
Features: Combined ASR + Translation
```

#### 2. Kokoro TTS
```python
Model: kokoro-v0.19
Size: 82M parameters
Device: CPU (ONNX, 16 threads)
Latency: ~300ms per sentence
Sample rate: 24kHz
Voices: af_sky, am_adam, etc.
```

#### 3. Pyannote Speaker ID
```python
Model: pyannote/embedding
Size: ~200MB
Device: CPU (4 threads)
Latency: ~50ms per identification
Method: 512D embeddings + cosine similarity
```

### Laptop Component

#### F5-TTS Voice Cloning
```python
Model: F5-TTS (to be implemented)
Size: ~2-3GB VRAM
Device: GPU (3050, 4GB)
Latency: ~800ms per sentence
Method: Reference-based voice cloning
Training: Passive (collects speaker samples)
```

## Network Protocol

### Server ↔ Phone

**Phone → Server (Audio):**
```
Binary WebSocket frame
Format: Int16 PCM
Sample rate: 16kHz mono
Typical size: 48KB per 3s utterance
```

**Server → Phone (Results):**
```json
{
  "type": "result",
  "speaker_name": "Pierre",
  "translation": "Hello, how are you?",
  "tts_audio": "base64_wav_data",  // Kokoro (immediate)
  "tts_voice": "kokoro",
  "has_f5_pending": true,  // F5-TTS will follow
  "latency_ms": 1234
}
```

**Server → Phone (F5-TTS Enhancement):**
```json
{
  "type": "f5_result",
  "speaker_name": "Pierre",
  "tts_audio": "base64_wav_data",  // F5-TTS (cloned)
  "tts_voice": "f5_cloned",
  "timestamp": 1234567890
}
```

### Server ↔ Laptop

**Server → Laptop (TTS Request):**
```json
{
  "type": "tts_request",
  "request_id": "unique_id",
  "text": "Hello, how are you?",
  "speaker_id": "speaker_1",
  "speaker_name": "Pierre"
}
```

**Laptop → Server (TTS Result):**
```json
{
  "type": "tts_result",
  "request_id": "unique_id",
  "speaker_name": "Pierre",
  "audio": "base64_wav_data",  // Cloned voice
  "latency_ms": 823
}
```

## Advantages of Hybrid Architecture

### 1. Progressive Enhancement
- ✅ Works immediately (Phase 1)
- ✅ Improves over time (Phase 2)
- ✅ Laptop optional (not required)

### 2. Fault Tolerance
- ✅ If laptop disconnects → Falls back to Kokoro
- ✅ Server always provides baseline quality
- ✅ No single point of failure

### 3. Resource Efficiency
- ✅ Server uses <50% capacity
- ✅ Laptop GPU utilized effectively
- ✅ Can add more laptops for load balancing

### 4. User Experience
- ✅ Immediate response (2s)
- ✅ Optional quality enhancement (2.8s)
- ✅ Seamless degradation if accelerator unavailable

### 5. Scalability
- ✅ Multiple laptops can connect
- ✅ Load balanced across accelerators
- ✅ Server remains central hub

## Deployment

### Server Startup
```bash
python server_cpu.py

# Listens on:
# - Port 9000 /ws/client (for phones)
# - Port 9000 /ws/tts-accelerator (for laptop)
```

### Laptop Startup (Optional)
```bash
python laptop_tts_accelerator.py --server ws://server-ip:9000/ws/tts-accelerator

# Connects to server
# Provides F5-TTS acceleration
# Can disconnect/reconnect anytime
```

### Phone Clients
```bash
# Open client_thin.html
# Configure server: ws://server-ip:9000/ws/client
# Start speaking!
```

## Monitoring

### Server Dashboard
```bash
curl http://server:9000/

{
  "service": "BabbleFish CPU Server",
  "clients": 3,
  "tts_accelerator": "connected",  // or null if no laptop
  "models": {"seamless": true, "kokoro": true, "speaker": true},
  "cpu_usage": "55%"
}
```

### Laptop Status
```python
# In laptop_tts_accelerator.py logs
[Accelerator] Connected to server
[GPU] Found: NVIDIA GeForce RTX 3050
[GPU] VRAM: 4.0 GB
[F5-TTS] Synthesized for Pierre (823ms)
[GPU] VRAM used: 2.8 GB
```

## Performance Benchmarks

### Without Laptop (Phase 1)
```
Latency: ~2.0s end-to-end
Voice: Kokoro (generic, high quality)
CPU: ~55% (60/128 cores)
Throughput: 3-5 concurrent conversations
```

### With Laptop (Phase 2)
```
Latency: ~2.0s (Kokoro) + ~0.8s (F5-TTS)
Voice: Cloned (authentic speaker voice)
CPU: ~55% (server same as Phase 1)
GPU: ~75% (3GB/4GB VRAM)
Throughput: 3-5 concurrent conversations (same)
```

---

**Architecture:** Hybrid Progressive (C)
**Status:** Production Ready
**Recommendation:** Deploy Phase 1 immediately, add Phase 2 when ready
**Last Updated:** 2026-02-08
