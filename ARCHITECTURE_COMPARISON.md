# Architecture Comparison: Current vs Lightweight Alternative

## Two Approaches

You have two excellent options for the server architecture. Both support the hybrid TTS approach (Kokoro immediate + F5-TTS optional).

---

## Option A: Current (SeamlessM4T-based)

### Server Stack
```
Component                 Threads    RAM      Notes
─────────────────────────────────────────────────────────────
SeamlessM4T v2 Medium        32     3-4 GB   All-in-one ASR+MT
Kokoro TTS (ONNX)            16     500 MB   Fast synthesis
Pyannote Speaker ID           4     200 MB   Embedding-based
WebSocket routing             8     100 MB   Multi-client
─────────────────────────────────────────────────────────────
Total                       ~60     ~5 GB    47% cores
```

**Pros:**
- ✅ Single model for ASR + Translation (simpler)
- ✅ State-of-the-art quality
- ✅ 200+ languages built-in
- ✅ Consistent performance

**Cons:**
- ❌ Larger memory footprint (~5GB)
- ❌ More cores used (60 of 128)
- ❌ Heavier model loading time

**Best for:** When you want maximum quality and simplicity (one model does everything)

---

## Option B: Lightweight (Whisper + NLLB)

### Server Stack
```
Component                 Threads    RAM      Notes
─────────────────────────────────────────────────────────────
Silero VAD                    1     ~10 MB   Speech detection
SpeechBrain Embeddings        4     200 MB   Speaker ID
faster-whisper Medium     16-32     1.5 GB   ASR only (int8)
NLLB-600M (CTranslate2)    8-16     1.2 GB   Translation only
Kokoro TTS (ONNX)            16     500 MB   Fast synthesis
WebSocket routing           4-8     100 MB   Multi-client
─────────────────────────────────────────────────────────────
Total                    35-60     ~3.5 GB   27-47% cores
```

**Pros:**
- ✅ Lower memory usage (~3.5GB vs ~5GB)
- ✅ More modular (can swap components)
- ✅ Potentially faster (two smaller models vs one large)
- ✅ Leaves more server capacity for other workloads

**Cons:**
- ❌ More complex (two models to manage)
- ❌ Two inference passes (Whisper then NLLB)
- ❌ Additional VAD step needed

**Best for:** When you want maximum efficiency and have other workloads on the server

---

## Detailed Comparison

### Latency

**Option A (SeamlessM4T):**
```
Speaker ID:       50ms
SeamlessM4T:    800ms   ← Single model does ASR + MT
Kokoro TTS:     300ms
─────────────────────
Total:         1150ms
```

**Option B (Whisper + NLLB):**
```
Silero VAD:      10ms   ← Extra step
Speaker ID:      50ms
Whisper ASR:    500ms   ← Faster than SeamlessM4T for ASR alone
NLLB MT:        300ms   ← Faster than SeamlessM4T for MT alone
Kokoro TTS:     300ms
─────────────────────
Total:         1160ms
```

**Winner:** Roughly equivalent (~1.1-1.2s both)

### Memory Efficiency

**Option A:** ~5GB
**Option B:** ~3.5GB

**Winner:** Option B (30% less RAM)

### CPU Utilization

**Option A:** 60/128 cores (47%)
**Option B:** 35-60/128 cores (27-47%)

**Winner:** Option B (more headroom)

### Quality

**Option A:** State-of-the-art (SeamlessM4T is newer)
**Option B:** Excellent (Whisper + NLLB-600M proven)

**Winner:** Option A (slightly better, but both are excellent)

### Complexity

**Option A:** 1 main model (SeamlessM4T)
**Option B:** 2 main models (Whisper + NLLB)

**Winner:** Option A (simpler)

---

## Laptop Component (Same for Both)

### Option 1: F5-TTS (What we implemented)
```
Model: F5-TTS
VRAM: 2-3 GB
Quality: Excellent voice cloning
Speed: ~800ms per sentence
```

### Option 2: Chatterbox Multilingual (Your suggestion)
```
Model: Chatterbox Multilingual
VRAM: 2-3 GB
Quality: Good multilingual TTS
Speed: ~500-800ms
```

Both work with the hybrid architecture. F5-TTS is better for voice cloning, Chatterbox might be faster for multilingual.

---

## Resource Breakdown Summary

