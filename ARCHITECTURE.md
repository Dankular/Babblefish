# BabbleFish Architecture Documentation

## System Overview

BabbleFish is a distributed real-time translation system with a client-server architecture optimized for multi-core CPU processing.

```
┌──────────────────────────────────────────────────────────────────┐
│                         System Overview                          │
├────────────────────────┬─────────────────────────────────────────┤
│   Thin Clients         │        CPU Server (128 cores)           │
│   (Phones/Laptops)     │                                         │
│                        │                                         │
│ • Mic capture          │ • SeamlessM4T v2 (ASR + Translation)    │
│ • Simple VAD           │ • Kokoro TTS (ONNX synthesis)           │
│ • WebSocket stream     │ • Pyannote (speaker diarization)        │
│ • Audio playback       │ • Multi-client handler                  │
│                        │                                         │
│ CPU: <10%              │ CPU: ~50-60% (60-70 of 128 cores)       │
│ GPU: FREE              │ GPU: Not needed                         │
│ RAM: <100MB            │ RAM: ~5-6GB                             │
└────────────────────────┴─────────────────────────────────────────┘
```

## Component Architecture

### 1. CPU Server (Port 9000)

#### 1.1 Multi-Client Handler
**Responsibility:** Manage WebSocket connections, route messages

```python
class MultiClientHandler:
    clients: Dict[str, ClientInfo]  # client_id -> connection info

    async def handle_client(websocket, client_id, target_lang, name):
        # Register client
        # Receive audio chunks
        # Process utterances
        # Send results back
        # Broadcast to other clients
```

**Thread allocation:** 8 threads
**Memory:** ~100MB
**Concurrency:** Handles N clients simultaneously

#### 1.2 Speaker Diarization
**Responsibility:** Identify speakers via voiceprint matching

```python
class SpeakerDiarizationServer:
    embedding_model: pyannote.Inference
    known_speakers: Dict[str, np.ndarray]  # speaker_id -> embedding

    def identify_speaker(audio) -> (speaker_id, name, confidence):
        # Extract 512D embedding
        # Compare with known speakers (cosine similarity)
        # If similarity > 0.75: match
        # If similarity < 0.75: new speaker
        # Update running average
```

**Thread allocation:** 4 threads
**Memory:** ~200MB
**Latency:** ~50ms per identification

**Algorithm:**
1. Extract embedding: `audio → pyannote → 512D vector`
2. Normalize: `embedding / ||embedding||`
3. Compare: `similarity = dot(new, known) / (||new|| * ||known||)`
4. Match: `similarity > 0.75 → same speaker`
5. Update: `avg = 0.9 * old + 0.1 * new` (running average)

#### 1.3 SeamlessM4T v2 Processor
**Responsibility:** ASR + Translation in single model

```python
class SeamlessM4TProcessor:
    model: SeamlessM4Tv2Model
    processor: AutoProcessor

    def process_audio(audio_path, target_lang) -> result:
        # Load audio (librosa, 16kHz mono)
        # Process with model
        # Generate transcription + translation
        # Return source text + translation
```

**Thread allocation:** 32 threads (torch.set_num_threads)
**Memory:** ~3-4GB
**Latency:** ~800ms for 3s audio

**Model details:**
- Size: 2.3B parameters (medium)
- Quantization: float32 (CPU optimal)
- Languages: 200+ supported
- Combined ASR + MT pipeline

#### 1.4 Kokoro TTS Server
**Responsibility:** Fast speech synthesis

```python
class KokoroTTSServer:
    model: kokoro_onnx.Kokoro
    num_threads: 16

    def synthesize(text, voice, speed) -> audio:
        # ONNX Runtime synthesis
        # Return 24kHz float32 audio
```

**Thread allocation:** 16 threads per synthesis (parallel for multiple languages)
**Memory:** ~500MB
**Latency:** ~300ms per sentence
**Sample rate:** 24kHz

