# 🚀 BabbleFish Benchmark Guide

## What's Being Tested

### 1. **NLLB Translation Speed** ⚡
- Tests short, medium, long, and very long text
- Measures words per second
- Shows translation latency by text length

### 2. **Whisper Transcription Speed** 🎤
- Tests 1s, 3s, 5s, and 10s audio
- Calculates Real-Time Factor (RTF)
- RTF < 1.0 = Faster than real-time ✅

### 3. **End-to-End Pipeline** 🔄
- Complete flow: Audio → Transcription → Translation
- Shows latency breakdown
- Includes all overhead (VAD, network, etc.)

### 4. **Maximum Throughput** 📊
- How many sentences per minute
- Sustained performance test
- Tests batch processing efficiency

### 5. **Memory Usage** 💾
- RAM used by each model
- Total memory footprint
- Identifies memory bottlenecks

### 6. **CPU Utilization** 🖥️
- Average CPU usage during inference
- Peak CPU usage
- Per-core utilization

---

## Expected Performance (CPU)

### Good Performance ✅
```
NLLB Translation:     0.5-1.5s per sentence
Whisper (3s audio):   ~1.0s (RTF: ~0.3x)
End-to-end latency:   2-3s total
Throughput:           15-25 sentences/min
Memory:               4-6 GB
CPU:                  50-80% (single core)
```

### Excellent Performance 🔥
```
NLLB Translation:     <0.5s per sentence
Whisper (3s audio):   <0.8s (RTF: <0.27x)
End-to-end latency:   <2s total
Throughput:           >25 sentences/min
Memory:               <5 GB
CPU:                  <50% (single core)
```

### With GPU 🚀
```
NLLB Translation:     0.1-0.3s per sentence
Whisper (3s audio):   ~0.3s (RTF: ~0.1x)
End-to-end latency:   0.5-1s total
Throughput:           60-100 sentences/min
Memory:               2-4 GB VRAM
GPU:                  20-40% utilization
```

---

## Performance Grades

| Grade | Latency | Throughput | Notes |
|-------|---------|------------|-------|
| **A+** | <2s | >25/min | Excellent - Production ready |
| **A**  | 2-3s | 20-25/min | Great - Very usable |
| **B+** | 3-4s | 15-20/min | Good - Acceptable |
| **B**  | 4-5s | 10-15/min | OK - May need optimization |
| **C**  | >5s | <10/min | Slow - Check configuration |

---

## Interpreting Results

### Real-Time Factor (RTF)
```
RTF = Processing Time / Audio Duration

RTF < 1.0 = Faster than real-time ✅
RTF = 1.0 = Same speed as real-time
RTF > 1.0 = Slower than real-time ❌

Example:
3s audio processed in 0.9s → RTF = 0.3x (3x faster!)
```

### Words Per Second (WPS)
```
Higher is better!

Good:   >10 words/sec
Great:  >20 words/sec
Amazing: >30 words/sec
```

### Throughput
```
Sentences per minute at sustained load

Production target: >15/min
Real-time target:  >20/min (to handle spikes)
```

---

## Optimization Tips

### If Latency is High (>3s)

1. **Check Model Sizes**
   ```python
   # Use smaller models
   WHISPER_MODEL_SIZE = "small"  # instead of "medium"
   NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"  # instead of 1.3B
   ```

2. **Optimize Quantization**
   ```python
   compute_type="int8"  # Already optimal for CPU
   ```

3. **Reduce Beam Size**
   ```python
   beam_size=1  # Fastest (lower quality)
   beam_size=4  # Balanced (default)
   beam_size=8  # Best quality (slower)
   ```

### If Memory is High (>6GB)

1. **Use Smaller Models**
   - Whisper: tiny (39M), base (74M), small (244M)
   - NLLB: 600M instead of 1.3B

2. **Unload Models Between Uses**
   ```python
   del model
   import gc
   gc.collect()
   ```

### If CPU Usage is High (>90%)

1. **Reduce Thread Count**
   ```python
   inter_threads=2  # instead of 4
   intra_threads=2  # instead of 4
   ```

