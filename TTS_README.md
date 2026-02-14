# BabbleFish TTS Server V2

Complete TTS pipeline with ASR, Translation, and Voice Cloning using XTTS-v2.

## Features

- 🎤 **ASR**: Automatic Speech Recognition using faster-whisper (supports all languages)
- 🌍 **Translation**: NLLB-200 translation between 200+ languages
- 🗣️ **TTS**: XTTS-v2 multilingual text-to-speech (24 languages)
- 🎭 **Voice Cloning**: Clone any voice from reference audio
- ⚡ **GPU Acceleration**: Optimized for 4GB VRAM with int8 quantization
- 🔄 **Full Pipeline**: Audio → ASR → Translation → TTS in one API call

## Installation

### 1. Install Dependencies

```bash
pip install -r server/requirements.txt
```

### 2. Configure Environment

Copy the example configuration:

```bash
cp server/.env.example server/.env
```

Edit `server/.env`:

```bash
# For GPU acceleration (recommended)
DEVICE=cuda
COMPUTE_TYPE=int8  # Optimal for 4GB VRAM

# For CPU only
DEVICE=cpu
COMPUTE_TYPE=int8
```

### 3. Download Models

Models are automatically downloaded on first use:
- **XTTS-v2**: ~2GB (HuggingFace)
- **faster-whisper**: ~1.5GB (medium model)
- **NLLB-200**: ~1.2GB (distilled-600M)

## Quick Start

### Start the Server

```bash
cd server
python tts_server.py
```

The server will start at `http://localhost:8000`

API Documentation: http://localhost:8000/docs

## API Endpoints

### 1. Check Status

```bash
GET /api/tts/status
```

Returns device info, supported languages, and voice profiles.

### 2. Text-to-Speech (TTS)

Synthesize speech from text with optional voice cloning:

```bash
POST /api/tts/synthesize
Content-Type: multipart/form-data

text: "Hello, how are you?"
language: "en"
voice_profile: "my_voice"  # optional
temperature: 0.7           # optional (0.1-1.0)
speed: 1.0                 # optional (0.5-2.0)
reference_audio: <file>    # optional WAV/MP3
```

**Example with curl:**

```bash
# Basic synthesis
curl -X POST "http://localhost:8000/api/tts/synthesize" \
  -F "text=Hello world" \
  -F "language=en" \
  -o output.wav

# With voice cloning
curl -X POST "http://localhost:8000/api/tts/synthesize" \
  -F "text=Bonjour le monde" \
  -F "language=fr" \
  -F "reference_audio=@my_voice.wav" \
  -o output_french.wav
```

### 3. Speech-to-Text (ASR)

Transcribe audio with language detection:

```bash
POST /api/tts/transcribe
Content-Type: multipart/form-data

audio_file: <file>  # WAV/MP3
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/tts/transcribe" \
  -F "audio_file=@recording.wav"
```

**Response:**

```json
{
  "text": "Hello, how are you?",
  "language": "en",
  "duration": 2.5
}
```

### 4. Translation

Translate text between languages:

```bash
POST /api/tts/translate
Content-Type: application/json

{
  "text": "Hello world",
  "source_lang": "en",
  "target_lang": "es"
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/tts/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "source_lang": "en",
    "target_lang": "es"
  }'
```

**Response:**

```json
{
  "original_text": "Hello world",
  "translated_text": "Hola mundo",
  "source_lang": "en",
  "target_lang": "es"
}
```

### 5. Full Pipeline

Complete pipeline: Audio → ASR → Translation → TTS

```bash
POST /api/tts/process
Content-Type: multipart/form-data

audio_file: <file>         # Input audio (any language)
target_language: "es"      # Target language for output
voice_profile: "my_voice"  # optional
temperature: 0.7           # optional
speed: 1.0                 # optional
```

**Example:**

```bash
# English audio → Spanish speech
curl -X POST "http://localhost:8000/api/tts/process" \
  -F "audio_file=@english_recording.wav" \
  -F "target_language=es" \
  -o spanish_output.wav
```

### 6. Voice Profile Management

#### Add Voice Profile

```bash
POST /api/tts/voice-profile/add
Content-Type: multipart/form-data

name: "john_voice"
description: "John's voice profile"  # optional
audio_file: <file>  # Reference audio (WAV/MP3)
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/tts/voice-profile/add" \
  -F "name=john_voice" \
  -F "description=John's voice" \
  -F "audio_file=@john_sample.wav"
```

#### List Voice Profiles

```bash
GET /api/tts/voice-profiles
```

### 7. Supported Languages

```bash
GET /api/tts/languages
```

Returns list of supported language codes.

## Supported Languages (24)

XTTS-v2 supports the following languages:

