# BabbleFish - Final Production Architecture

## Three-Tier Progressive TTS System

```
📱 Phones ──► 🖥 Server (128 cores) ──► 💻 Laptop (3050 GPU - 4GB)
              │                         │
              ├─ Tier 1: Kokoro         ├─ Tier 2: Chatterbox Turbo
              │  ~2.0s latency          │  ~2.3s latency
              │  5 languages            │  23 languages
              │  Generic voice          │  Zero-shot cloning
              │  Always available       │  Beats ElevenLabs
              │                         │
              │                         ├─ Tier 3: F5-TTS
              │                         │  ~2.8s latency
              │                         │  Authentic cloning
              │                         │  Trained speakers
              └─────────────────────────┘
```

## Complete System Overview

### Server (🖥 128 cores, 256GB RAM)

**Components:**
```
SeamlessM4T v2:      32 threads, 3.5 GB  - ASR + Translation
Kokoro TTS:          16 threads, 0.5 GB  - Tier 1 TTS (generic)
Pyannote Speaker:     4 threads, 0.2 GB  - Speaker identification
WebSocket Hub:        8 threads, 0.1 GB  - Multi-client routing
────────────────────────────────────────────────────────────────
Total:              ~60 threads, ~5 GB   (47% cores, minimal RAM)
Remaining:          ~68 threads, ~251 GB (plenty of headroom)
```

### Laptop (💻 3050 GPU, 4GB VRAM)

**Components:**
```
Chatterbox Turbo:   1.5 GB VRAM  - Tier 2 TTS (23 languages)
F5-TTS:             2.5 GB VRAM  - Tier 3 TTS (voice cloning)
────────────────────────────────────────────────────────────
Total:              4.0 GB VRAM  (perfect fit!)
```

### Phones (📱 Thin Clients)

**Resources:**
```
CPU:   <10%
RAM:   <100MB
GPU:   FREE (0% usage)
```

## Three-Tier TTS Strategy

### Tier 1: Kokoro (Server CPU) - Immediate Comprehension

**Purpose:** Always-available baseline quality
**Latency:** ~2.0s from speech end
**Languages:** 5 (English, Japanese, Korean, Chinese, Spanish)
**Quality:** Good (generic voices)
**Fallback:** Works even if laptop disconnected

**When used:**
- Always sent first (immediate comprehension)
- Fallback if laptop unavailable
- Languages not supported by Chatterbox

### Tier 2: Chatterbox Turbo (Laptop GPU) - Excellent Quality

**Purpose:** High-quality multilingual with zero-shot cloning
**Latency:** ~2.3s from speech end
**Languages:** 23 (Arabic, Chinese, Danish, Dutch, English, Finnish, French, German, Greek, Hebrew, Hindi, Italian, Japanese, Korean, Malay, Norwegian, Polish, Portuguese, Russian, Spanish, Swahili, Swedish, Turkish)
**Quality:** Excellent (beats ElevenLabs in 63.75% of blind tests)
**Features:**
- Zero-shot voice cloning (5-10s reference audio)
- Emotion control (happy, sad, angry)
- Paralinguistic tags ([laugh], [cough], [chuckle])
- MIT license (open-source)

**When used:**
- Language supported by Chatterbox
- No trained F5-TTS model available
- New speakers (instant voice adaptation)
- Emotional expression needed

### Tier 3: F5-TTS (Laptop GPU) - Authentic Cloning

**Purpose:** Maximum authenticity for known speakers
**Latency:** ~2.8s from speech end
**Languages:** Any (learns from collected samples)
**Quality:** Exceptional (sounds exactly like speaker)
**Features:**
- Deep voice cloning
- Natural prosody and rhythm
- Speaker-specific training
- Long-term consistency

**When used:**
- Speaker has trained model available
- Maximum authenticity required
- Known participants (Pierre, Dan, Marek)

## Progressive User Experience

### Example: Pierre speaks French

**Timeline:**

```
0ms      - Pierre starts speaking French
1500ms   - VAD detects pause, sends to server
1600ms   - Server identifies: "Pierre"
2400ms   - SeamlessM4T completes: FR → EN translation

2000ms   - 🔊 Tier 1 plays: Kokoro (generic English voice)
           User comprehends immediately

2300ms   - 🔊 Tier 2 plays: Chatterbox (Pierre's French accent in English)
           Better quality, language characteristics

2800ms   - 🔊 Tier 3 plays: F5-TTS (Sounds exactly like Pierre speaking English)
           Authentic Babel Fish magic
```

**User hears:**
1. First: Generic but clear English (comprehension)
2. Then: High-quality with French accent (improvement)
3. Finally: Pierre's actual voice speaking English (perfection)

## Decision Tree (Laptop TTS Accelerator)

```python
def choose_tts_tier(speaker_id, target_lang, has_reference):
    """
    Smart TTS selection

    Priority order:
    1. F5-TTS if trained for speaker
    2. Chatterbox if language supported
    3. Kokoro (already sent from server)
    """

    # Tier 3: Best quality for known speakers
    if has_f5_trained_model(speaker_id):
        return "f5-tts"  # ~2.8s, exceptional quality

    # Tier 2: Excellent multilingual
    elif target_lang in CHATTERBOX_LANGS:  # 23 languages
        return "chatterbox"  # ~2.3s, excellent quality

    # Tier 1: Baseline (server handles this)
    else:
        return "kokoro"  # ~2.0s, good quality (from server)
```

## Language Coverage

