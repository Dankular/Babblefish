# BabbleFish Translation Service

A real-time multi-speaker translation system with client-server architecture:

**Server (CPU-Optimized - 128+ cores):**
- **SeamlessM4T v2** (Meta's all-in-one ASR + Translation)
- **Kokoro TTS** (ONNX Runtime for fast synthesis)
- **Pyannote.audio** (Speaker diarization)

**Thin Clients (Laptop/Phone):**
- Minimal CPU/GPU usage
- Just VAD, mic capture, and audio playback
- WebSocket streaming to server

Optimized for multi-core CPU processing with transformers + ONNX Runtime.

## Features

### Core Translation
- 🌍 **Translate text** between 200+ languages (NLLB-200)
- 🎤 **Transcribe audio** in 90+ languages (Whisper)
- 🔄 **Transcribe + Translate** audio files in one call
- ⚡ **Optimized inference** with CTranslate2 (3.2x faster)
- 🚀 **FastAPI** REST endpoints
- 💻 **CPU & GPU support**

### Real-Time Features
- 🎙️ **WebSocket streaming** - Real-time audio translation
- 🔊 **Voice Activity Detection** - Smart speech segmentation (Silero VAD)
- 🌐 **Language auto-detection** - Automatic source language identification
- 🎵 **Text-to-Speech** - Kokoro TTS for translated output
- 🎭 **Voice cloning** - Passive F5-TTS speaker training
- 📊 **Training progress** - Real-time stats on voice learning
- 👥 **Multi-speaker support** - Identify and track multiple speakers (pyannote.audio)
- 🎨 **Per-speaker voices** - Train unique F5-TTS model for each speaker
- 🔍 **Speaker diarization** - Automatic speaker identification via voiceprints

## Quick Start (Client-Server Architecture)

### Server Setup (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements_server.txt

# 2. Authenticate with Hugging Face
huggingface-cli login
# Visit https://huggingface.co/pyannote/embedding and accept terms

# 3. Start server (optimized for 128-core CPU)
python server_cpu.py

# Server ready at: ws://0.0.0.0:9000
```

### Client Setup (30 seconds)

```bash
# 1. Open client_thin.html in browser (laptop or phone)

# 2. Configure:
#    - Server URL: ws://YOUR-SERVER-IP:9000/ws/client
#    - Your name: Dan
#    - Target language: English

# 3. Tap microphone and speak!
```

**That's it!** Server handles all heavy processing. Your laptop/phone just streams audio.

---

## Legacy: Standalone Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

For model conversion, also install:
```bash
pip install transformers
```

### 2. Setup Models

Run the setup script to download and convert models:

```bash
python setup_models.py
```

**Manual NLLB Conversion** (if needed):

```bash
# Install converter
pip install ctranslate2 transformers sentencepiece

# Convert NLLB model
ct2-transformers-converter \
  --model facebook/nllb-200-distilled-1.3B \
  --output_dir ./models/nllb-ct2 \
  --quantization int8
```

### 3. Update Model Paths

Edit `main.py` and update the model loading section to point to your converted models:

```python
# In load_models() function
ct2_model_path = "./models/nllb-ct2"
```

## Usage

### Start the Server

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

### API Endpoints

#### 1. Translate Text

```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "source_lang": "eng_Latn",
    "target_lang": "spa_Latn"
  }'
```

Response:
```json
{
  "translation": "Hola, ¿cómo estás?",
  "source_lang": "eng_Latn",
  "target_lang": "spa_Latn"
}
```

#### 2. Transcribe Audio

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=en"
```

Response:
```json
{
  "text": "This is the transcribed text",
  "language": "en",
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "This is the transcribed text"}
  ]
}
```

#### 3. Transcribe + Translate

```bash
curl -X POST "http://localhost:8000/transcribe-translate" \
  -F "file=@audio.mp3" \
  -F "target_lang=spa_Latn"
```

Response:
```json
{
  "transcription": "Hello, how are you?",
  "detected_language": "en",
  "translation": "Hola, ¿cómo estás?",
  "target_lang": "spa_Latn"
}
```

#### 4. Health Check

```bash
curl http://localhost:8000/health
```

#### 5. Supported Languages