- **English** (en)
- **Spanish** (es)
- **French** (fr)
- **German** (de)
- **Italian** (it)
- **Portuguese** (pt)
- **Polish** (pl)
- **Turkish** (tr)
- **Russian** (ru)
- **Dutch** (nl)
- **Czech** (cs)
- **Arabic** (ar)
- **Chinese** (zh)
- **Japanese** (ja)
- **Korean** (ko)
- **Hindi** (hi)
- **Hungarian** (hu)
- **Swedish** (sv)
- **Finnish** (fi)
- **Danish** (da)
- **Norwegian** (no)
- **Hebrew** (he)
- **Greek** (el)
- **Slovak** (sk)

## Python Client Examples

### Basic TTS

```python
import requests

# Synthesize English speech
response = requests.post(
    "http://localhost:8000/api/tts/synthesize",
    files={
        "text": (None, "Hello, how are you?"),
        "language": (None, "en")
    }
)

with open("output.wav", "wb") as f:
    f.write(response.content)
```

### Voice Cloning

```python
import requests

# Synthesize with voice cloning
with open("reference_voice.wav", "rb") as ref:
    response = requests.post(
        "http://localhost:8000/api/tts/synthesize",
        files={
            "text": (None, "Bonjour le monde"),
            "language": (None, "fr"),
            "reference_audio": ref
        }
    )

with open("cloned_voice.wav", "wb") as f:
    f.write(response.content)
```

### Full Translation Pipeline

```python
import requests

# English audio → Spanish speech
with open("english_audio.wav", "rb") as audio:
    response = requests.post(
        "http://localhost:8000/api/tts/process",
        files={
            "audio_file": audio,
            "target_language": (None, "es")
        }
    )

# Check metadata in headers
print(f"Source: {response.headers.get('X-Source-Text')}")
print(f"Translated: {response.headers.get('X-Translated-Text')}")

with open("spanish_output.wav", "wb") as f:
    f.write(response.content)
```

## Performance Optimization

### GPU Configuration

For **4GB VRAM** (optimal):
```bash
DEVICE=cuda
COMPUTE_TYPE=int8
```

For **6GB+ VRAM** (better quality):
```bash
DEVICE=cuda
COMPUTE_TYPE=float16
```

### Model Selection

- **faster-whisper**: Use `medium` for best accuracy/speed balance
- **NLLB-200**: `distilled-600M` is optimal for speed
- **XTTS-v2**: Automatic GPU acceleration when available

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TTS Manager V2                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │    ASR     │  │ Translation  │  │      TTS      │  │
│  │  (Whisper) │→ │    (NLLB)    │→ │   (XTTS-v2)   │  │
│  └────────────┘  └──────────────┘  └───────────────┘  │
│       ↓                  ↓                  ↓          │
│   Audio→Text      Text→Translation    Text→Speech     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │          Voice Profile Manager                  │  │
│  │          (Reference Audio Storage)              │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Key Implementation Details

### NLLB Translation

- ✅ **Always use `transformers.AutoTokenizer`** (never SentencePiece directly)
- ✅ **Set `src_lang` parameter** for proper input tokenization
- ✅ **Skip first token** in translation output (it's the language tag)

```python
# Correct NLLB usage
tokenizer = transformers.AutoTokenizer.from_pretrained(
    model_path,
    src_lang=source_flores,  # CRITICAL!
    clean_up_tokenization_spaces=True
)

# Skip first token in output
translated_tokens = results[0].hypotheses[0][1:]  # Skip language tag
```

### GPU Acceleration

- **Device**: `DEVICE=cuda` for GPU, `cpu` for CPU
- **Compute Type**: `int8` optimal for 4GB VRAM
- **Auto-detection**: Falls back to CPU if CUDA unavailable

### Voice Cloning

XTTS-v2 uses reference audio for voice cloning:

1. **Reference audio**: 5-30 seconds of clear speech
2. **Format**: WAV/MP3, mono, 24kHz recommended
3. **Quality**: Higher quality reference = better cloning

## Troubleshooting

### Out of Memory (GPU)

Reduce compute type:
```bash
COMPUTE_TYPE=int8  # Use this for 4GB VRAM
```

### Slow Performance

1. Check GPU is being used:
   ```bash
   curl http://localhost:8000/api/tts/status
   ```

2. Verify CUDA installation:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

### Model Download Issues

Models are cached in:
- XTTS-v2: `models/xtts/`
- Whisper: Auto-downloaded by faster-whisper
- NLLB: `models/nllb-200-distilled-600M-ct2/`

## License

BabbleFish TTS Server - MIT License

Models used:
- XTTS-v2: Mozilla Public License 2.0
- faster-whisper: MIT License
- NLLB-200: CC-BY-NC 4.0
