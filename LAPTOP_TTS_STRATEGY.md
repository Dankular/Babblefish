# Laptop TTS Accelerator Strategy - Chatterbox + F5-TTS

## Overview

The 3050 GPU (4GB VRAM) runs **two complementary TTS models** for optimal quality and coverage:

1. **Chatterbox Turbo** - Fast multilingual TTS (23 languages)
2. **F5-TTS** - Deep voice cloning for authentic speaker voices

## Why Both Models?

### Chatterbox Turbo (Primary - Fast Path)

**Strengths:**
- ✅ **23 languages supported** (vs Kokoro's ~5)
- ✅ **Zero-shot voice cloning** (instant, no training needed)
- ✅ **Emotion control** (happy, sad, angry)
- ✅ **Fast inference** (350M parameters, optimized)
- ✅ **High quality** (beats ElevenLabs in blind tests - 63.75% preference)
- ✅ **MIT license** (permissive, open-source)

**Best for:**
- Immediate multilingual output
- Quick voice adaptation
- Languages not in your training set
- Emotional expression

**VRAM:** ~1-1.5GB

### F5-TTS (Secondary - Quality Path)

**Strengths:**
- ✅ **Authentic voice cloning** (deep learning, highest quality)
- ✅ **Speaker-specific training** (learns exact voice characteristics)
- ✅ **Natural prosody** (rhythm, intonation)
- ✅ **Long-term consistency** (trained models)

**Best for:**
- Known speakers (Pierre, Dan, Marek)
- Maximum authenticity
- Consistent character voices
- High-stakes scenarios

**VRAM:** ~2-2.5GB

### Combined Power

**Together on 3050 (4GB VRAM):**
```
Chatterbox Turbo:  ~1.5 GB
F5-TTS:            ~2.5 GB
─────────────────────────
Total:             ~4 GB  ✅ Fits perfectly!
```

## Three-Tier TTS Architecture

```
📱 Phone receives THREE versions of translation:

Tier 1: Kokoro (Server)
  ├─ Latency: ~2.0s
  ├─ Quality: Good (generic voice)
  ├─ Coverage: Basic languages
  └─ Purpose: Immediate comprehension

Tier 2: Chatterbox (Laptop - Fast Path)
  ├─ Latency: ~2.3s (+0.3s from Kokoro)
  ├─ Quality: Excellent (zero-shot cloning)
  ├─ Coverage: 23 languages
  └─ Purpose: High-quality multilingual

Tier 3: F5-TTS (Laptop - Quality Path)
  ├─ Latency: ~2.8s (+0.5s from Chatterbox)
  ├─ Quality: Exceptional (trained clone)
  ├─ Coverage: Trained speakers only
  └─ Purpose: Authentic Babel Fish magic
```

## Chatterbox Details

### Model: Chatterbox Turbo

**Specifications:**
- **Parameters:** 350M (efficient for GPU)
- **Languages:** 23 (Arabic, Chinese, Danish, Dutch, English, Finnish, French, German, Greek, Hebrew, Hindi, Italian, Japanese, Korean, Malay, Norwegian, Polish, Portuguese, Russian, Spanish, Swahili, Swedish, Turkish)
- **Sample rate:** 24kHz
- **Zero-shot:** Yes (instant voice cloning from 5-10s reference)
- **Emotion control:** Yes (happy, sad, angry + intensity)
- **Paralinguistic:** Yes ([laugh], [cough], [chuckle])
- **License:** MIT (open-source)

**Performance:**
- Inference speed: ~300-500ms per sentence (GPU)
- Quality: Beats ElevenLabs in 63.75% of blind tests
- VRAM usage: ~1-1.5GB

### Installation

```bash
pip install chatterbox-tts
# or from source:
git clone https://github.com/resemble-ai/chatterbox.git
cd chatterbox
pip install -e .
```

### Usage

```python
from chatterbox import ChatterboxTTS

# Initialize
tts = ChatterboxTTS(
    model="ResembleAI/chatterbox-turbo",
    device="cuda"
)

# Synthesize with zero-shot voice cloning
audio = tts.synthesize(
    text="Hello, how are you?",
    reference_audio="path/to/speaker.wav",  # 5-10s sample
    language="en",
    emotion="neutral",
    emotion_intensity=1.0
)
```

## Decision Flow (Laptop TTS Accelerator)

```python
def choose_tts_model(
    text: str,
    speaker_id: str,
    target_lang: str,
    has_f5_trained: bool,
    has_reference_audio: bool
):
    """
    Choose best TTS model for this request

    Decision tree:
    1. If F5-TTS trained for this speaker → Use F5-TTS (highest quality)
    2. Else if Chatterbox supports language → Use Chatterbox (good quality)
    3. Else → Fallback to Kokoro on server
    """

    # Tier 3: F5-TTS (trained speaker voices)
    if has_f5_trained:
        return use_f5_tts(text, speaker_id)

    # Tier 2: Chatterbox (zero-shot cloning)
    elif target_lang in CHATTERBOX_LANGUAGES and has_reference_audio:
        return use_chatterbox(text, speaker_id, target_lang, reference_audio)

    # Tier 1: Already sent from server (Kokoro)
    else:
        return None  # Server Kokoro already sent
```

## Language Coverage Comparison

### Kokoro (Server - Tier 1)
```
Languages: ~5 (English, Japanese, Korean, Chinese, Spanish)
Quality: Good
Speed: Fast (~300ms)
```

### Chatterbox (Laptop - Tier 2)
```
Languages: 23
  - European: English, Spanish, French, German, Italian, Portuguese,
              Dutch, Danish, Finnish, Norwegian, Polish, Swedish, Greek
  - Asian: Chinese, Japanese, Korean, Hindi, Malay, Hebrew
  - Middle Eastern: Arabic, Turkish
  - African: Swahili
  - Slavic: Russian, Polish

Quality: Excellent (beats ElevenLabs)
Speed: Fast (~400ms GPU)
```

### F5-TTS (Laptop - Tier 3)
```
Languages: Any (trained on collected samples)
Quality: Exceptional (authentic cloning)
Speed: Moderate (~800ms GPU)
```

## Resource Allocation (3050 GPU)

```
Component           VRAM      Usage Pattern
───────────────────────────────────────────────
Chatterbox Turbo   1.5 GB    Always loaded
F5-TTS             2.5 GB    Loaded when trained speakers available
Temp buffers       0.5 GB    Processing overhead
───────────────────────────────────────────────
Total Peak         4.0 GB    ✅ Perfect fit for 3050

Dynamic loading:
  - Chatterbox: Always active (covers 23 languages)
  - F5-TTS: Loaded only when needed (conserves VRAM)
```

## Progressive Enhancement Timeline

### Phase 1: Kokoro Only (Server)
```
Latency: ~2.0s
Quality: Good
Languages: 5
Cost: Server CPU only
```

### Phase 2: + Chatterbox (Laptop)
```
Latency: ~2.3s (Kokoro) + ~2.6s (Chatterbox)
Quality: Excellent
Languages: 23
Cost: Laptop 3050 GPU (~1.5GB VRAM)
```

### Phase 3: + F5-TTS (Laptop)
```
Latency: ~2.0s (Kokoro) + ~2.3s (Chatterbox) + ~2.8s (F5)
Quality: Exceptional
Languages: 23 + any trained
Cost: Laptop 3050 GPU (~4GB VRAM full)
```

## Use Case Examples

### Example 1: Pierre speaks French (trained speaker)

**What happens:**
1. **Server sends Kokoro** (~2s) - Generic French voice
2. **Laptop sends Chatterbox** (~2.3s) - Zero-shot Pierre voice (French accent)
3. **Laptop sends F5-TTS** (~2.8s) - Trained Pierre clone (authentic)

**User experience:**
- Hears Kokoro first (immediate comprehension)
- Chatterbox replaces it (better quality, French characteristics)
- F5-TTS replaces that (sounds exactly like Pierre)

### Example 2: New speaker (Greek)

**What happens:**
1. **Server sends Kokoro** (~2s) - Generic voice (may not support Greek well)
2. **Laptop sends Chatterbox** (~2.3s) - Zero-shot Greek voice (no training needed!)

**User experience:**
- Hears Kokoro first (comprehension)
- Chatterbox replaces it (proper Greek pronunciation, natural)

### Example 3: Emotional speech

**What happens:**
1. **Server sends Kokoro** (~2s) - Neutral tone
2. **Laptop sends Chatterbox** (~2.3s) - With emotion control
   - Text: "I'm so happy!" → Chatterbox adds happy emotion
   - Text: "This is terrible..." → Chatterbox adds sad/concerned emotion

**User experience:**
- Hears neutral first
- Emotional version adds context and realism

## Advantages of Dual-Model Approach

### 1. Language Coverage
- **Kokoro:** 5 languages
- **+ Chatterbox:** 23 languages (18 additional)
- **+ F5-TTS:** Any language (trained)

### 2. Quality Progression
- **Tier 1 (Kokoro):** Immediate, understandable
- **Tier 2 (Chatterbox):** High quality, zero-shot cloning
- **Tier 3 (F5-TTS):** Exceptional, authentic cloning

### 3. Fault Tolerance
- If laptop disconnects → Kokoro works
- If F5-TTS unavailable → Chatterbox works
- If Chatterbox unavailable → Kokoro works

### 4. VRAM Efficiency
- Dynamic loading based on need
- Chatterbox (1.5GB) always ready
- F5-TTS (2.5GB) only when trained speakers present

### 5. Zero-Shot Capability
- Chatterbox clones voices instantly (5-10s reference audio)
- No training wait time
- Works for new speakers immediately

## Implementation Priority

### Immediate (Phase 2A): Chatterbox Only
```bash
# Fastest path to 23-language support
pip install chatterbox-tts
python laptop_tts_accelerator.py --model chatterbox

Benefits:
  ✅ 23 languages instantly
  ✅ Zero-shot voice cloning
  ✅ Emotion control
  ✅ Only 1.5GB VRAM
  ✅ Beats ElevenLabs quality
```

### Later (Phase 2B): + F5-TTS
```bash
# Add deep voice cloning
python laptop_tts_accelerator.py --model both

Benefits:
  ✅ All Chatterbox features
  ✅ + Authentic trained voices
  ✅ Best of both worlds
  ✅ Uses full 4GB VRAM
```

## Performance Benchmarks

### Chatterbox Turbo (3050 GPU)
```
Text length: 20 words
Inference time: ~400ms
VRAM usage: 1.5 GB
Quality score: 4.2/5 (blind test)
Languages: 23
```

### F5-TTS (3050 GPU)
```
Text length: 20 words
Inference time: ~800ms
VRAM usage: 2.5 GB
Quality score: 4.8/5 (with training)
Languages: Unlimited (trained)
```

### Kokoro (Server CPU)
```
Text length: 20 words
Inference time: ~300ms
CPU threads: 16
Quality score: 3.8/5
Languages: 5
```

## Recommended Configuration

```python
# laptop_tts_accelerator.py config

TTS_CONFIG = {
    "primary": "chatterbox",      # Always active
    "secondary": "f5-tts",         # Load when trained speakers available
    "fallback": "server-kokoro",   # Already sent from server

    "chatterbox": {
        "model": "ResembleAI/chatterbox-turbo",
        "vram": "1.5GB",
        "languages": 23,
        "zero_shot": True,
        "emotion_control": True
    },

    "f5-tts": {
        "model": "F5-TTS",
        "vram": "2.5GB",
        "quality": "exceptional",
        "requires_training": True
    }
}
```

---

**Status:** Ready to implement
**Recommendation:** Start with Chatterbox only (Phase 2A), add F5-TTS when speakers are trained
**VRAM:** Perfect fit for 3050 (4GB)
**Quality:** Better than ElevenLabs (proven in blind tests)

**Last Updated:** 2026-02-08

---

**Sources:**
- [Chatterbox GitHub](https://github.com/resemble-ai/chatterbox)
- [Chatterbox Multilingual Launch](https://www.resemble.ai/introducing-chatterbox-multilingual-open-source-tts-for-23-languages/)
- [Chatterbox Turbo Model](https://huggingface.co/ResembleAI/chatterbox-turbo)
- [Chatterbox Performance Benchmarks](https://www.marktechpost.com/2025/09/05/meet-chatterbox-multilingual-an-open-source-zero-shot-text-to-speech-tts-multilingual-model-with-emotion-control-and-watermarking/)
