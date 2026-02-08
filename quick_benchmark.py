"""
Quick BabbleFish Performance Test
Fast benchmark showing key metrics
"""

import time
import numpy as np
import psutil
import os

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*60)
print(">> BabbleFish Quick Performance Test")
print("="*60)

# Memory baseline
process = psutil.Process(os.getpid())
mem_start = process.memory_info().rss / 1024 / 1024

print("\n[1/3] Testing NLLB Translation...")
from nllb_ct2_fixed import NLLBTranslatorCT2

translator = NLLBTranslatorCT2(device="cpu", compute_type="int8")
translator.load_model()

test_sentences = [
    "Hello, how are you?",
    "The weather is beautiful today.",
    "I love programming in Python."
]

# Warm up
translator.translate(test_sentences[0], "eng_Latn", "spa_Latn")

# Benchmark
times = []
for sentence in test_sentences * 3:  # 9 total
    start = time.time()
    result = translator.translate(sentence, "eng_Latn", "spa_Latn")
    times.append(time.time() - start)

avg_time = np.mean(times)
print(f"  ✓ Average: {avg_time:.3f}s per sentence")
print(f"  ✓ Throughput: {60/avg_time:.1f} sentences/min")

mem_after_nllb = process.memory_info().rss / 1024 / 1024

print("\n[2/3] Testing Whisper Transcription...")
from faster_whisper import WhisperModel
import tempfile
import wave

whisper = WhisperModel("medium", device="cpu", compute_type="int8")

# Create 3-second test audio
sample_rate = 16000
duration = 3
samples = int(sample_rate * duration)
audio = np.random.randn(samples) * 0.01
audio = audio.astype(np.float32)

temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
audio_int16 = (audio * 32768).astype(np.int16)

with wave.open(temp_file.name, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(audio_int16.tobytes())

# Warm up
segments, info = whisper.transcribe(temp_file.name)
list(segments)

# Benchmark
times = []
for _ in range(3):
    start = time.time()
    segments, info = whisper.transcribe(temp_file.name)
    list(segments)
    times.append(time.time() - start)

try:
    temp_file.close()
    os.unlink(temp_file.name)
except:
    pass

avg_whisper = np.mean(times)
rtf = avg_whisper / duration

print(f"  ✓ Time: {avg_whisper:.3f}s for {duration}s audio")
print(f"  ✓ RTF: {rtf:.2f}x ({'faster' if rtf < 1 else 'slower'} than realtime)")

mem_end = process.memory_info().rss / 1024 / 1024

print("\n[3/3] End-to-End Pipeline...")
start = time.time()

# Create audio
samples = int(sample_rate * 3)
audio = np.random.randn(samples) * 0.01
audio = audio.astype(np.float32)
temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
audio_int16 = (audio * 32768).astype(np.int16)
with wave.open(temp_file.name, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(audio_int16.tobytes())

# Transcribe
segments, info = whisper.transcribe(temp_file.name)
transcription = " ".join([seg.text for seg in segments]) or "test"

# Translate
translation = translator.translate(transcription, "eng_Latn", "spa_Latn")

total_time = time.time() - start
try:
    temp_file.close()
    os.unlink(temp_file.name)
except:
    pass

print(f"  ✓ Total: {total_time:.3f}s (audio → text → translation)")

# Summary
print("\n" + "="*60)
print("📊 PERFORMANCE SUMMARY")
print("="*60)

print(f"\n⚡ Speed:")
print(f"  Translation:     {avg_time:.3f}s/sentence")
print(f"  Transcription:   {avg_whisper:.3f}s (RTF: {rtf:.2f}x)")
print(f"  End-to-end:      {total_time:.3f}s")
print(f"  Throughput:      {60/avg_time:.1f} sentences/min")

print(f"\n💾 Memory:")
print(f"  Whisper:         {mem_after_nllb - mem_start:.0f} MB")
print(f"  NLLB:            {mem_end - mem_after_nllb:.0f} MB")
print(f"  Total:           {mem_end:.0f} MB")

print(f"\n🖥️  System:")
print(f"  CPU Cores:       {psutil.cpu_count()}")
print(f"  CPU Usage:       {psutil.cpu_percent()}%")

# Grade
if total_time < 2:
    grade = "A+"
    emoji = "🔥"
elif total_time < 3:
    grade = "A"
    emoji = "✅"
elif total_time < 4:
    grade = "B+"
    emoji = "👍"
elif total_time < 5:
    grade = "B"
    emoji = "⚠️"
else:
    grade = "C"
    emoji = "❌"

print(f"\n🎯 Performance Grade: {grade} {emoji}")

if grade in ["A+", "A"]:
    print("  Excellent! Production-ready performance.")
elif grade == "B+":
    print("  Good performance. Consider GPU for higher load.")
elif grade == "B":
    print("  Acceptable. Try smaller models for better speed.")
else:
    print("  Slow. Check system resources or use GPU.")

print("\n" + "="*60)
print("✨ Quick benchmark complete!")
print("="*60)