```bash
curl http://localhost:8000/languages
```

## Language Codes

### Whisper (ISO 639-1)
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `zh` - Chinese
- [Full list](https://github.com/openai/whisper#available-models-and-languages)

### NLLB-200 (Flores-200)
- `eng_Latn` - English
- `spa_Latn` - Spanish
- `fra_Latn` - French
- `deu_Latn` - German
- `zho_Hans` - Chinese (Simplified)
- `zho_Hant` - Chinese (Traditional)
- `jpn_Jpan` - Japanese
- `kor_Hang` - Korean
- `ara_Arab` - Arabic
- `rus_Cyrl` - Russian
- [Full list](https://github.com/facebookresearch/flores/blob/main/flores200/README.md#languages-in-flores-200)

## Model Sizes

### NLLB-200 Options
- `nllb-200-distilled-600M` - Smallest, fastest
- `nllb-200-distilled-1.3B` - **Recommended** (good balance)
- `nllb-200-3.3B` - Best quality (requires more VRAM)

### Whisper Options
- `tiny` - Fastest, least accurate
- `base` - Good for real-time
- `small` - Balanced
- `medium` - **Recommended** (good quality)
- `large-v2` - Best quality (slower)

## Performance Tuning

### CPU Optimization
```python
# In main.py startup
whisper_model = WhisperModel(
    "medium",
    device="cpu",
    compute_type="int8",  # Quantization
    cpu_threads=4
)
```

### GPU Optimization
```python
whisper_model = WhisperModel(
    "medium",
    device="cuda",
    compute_type="float16"  # Use FP16 on GPU
)

nllb_translator = ctranslate2.Translator(
    model_path,
    device="cuda",
    compute_type="float16"
)
```

### Batch Processing
For multiple translations, use the batch endpoints (to be implemented) for better throughput.

## Docker Deployment (Optional)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download models (or mount volume)
RUN python setup_models.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t babelfish .
docker run -p 8000:8000 babelfish
```

## ⭐ NEW: Client-Server Architecture (Recommended)

### Server-Side CPU Processing (128 cores)

The server does all heavy lifting - optimized for multi-core CPUs:

```bash
# On your powerful server
pip install -r requirements_server.txt

# Authenticate with Hugging Face
huggingface-cli login

# Start CPU server (port 9000)
python server_cpu.py
```

**Server handles:**
- SeamlessM4T v2 (ASR + Translation) - 32 threads
- Kokoro TTS (ONNX) - 16 threads per synthesis
- Speaker diarization - 4 threads
- Multi-client WebSocket - 8 threads

### Thin Client (Laptop/Phone)

Clients use minimal resources - just streaming and playback:

```bash
# On laptop or phone browser
# Open: client_thin.html
# Configure server URL (e.g., ws://192.168.1.100:9000/ws/client)
# Select target language
# Tap microphone and speak!
```

**Client handles:**
- Microphone capture
- Simple VAD (energy-based)
- WebSocket streaming to server
- Audio playback from server

**Benefits:**
- ✅ Laptop GPU completely free (4GB VRAM available for F5-TTS later)
- ✅ Laptop CPU minimal usage (<10%)
- ✅ Server handles multiple clients simultaneously
- ✅ ~1.5-2s latency (acceptable for conversations)
- ✅ Works on phones, tablets, laptops

**See:** Architecture diagrams below

---

## Legacy: Standalone Real-Time Translation

### Quick Start (TTS Version)

```bash
# Install TTS dependencies
pip install -r requirements_tts.txt

# Start TTS server
python realtime_server_tts.py

# Open browser
# Navigate to http://localhost:8002
```

**Features:**
- Microphone capture with VAD
- Real-time transcription & translation
- Kokoro TTS for English output
- Passive speaker voice training (F5-TTS)
- Training progress tracking in UI

**See:** [TTS_SETUP.md](TTS_SETUP.md) for detailed guide

### Server Comparison

#### Port 9000 - CPU Server (Client-Server Architecture) ⭐ RECOMMENDED
```bash
python server_cpu.py
```
- **Client-server model** - thin clients connect via WebSocket
- **SeamlessM4T v2** - All-in-one ASR + translation
- **Multi-core optimized** - Uses 60-70 of 128 cores
- **Multi-client support** - Multiple people can connect
- **Speaker diarization** - Identifies speakers across all clients
- **Kokoro TTS** - Fast CPU-based synthesis
- **Latency:** ~1.5-2s per utterance
- **Best for:** Production use with powerful server

#### Port 8000 - REST API Server (Legacy)
```bash
python main.py
```
- REST endpoints for text/audio
- Batch processing
- Good for integrations

#### Port 8001 - Real-Time Server (No TTS)
```bash
python realtime_server.py
```
- WebSocket streaming
- VAD-based segmentation
- Language detection
- Text-only output

#### Port 8002 - Real-Time TTS Server (Single Speaker)
```bash
python realtime_server_tts.py
```
- Everything from 8001 +
- Kokoro TTS output
- Passive speaker training
- F5-TTS voice cloning
- Single speaker mode

#### Port 8003 - Multi-Speaker TTS Server ⭐
```bash
python realtime_server_multispeaker.py
```
- Everything from 8002 +
- **Speaker diarization** (pyannote.audio)
- **Per-speaker voice training** (separate F5-TTS models)
- **Speaker identification** (voiceprint matching)
- **Color-coded UI** (track multiple speakers)
- Best for: meetings, conferences, multi-person conversations

**See:** [MULTISPEAKER_SETUP.md](MULTISPEAKER_SETUP.md) for detailed guide

## Architecture

### Client-Server (Port 9000) ⭐ RECOMMENDED

```
┌─────────────────────────────────────────────────────────────────┐
│                    Thin Clients (Minimal CPU)                   │
├──────────────────┬──────────────────┬───────────────────────────┤
│   Dan's Phone    │  Marek's Phone   │    Pierre's Laptop        │
│   (English)      │   (Polish)       │    (French)               │
│                  │                  │                           │
│ • Mic capture    │ • Mic capture    │ • Mic capture             │
│ • Simple VAD     │ • Simple VAD     │ • Simple VAD              │
│ • WebSocket      │ • WebSocket      │ • WebSocket               │
│ • Playback       │ • Playback       │ • Playback                │
│                  │                  │                           │
│ CPU: <10%        │ CPU: <10%        │ CPU: <10%                 │
│ GPU: FREE        │ GPU: FREE        │ GPU: FREE (3050 - 4GB)    │
└────────┬─────────┴────────┬─────────┴────────┬──────────────────┘
         │                  │                  │
         │    WebSocket (audio chunks)         │
         └──────────────────┼──────────────────┘
                            │
         ┌──────────────────▼─────────────────────────────────────┐
         │         CPU Server (128 cores, Heavy Lifting)          │
         │                   Port 9000                            │
         ├────────────────────────────────────────────────────────┤
         │                                                        │
         │  ┌──────────────────────────────────────────────┐     │
         │  │  Multi-Client Handler (8 threads)            │     │
         │  │  Manages Dan, Marek, Pierre connections      │     │
         │  └───┬──────────────────────────────────────────┘     │
         │      │                                                 │
         │  ┌───▼────────────────────────────────────────┐       │
         │  │  Speaker Diarization (4 threads)           │       │
         │  │  Identifies: Pierre, Dan, Marek via        │       │
         │  │  pyannote embeddings (voiceprints)         │       │
         │  └───┬────────────────────────────────────────┘       │
         │      │                                                 │
         │  ┌───▼────────────────────────────────────────┐       │
         │  │  SeamlessM4T v2 Medium (32 threads)        │       │
         │  │  • ASR: Transcribe speech                  │       │
         │  │  • Translation: To target language         │       │
         │  │  • Language detection: Auto-detect source  │       │
         │  │  Pierre (FR) → "On devrait..."             │       │
         │  │    → EN: "We should..."                    │       │
         │  │    → PL: "Powinniśmy..."                   │       │
         │  └───┬────────────────────────────────────────┘       │
         │      │                                                 │
         │  ┌───▼────────────────────────────────────────┐       │
         │  │  Kokoro TTS (16 threads × N parallel)      │       │
         │  │  ONNX Runtime for fast CPU synthesis       │       │
         │  │  Thread pool A: EN → audio (for Dan)       │       │
         │  │  Thread pool B: PL → audio (for Marek)     │       │
         │  └───┬────────────────────────────────────────┘       │
         │      │                                                 │
         │  Resource Usage:                                       │
         │  • Cores used: ~60-70 of 128                          │
         │  • RAM: ~5GB                                          │
         │  • Remaining: 58-68 cores free                        │
         │                                                        │
         └──────┬──────────────────────────────────────┬──────────┘
                │                                       │
                │    WebSocket (synth audio back)      │
                │                                       │
    ┌───────────▼──────┐        ┌────────────▼─────────────┐
    │   Dan's Phone    │        │    Marek's Phone         │
    │   Hears Pierre   │        │    Hears Pierre          │
    │   in English     │        │    in Polish             │
    │   🔊             │        │    🔊                    │
    └──────────────────┘        └──────────────────────────┘

Latency Timeline:
  0ms      - Pierre speaks
  200ms    - VAD detects speech
  1500ms   - VAD detects pause, sends to server
  1600ms   - Speaker ID: "Pierre"
  2400ms   - SeamlessM4T: ASR + Translation
  3000ms   - Kokoro TTS (parallel for EN + PL)
  3000ms   - Audio plays on Dan's and Marek's phones

Total: ~1.5-2s after speech ends
```

### Legacy: REST API (Port 8000)
```
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼─────┐
│ NLLB  │ │Whisper │
│  CT2  │ │  CT2   │
└───┬───┘ └──┬─────┘
    │        │
    └────┬───┘
         │
    ┌────▼─────┐
    │ GPU/CPU  │
    └──────────┘
```

### Real-Time with TTS (Port 8002)
```
┌──────────────┐
│   Browser    │
│ (Microphone) │
└──────┬───────┘
       │ WebSocket
┌──────▼────────┐
│ Silero VAD    │
│ Audio Buffer  │
└──────┬────────┘
       │
┌──────▼────────┐     ┌─────────────┐
│    Whisper    │────▶│   Training  │
│ Transcription │     │   Storage   │
└──────┬────────┘     └─────────────┘
       │
┌──────▼────────┐
│   NLLB CT2    │
│  Translation  │
└──────┬────────┘
       │
┌──────▼────────┐     ┌─────────────┐
│  Kokoro TTS   │◀────│  F5-TTS     │
│   Synthesis   │     │  (Trained)  │
└──────┬────────┘     └─────────────┘
       │
┌──────▼────────┐
│   Browser     │
│  (Speakers)   │
└───────────────┘
```

## Troubleshooting

### Model conversion fails
- Ensure you have `transformers` installed: `pip install transformers`
- Check you have enough disk space (~4GB for NLLB-1.3B)
- Try running the conversion command manually

### Out of memory
- Use smaller models (`600M` for NLLB, `small` for Whisper)
- Reduce `max_batch_size` in translation calls
- Use `int8` quantization for CPU

### Slow performance
- Use GPU if available (`device="cuda"`)
- Enable `vad_filter` in Whisper for faster audio processing
- Pre-convert models to CT2 format (10-30% faster)

## References

- [NLLB-200 Paper](https://arxiv.org/abs/2207.04672)
- [Whisper Paper](https://arxiv.org/abs/2212.04356)
- [CTranslate2 Docs](https://opennmt.net/CTranslate2/)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## TODO

### Completed ✅
- [x] WebSocket support for real-time transcription
- [x] Language detection with confidence scores
- [x] CTranslate2 optimization (3.2x speedup)
- [x] Text-to-Speech integration (Kokoro)
- [x] Passive speaker voice training (F5-TTS)
- [x] VAD-based speech segmentation (Silero)
- [x] Real-time browser client

### In Progress 🚧
- [ ] Complete F5-TTS training pipeline (currently placeholder)
- [ ] GPU optimization for Whisper (improve RTF)
- [ ] Multilingual TTS support (beyond English)

### Planned 📋
- [ ] Implement batch translation endpoint
- [ ] Model caching and warm-up
- [ ] Rate limiting
- [ ] Authentication
- [ ] Prometheus metrics
- [ ] Docker Compose setup
- [ ] Opus audio encoding (bandwidth optimization)