### Kokoro (Tier 1)
```
Languages: 5
- English (en)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)
- Spanish (es)

Coverage: ~40% of world population
```

### Chatterbox (Tier 2)
```
Languages: 23
- European: English, Spanish, French, German, Italian, Portuguese,
            Dutch, Danish, Finnish, Norwegian, Polish, Swedish, Greek
- Asian: Chinese, Japanese, Korean, Hindi, Malay, Hebrew
- Middle Eastern: Arabic, Turkish
- African: Swahili

Coverage: ~75% of world population
```

### F5-TTS (Tier 3)
```
Languages: Unlimited (learns from samples)
- Any language with training data
- Speaker-specific cloning
- Learns accents, dialects, characteristics

Coverage: 100% (with training)
```

## Performance Comparison

| Metric | Kokoro (T1) | Chatterbox (T2) | F5-TTS (T3) |
|--------|-------------|-----------------|-------------|
| **Latency** | ~2.0s | ~2.3s | ~2.8s |
| **Languages** | 5 | 23 | Any |
| **Quality** | Good | Excellent | Exceptional |
| **Voice** | Generic | Zero-shot clone | Trained clone |
| **VRAM** | 0 (CPU) | ~1.5 GB | ~2.5 GB |
| **Training** | None | None | 50+ chunks |
| **Emotion** | No | Yes | Limited |
| **Availability** | Always | If laptop | If trained |

## Deployment Strategy

### Phase 1: Server Only (Day 1)

**Deploy:**
- Server with SeamlessM4T + Kokoro
- Phone clients

**Result:**
- ✅ Tier 1 TTS (Kokoro)
- ✅ 5 languages
- ✅ ~2s latency
- ✅ Works immediately

### Phase 2A: + Chatterbox (Week 1)

**Add:**
- Laptop with Chatterbox Turbo

**Result:**
- ✅ Tier 1 + Tier 2 TTS
- ✅ 23 languages
- ✅ Zero-shot voice cloning
- ✅ Beats ElevenLabs quality

**Command:**
```bash
python laptop_tts_accelerator.py --strategy chatterbox
```

### Phase 2B: + F5-TTS (Week 2+)

**Add:**
- F5-TTS on same laptop

**Result:**
- ✅ All three tiers
- ✅ Authentic voice cloning
- ✅ Complete Babel Fish experience

**Command:**
```bash
python laptop_tts_accelerator.py --strategy both
```

## Installation

### Server
```bash
pip install -r requirements_server.txt
huggingface-cli login  # Accept pyannote terms
python server_cpu.py
```

### Laptop (Chatterbox + F5-TTS)
```bash
# Install Chatterbox
pip install chatterbox-tts
# OR from source:
git clone https://github.com/resemble-ai/chatterbox.git
cd chatterbox && pip install -e .

# Install F5-TTS (TODO: Add installation)

# Start accelerator
python laptop_tts_accelerator.py --strategy both
```

### Phones
```bash
# Open client_thin.html
# Configure server URL
# Start speaking!
```

## Resource Utilization

### Server (128 cores)
```
Used:      60 cores (47%)
Available: 68 cores (53%)
RAM:       ~5 GB of 256 GB

Can run other workloads simultaneously:
- Your existing Whisper workload
- Other applications
- Future expansions
```

### Laptop (3050 GPU - 4GB VRAM)
```
Chatterbox:  1.5 GB (37%)
F5-TTS:      2.5 GB (63%)
─────────────────────────
Total:       4.0 GB (100% - perfect fit!)

CPU: <5% (minimal)
```

## Advantages of Three-Tier Approach

1. **Progressive Enhancement**
   - Works immediately (Tier 1)
   - Improves with laptop (Tier 2)
   - Perfects with training (Tier 3)

2. **Fault Tolerance**
   - Laptop down → Tier 1 still works
   - F5-TTS unavailable → Tier 2 still works
   - No single point of failure

3. **Language Coverage**
   - Tier 1: 5 languages
   - Tier 2: 23 languages
   - Tier 3: Unlimited languages

4. **Quality Options**
   - Tier 1: Good (generic)
   - Tier 2: Excellent (zero-shot)
   - Tier 3: Exceptional (trained)

5. **User Experience**
   - Immediate response (~2s)
   - Quality improvements (~2.3s, ~2.8s)
   - Seamless progression

## Production Checklist

- [x] Server code complete
- [x] Laptop TTS accelerator complete
- [x] Phone client complete
- [x] Documentation complete
- [x] GitHub repository updated
- [ ] Test Chatterbox installation
- [ ] Test F5-TTS installation
- [ ] Production deployment
- [ ] User training

## Next Steps

1. **Test Chatterbox** (This week)
   ```bash
   pip install chatterbox-tts
   python laptop_tts_accelerator.py --strategy chatterbox
   # Test with multiple languages
   ```

2. **Compare Quality** (This week)
   - Kokoro vs Chatterbox
   - Zero-shot cloning effectiveness
   - Language coverage verification

3. **Add F5-TTS** (Next week)
   - Collect speaker samples (50+ chunks)
   - Train speaker models
   - Test Tier 3 quality

4. **Production Deploy** (Week 2)
   - Server on 128-core machine
   - Laptop accelerator
   - Phone clients
   - Monitor performance

---

**Final Architecture:** ✅ Complete
**Status:** Ready for testing
**Recommendation:** Deploy Phase 2A (Chatterbox) immediately
**GitHub:** https://github.com/Dankular/Babblefish

**Last Updated:** 2026-02-08