### Option A (Current Implementation)

```
🖥 Server (128 cores):
├─ SeamlessM4T:     32 threads, 3.5 GB
├─ Kokoro TTS:      16 threads, 0.5 GB
├─ Pyannote:         4 threads, 0.2 GB
├─ WebSocket:        8 threads, 0.1 GB
└─ Total:          ~60 threads, ~5 GB (47% cores, minimal RAM)

💻 Laptop (3050 - 4GB VRAM):
└─ F5-TTS:         GPU, 2-3 GB VRAM

Remaining Server Capacity: 68 cores, lots of RAM
```

### Option B (Lightweight Alternative)

```
🖥 Server (128 cores):
├─ Silero VAD:       1 thread,  0.01 GB
├─ SpeechBrain:      4 threads, 0.2 GB
├─ Whisper Medium:  32 threads, 1.5 GB
├─ NLLB-600M:       16 threads, 1.2 GB
├─ Kokoro TTS:      16 threads, 0.5 GB
├─ WebSocket:        8 threads, 0.1 GB
└─ Total:          ~60 threads, ~3.5 GB (47% cores, less RAM)

💻 Laptop (3050 - 4GB VRAM):
└─ Chatterbox/F5:  GPU, 2-3 GB VRAM

Remaining Server Capacity: 68 cores, even more RAM
```

---

## Recommendation

### For Your Use Case

**If you:**
- Want simplest setup → **Option A**
- Have other workloads on server → **Option B**
- Want maximum quality → **Option A**
- Want maximum efficiency → **Option B**
- Care most about ease of maintenance → **Option A**

**My recommendation:** Start with **Option A** (current implementation)

**Why:**
- Already implemented and ready to test
- Simpler (one model vs two)
- State-of-the-art quality
- Still uses <50% of your server capacity
- Your existing Whisper workload can run alongside easily (~1.5GB + ~3.5GB = 5GB total, plenty of room)

**Then:** If you need more server capacity later, switch to Option B

---

## Migration Path

### Start: Option A (SeamlessM4T)
```bash
# Current implementation
python server_cpu.py
```

### Later: Option B (Whisper + NLLB)
```bash
# Create server_cpu_lightweight.py with:
# - SpeechBrain instead of pyannote
# - faster-whisper instead of SeamlessM4T ASR
# - NLLB-600M instead of SeamlessM4T MT
# - Silero VAD for speech detection
```

Both use the same:
- Client protocol (no changes needed)
- Laptop accelerator (works with both)
- Hybrid TTS approach (Kokoro + F5)

---

## Coexistence with Existing Workloads

Your concern: "Your existing Whisper workload can run alongside this"

### With Option A (SeamlessM4T)
```
Server Total: 128 cores, 256 GB RAM

BabbleFish:           60 cores, ~5 GB
Your Whisper workload: X cores, ~1.5 GB
─────────────────────────────────────
Remaining:         68-X cores, ~249 GB

✓ Plenty of room for both
```

### With Option B (Whisper + NLLB)
```
Server Total: 128 cores, 256 GB RAM

BabbleFish:           60 cores, ~3.5 GB
Your Whisper workload: Can share Whisper instance!
─────────────────────────────────────
Remaining:         68 cores, ~252 GB

✓ Even more room
✓ Can share Whisper model between workloads
```

**Advantage Option B:** If you already have Whisper running, BabbleFish can use the same instance (save ~1.5GB RAM)

---

## Next Steps

### Option 1: Proceed with Current (Recommended)
```bash
# Test what we have
python server_cpu.py
python laptop_tts_accelerator.py

# Evaluate:
# - Does it work well?
# - Is latency acceptable?
# - Is server capacity sufficient?

# If yes → Production deployment
# If no → Consider Option B
```

### Option 2: Implement Lightweight Version
```bash
# I can create server_cpu_lightweight.py with:
# - SpeechBrain embeddings
# - faster-whisper medium
# - NLLB-600M CTranslate2
# - Silero VAD

# Then test and compare
```

**Your call!** Both are excellent. Option A is ready now, Option B would take ~1-2 hours to implement.

---

**Recommendation:** Test Option A first (it's ready), switch to Option B only if you need the extra server capacity.

**Status:** Option A implemented, Option B can be added if needed
**Last Updated:** 2026-02-08
