# Babblefish Models

This directory contains the ML models used by the Babblefish server.

## Models

### 1. faster-whisper (medium, int8)

**Purpose**: Automatic Speech Recognition (ASR)
**Size**: ~1.5 GB RAM
**Download**: Auto-downloads on first use
**Location**: `~/.cache/huggingface/hub/`

**Model Details**:
- Based on OpenAI Whisper medium
- CTranslate2 optimized for CPU inference
- int8 quantization for smaller memory footprint
- Supports 99 languages with automatic detection

**Performance** (CPU):
- Transcription latency: ~500ms for 3-second audio
- Accuracy: High (word error rate ~3-5% for English)

### 2. NLLB-200-distilled-600M (int8)

**Purpose**: Neural Machine Translation
**Size**: ~1.2 GB RAM
**Download**: Manual (see below)
**Location**: `models/nllb-200-distilled-600M-ct2/`

**Model Details**:
- Meta AI's No Language Left Behind (NLLB)
- Supports 200 languages
- CTranslate2 optimized for CPU inference
- int8 quantization

**Performance** (CPU):
- Translation latency: ~300ms per language
- Quality: High (BLEU scores comparable to full model)

**Languages Supported**: See `server/pipeline/language.py` for complete list

### 3. SentencePiece Tokenizer

**Purpose**: Text tokenization for NLLB
**Size**: ~5 MB
**Download**: Included with NLLB model
**Location**: `models/nllb-200-distilled-600M-ct2/sentencepiece.model`

---

## Download Instructions

### Automatic Download

Run the download script:

```bash
cd models
python download_server_models.py
```

This will:
1. ✓ Auto-download faster-whisper medium (if not cached)
2. ⚠️  Provide instructions for NLLB download (requires manual conversion)

### Manual NLLB Download

If automatic download fails, follow these steps:

#### Step 1: Install dependencies

```bash
pip install huggingface-hub ctranslate2
```

#### Step 2: Download the model

```bash
huggingface-cli download facebook/nllb-200-distilled-600M --local-dir models/nllb-200-distilled-600M-hf
```

#### Step 3: Convert to CTranslate2 format

```bash
ct2-transformers-converter \
  --model models/nllb-200-distilled-600M-hf \
  --output_dir models/nllb-200-distilled-600M-ct2 \
  --quantization int8
```

#### Step 4: Verify

Check that these files exist:
- `models/nllb-200-distilled-600M-ct2/model.bin`
- `models/nllb-200-distilled-600M-ct2/config.json`
- `models/nllb-200-distilled-600M-ct2/sentencepiece.model`

---

## Alternative: Pre-converted CTranslate2 Models

Some community members have uploaded pre-converted CTranslate2 models to Hugging Face. You can search for:

- `Narsil/nllb-200-distilled-600M-ct2` (if available)
- Or convert yourself using the instructions above

---

## Storage Requirements

| Model | Disk Space | RAM (Runtime) |
|-------|-----------|---------------|
| faster-whisper medium | ~1.5 GB | ~1.5 GB |
| NLLB-200-600M (ct2) | ~1.2 GB | ~1.2 GB |
| **Total** | **~2.7 GB** | **~2.7 GB** |

**Recommended System**:
- CPU: 4+ cores
- RAM: 8+ GB (4 GB for models + 4 GB for OS/app)
- Storage: 10 GB free (for models + dependencies)

---

## Model Licenses

### faster-whisper
- Based on OpenAI Whisper
- License: MIT
- Source: https://github.com/SYSTRAN/faster-whisper

### NLLB-200
- Developer: Meta AI
- License: CC-BY-NC 4.0 (non-commercial research)
- For commercial use, contact Meta AI
- Source: https://github.com/facebookresearch/fairseq/tree/nllb

### CTranslate2
- License: MIT
- Source: https://github.com/OpenNMT/CTranslate2

---

## Troubleshooting

### faster-whisper fails to download

**Solution**: Ensure you have internet access and enough disk space. The model downloads to `~/.cache/huggingface/hub/`.

### NLLB conversion fails

**Common issues**:
1. **Out of memory**: CTranslate2 conversion requires ~4GB RAM. Close other applications.
2. **Missing dependencies**: Ensure `transformers`, `sentencepiece`, and `ctranslate2` are installed.
3. **Network timeout**: Download the model manually first, then convert.

### Models not found at runtime

**Solution**: Check that `server/config.py` points to the correct model paths:
- `WHISPER_MODEL_SIZE = "medium"`
- `NLLB_MODEL_PATH = "models/nllb-200-distilled-600M-ct2"`

Update paths in `.env` if models are in a different location.

---

## Future Models (Phase 2/3)

### Phase 2: Kokoro TTS
- Size: ~160 MB
- Location: Browser (downloads to client)
- Purpose: Generic text-to-speech

### Phase 3: F5-TTS
- Size: ~200 MB
- Location: Browser (downloads to client)
- Purpose: Voice cloning TTS

These models run on the client side (browser) using WebGPU/WASM, so they don't need to be downloaded for the server.