**Optimization:**
- ONNX Runtime for CPU
- Multi-threaded inference
- Parallel synthesis for multiple target languages
- Voice options: af_sky, am_adam, etc.

### 2. Thin Client (Browser/Phone)

#### 2.1 Microphone Capture
```javascript
// Request 16kHz mono audio
navigator.mediaDevices.getUserMedia({
    audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
    }
})
```

#### 2.2 Simple VAD (Voice Activity Detection)
```javascript
// Energy-based speech detection
function isVoice(audioData) {
    energy = sqrt(sum(sample^2) / N)
    return energy > 0.01  // threshold
}

// Buffer speech until silence
if (isVoice) {
    buffer.push(audioData)
    clearTimeout(silenceTimer)
} else if (buffer.length > 0) {
    silenceTimer = setTimeout(() => {
        sendToServer(buffer)
        buffer = []
    }, 500)  // 500ms silence
}
```

#### 2.3 WebSocket Communication
```javascript
// Connect to server
ws = new WebSocket('ws://server:9000/ws/client?client_id=dan&target_lang=eng&name=Dan')

// Send audio
ws.send(int16AudioBuffer)

// Receive results
ws.onmessage = (event) => {
    result = JSON.parse(event.data)
    displayMessage(result)
    playAudio(result.tts_audio)  // base64 encoded WAV
}
```

## Data Flow

### Complete Utterance Pipeline

```
Client Side:
┌─────────────────────────────────────────────────────┐
│ 1. Microphone captures audio (16kHz mono)          │
│    Time: 0ms                                        │
├─────────────────────────────────────────────────────┤
│ 2. Simple VAD detects speech                       │
│    Time: 200ms                                      │
│    Energy threshold: 0.01                           │
├─────────────────────────────────────────────────────┤
│ 3. Buffer audio chunks                             │
│    Time: 200ms - 1500ms                            │
│    Typical utterance: 1-3 seconds                  │
├─────────────────────────────────────────────────────┤
│ 4. VAD detects 500ms silence → send to server     │
│    Time: 1500ms                                     │
│    WebSocket.send(int16_audio_buffer)              │
└─────────────────────────────────────────────────────┘
                            │
                            │ WebSocket (audio chunk)
                            ▼
Server Side:
┌─────────────────────────────────────────────────────┐
│ 5. Receive audio chunk                             │
│    Time: 1550ms                                     │
│    Size: ~48KB for 3s audio                        │
├─────────────────────────────────────────────────────┤
│ 6. Speaker identification (pyannote)               │
│    Time: 1600ms (+50ms)                            │
│    Extract 512D embedding                          │
│    Match against known speakers                    │
│    Result: "Pierre" (speaker_1, conf: 0.95)       │
├─────────────────────────────────────────────────────┤
│ 7. Save temp audio file (WAV)                      │
│    Time: 1610ms (+10ms)                            │
│    Format: 16kHz mono PCM                          │
├─────────────────────────────────────────────────────┤
│ 8. SeamlessM4T processing                          │
│    Time: 1610ms - 2400ms (+790ms)                  │
│    a. Load audio with librosa                      │
│    b. Process with model (32 threads)              │
│    c. ASR: "On devrait vérifier la proposition"    │
│    d. Detect language: French                      │
│    e. Translate to target (e.g., English)          │
│    f. Result: "We should check the proposal"       │
├─────────────────────────────────────────────────────┤
│ 9. Kokoro TTS synthesis                            │
│    Time: 2400ms - 2700ms (+300ms)                  │
│    Parallel for multiple target languages:         │
│    • Thread pool A: English → WAV (for Dan)        │
│    • Thread pool B: Polish → WAV (for Marek)       │
│    ONNX Runtime, 16 threads each                   │
├─────────────────────────────────────────────────────┤
│ 10. Encode audio to base64                         │
│     Time: 2720ms (+20ms)                           │
│     WAV format, base64 string                      │
├─────────────────────────────────────────────────────┤
│ 11. Send results via WebSocket                     │
│     Time: 2750ms (+30ms)                           │
│     JSON: {                                        │
│       type: "result",                              │
│       speaker_name: "Pierre",                      │
│       source_text: "On devrait...",                │
│       translation: "We should...",                 │
│       tts_audio: "base64_encoded_wav",             │
│       latency_ms: 1200                             │
│     }                                              │
└─────────────────────────────────────────────────────┘
                            │
                            │ WebSocket (result JSON)
                            ▼
Client Side:
┌─────────────────────────────────────────────────────┐
│ 12. Receive result                                  │
│     Time: 2800ms                                    │
├─────────────────────────────────────────────────────┤
│ 13. Display message in UI                          │
│     Time: 2810ms (+10ms)                           │
│     Show: Pierre said "We should check..."         │
├─────────────────────────────────────────────────────┤
│ 14. Decode base64 → audio buffer                   │
│     Time: 2820ms (+10ms)                           │
├─────────────────────────────────────────────────────┤
│ 15. Play audio through speakers                    │
│     Time: 2830ms (+10ms)                           │
│     Web Audio API                                  │
└─────────────────────────────────────────────────────┘

Total Latency: ~2.8s from end of speech to playback start
Server Processing: ~1.2s (speaker ID + ASR/MT + TTS)
```