2. **Add Delays Between Requests**
   ```python
   time.sleep(0.1)  # Give CPU a break
   ```

---

## Comparison to Alternatives

### vs. Google Cloud Speech-to-Text + Translation API
```
BabbleFish (CPU):     2-3s latency, FREE
Google Cloud:         2-4s latency, $0.024/min

Advantage: Cost and privacy
```

### vs. AWS Transcribe + Translate
```
BabbleFish (CPU):     2-3s latency, FREE
AWS:                  3-5s latency, $0.03/min

Advantage: Cost, latency, and customization
```

### vs. DeepL Live Translator
```
BabbleFish (CPU):     2-3s latency, FREE, 200+ languages
DeepL:                2-4s latency, €25/month, 30 languages

Advantage: Cost, languages, privacy
```

---

## Bottleneck Analysis

The benchmark will show you where time is spent:

```
Typical breakdown:
  Transcription:    50-60%  (Whisper)
  Translation:      30-40%  (NLLB)
  Overhead:         5-10%   (VAD, I/O)
```

### If Transcription is Slow
- Whisper is the bottleneck
- Consider smaller model or GPU

### If Translation is Slow
- NLLB is the bottleneck
- Consider smaller model or GPU

### If Both are Slow
- CPU is saturated
- Consider GPU or model reduction

---

## Sample Output

```
============================================================
BENCHMARK SUMMARY REPORT
============================================================

📊 NLLB Translation Performance
────────────────────────────────────────
Short        0.523s  (1.9 words/sec)
Medium       0.687s  (8.7 words/sec)
Long         1.142s  (15.8 words/sec)
Very Long    1.856s  (18.3 words/sec)

🎤 Whisper Transcription Performance
────────────────────────────────────────
1s audio:   0.324s  (RTF: 0.32x faster)
3s audio:   0.891s  (RTF: 0.30x faster)
5s audio:   1.432s  (RTF: 0.29x faster)
10s audio:  2.734s  (RTF: 0.27x faster)

🔄 End-to-End Pipeline
────────────────────────────────────────
Transcription:  0.891s
Translation:    0.687s
Total latency:  2.028s

⚡ Throughput
────────────────────────────────────────
Sentences/min:  22.3
Per sentence:   0.694s

💾 Memory Usage
────────────────────────────────────────
Whisper:        1823.4 MB
NLLB:           2145.7 MB
Total:          4312.1 MB

🖥️  CPU Usage
────────────────────────────────────────
Average:        67.3%
Peak:           89.1%
Cores:          8

============================================================
PERFORMANCE GRADE
============================================================

Overall Grade: A
  Latency:    2.03s  ✅
  Throughput: 22.3/min  ✅
```

---

## Taking Action

### Results Show Grade A or Better → You're Good! ✅
- System is production-ready
- No optimizations needed
- Consider GPU only if you need higher throughput

### Results Show Grade B → Some Optimization Helpful ⚠️
- Try smaller models
- Reduce beam size
- Consider GPU for better performance

### Results Show Grade C → Optimization Required ❌
- Switch to smaller models immediately
- Check system resources (RAM, CPU)
- Consider GPU upgrade

---

## Saving Results

Benchmarks are saved to: `benchmark_results.json`

```json
{
  "nllb": [...],
  "whisper": [...],
  "pipeline": {...},
  "throughput": {...},
  "memory": {...},
  "cpu": {...}
}
```

Use for:
- Performance tracking over time
- A/B testing optimizations
- Capacity planning
- SLA documentation

---

## Questions to Ask

1. **Is my latency acceptable for my use case?**
   - Real-time conversation: Need <2s
   - Batch processing: Can be >5s

2. **Can my system handle expected load?**
   - Throughput × 60 = sentences per hour
   - Multiply by expected users

3. **Is memory usage sustainable?**
   - Leave 2GB free for OS
   - Multiple users = multiply memory

4. **Should I upgrade to GPU?**
   - If throughput is bottleneck: YES
   - If cost is concern: MAYBE
   - If privacy is key: Consider local GPU

---

**Run the benchmark and see how your stack performs!** 🚀