## Resource Allocation (128-core Server)

### Thread Distribution

```
Component                 Threads    % of 128    Typical Load
─────────────────────────────────────────────────────────────
SeamlessM4T (torch)         32        25%         Active during ASR/MT
Kokoro TTS (ONNX)          16×2       25%         Active during synthesis
Speaker embedding           4         3%          Active during ID
WebSocket handler           8         6%          Always active
System/Other               68        53%         Available/Idle

Peak Usage:                70        55%         When processing utterance
Idle Usage:                12         9%         Between utterances
```

### Memory Distribution

```
Component               RAM        Notes
──────────────────────────────────────────────────────
SeamlessM4T model      3-4 GB     Loaded once, shared
Kokoro TTS             500 MB     ONNX model
Pyannote embeddings    200 MB     Model + known speakers
WebSocket server       100 MB     Per-client overhead
Audio buffers           50 MB     Temporary storage
System overhead        500 MB     Python, libraries

Total Peak:           ~5-6 GB
Total Idle:           ~4-5 GB
```

## Network Protocol

### WebSocket Message Format

#### Client → Server (Audio Chunk)

```
Binary message:
┌────────────────────────┐
│ Int16 PCM audio data   │
│ 16kHz mono             │
│ Length: variable       │
│ Typical: 48000 samples │
│ (3 seconds × 16000 Hz) │
└────────────────────────┘

Size: ~96KB per 3-second utterance
```

#### Server → Client (Result)

```json
{
  "type": "result",
  "speaker_id": "speaker_1",
  "speaker_name": "Pierre",
  "speaker_confidence": 0.953,
  "source_text": "On devrait vérifier la proposition",
  "source_lang": "fra",
  "translation": "We should check the proposal",
  "target_lang": "eng",
  "tts_audio": "UklGRi4gAABXQVZFZm10IBAA...",  // base64 WAV
  "latency_ms": 1234.56,
  "timestamp": 1707393600.123
}
```

Size: ~50-100KB (mostly base64 audio)

### Connection Lifecycle

```
1. Client connects:
   ws://server:9000/ws/client?client_id=dan&target_lang=eng&name=Dan

2. Server accepts:
   WebSocket handshake → upgrade to WS

3. Server sends ready:
   {
     "type": "ready",
     "message": "Server ready (32 threads)",
     "client_id": "dan",
     "target_lang": "eng"
   }

4. Client streams audio:
   [binary chunks] → server processes → [JSON results]

5. Client disconnects:
   WebSocket close → server removes from clients dict
```

## Scalability Analysis

### Single Server Capacity

**Assumptions:**
- 128 cores available
- Each utterance uses ~70 cores for ~1.2s
- Utterances can overlap if different speakers

**Sequential processing:**
- Capacity: 60 / 1.2 = 50 utterances/minute

**Parallel processing (multiple clients speaking):**
- If 2 clients speak simultaneously: 128 cores / 70 = 1.8× capacity
- Practical limit: 2-3 simultaneous utterances
- 10 connected clients: ~100-150 utterances/minute total

### Bottlenecks

1. **CPU (SeamlessM4T):** 32 cores per inference
   - Solution: Queue utterances, process sequentially

2. **Memory (model loading):** ~4GB per model
   - Solution: Share single model instance across all clients

3. **Network bandwidth:** ~150KB per utterance (in + out)
   - Solution: Opus encoding (future), reduce to ~30KB

4. **TTS synthesis:** 16 cores × N languages
   - Solution: Parallel thread pools, cache common phrases

## Security Considerations

### Current Implementation (Local Network)

- No authentication
- No encryption
- Trust all clients
- LAN-only deployment

### Future Production Hardening

1. **Authentication:**
   - Client tokens in WebSocket URL
   - Server validates against known clients

2. **Encryption:**
   - WSS (WebSocket Secure) with TLS
   - Self-signed certs for LAN

3. **Rate limiting:**
   - Max 10 utterances/minute per client
   - Max 3 concurrent clients

4. **Input validation:**
   - Max audio length: 10 seconds
   - Audio format validation
   - Reject malformed data

## Performance Optimization

### Current Optimizations

1. **Torch thread allocation:**
   ```python
   torch.set_num_threads(32)
   os.environ["OMP_NUM_THREADS"] = "32"
   ```

2. **ONNX Runtime for TTS:**
   - CPU-optimized operators
   - Multi-threaded inference

3. **Running average for speaker embeddings:**
   - Reduces computation
   - Improves accuracy over time

4. **Base64 audio encoding:**
   - Simplifies WebSocket transmission
   - Browser-friendly

### Future Optimizations

1. **Quantization:**
   - SeamlessM4T int8 (if supported)
   - 2-3× speedup, minimal quality loss

2. **Model caching:**
   - Pre-load models on startup
   - Warm-up inference

3. **Audio compression:**
   - Opus codec for WebSocket
   - 10× bandwidth reduction

4. **Batch processing:**
   - Group multiple utterances
   - Process in single batch

## Monitoring & Debugging

### Health Checks

```bash
# Server status
curl http://server:9000/

# Response:
{
  "service": "BabbleFish CPU Server",
  "status": "running",
  "models": {
    "seamless": true,
    "tts": true,
    "speaker": true
  },
  "cpu_threads": 32,
  "clients": 3
}
```

### Known Speakers

```bash
curl http://server:9000/speakers

# Response:
{
  "speakers": {
    "speaker_1": {
      "id": "speaker_1",
      "name": "Pierre",
      "first_seen": 1707393600.0,
      "samples": 42
    }
  },
  "count": 1
}
```

### Server Logs

```python
[Client] Dan connected (target: eng)
[Speaker] New: Pierre (speaker_1)
[Processing] Pierre: 1234ms (fra → eng)
[TTS] Synthesized 28 chars in 315ms
[Client] Marek disconnected
```

### Client Console

```javascript
console.log('Connected to server');
console.log('Sent 48000 samples (3.00s)');
console.log('Received result: latency 1234ms');
```

## Disaster Recovery

### Server Crashes

- **Symptom:** Clients get WebSocket close event
- **Recovery:** Auto-restart server with systemd
- **Data loss:** In-flight utterances lost, speaker data persisted

### Client Disconnects

- **Detection:** WebSocket onclose event
- **Action:** Server removes from clients dict
- **Reconnect:** Client must manually reconnect

### Model Loading Fails

- **Symptom:** Server startup fails
- **Check:** Hugging Face authentication, model downloads
- **Fallback:** Disable failing component, continue with remaining

---

**Architecture Version:** 2.0
**Last Updated:** 2026-02-08
**Status:** Production-ready for local network deployment
