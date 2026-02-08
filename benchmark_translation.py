"""
Benchmark: Transformers vs CTranslate2 for NLLB
"""
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from nllb_transformers import NLLBTransformerTranslator
from nllb_ct2_fixed import NLLBTranslatorCT2

test_texts = [
    "Hello, how are you?",
    "The weather is beautiful today",
    "I love programming in Python",
    "Artificial intelligence is transforming the world",
    "This is a longer sentence to test translation performance with more tokens and complexity"
]

print("=" * 60)
print("NLLB Translation Benchmark")
print("=" * 60)
print()

# Test Transformers version
print("[1/2] Testing Transformers (current)...")
t1 = NLLBTransformerTranslator(device="cpu")
t1.load_model()

start = time.time()
for text in test_texts:
    result = t1.translate(text, "eng_Latn", "spa_Latn")
transformers_time = time.time() - start

print(f"Time: {transformers_time:.2f}s")
print()

# Test CT2 version
print("[2/2] Testing CTranslate2 (optimized)...")
t2 = NLLBTranslatorCT2(device="cpu", compute_type="int8")
t2.load_model()

start = time.time()
for text in test_texts:
    result = t2.translate(text, "eng_Latn", "spa_Latn")
ct2_time = time.time() - start

print(f"Time: {ct2_time:.2f}s")
print()

# Results
print("=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Transformers:  {transformers_time:.2f}s")
print(f"CTranslate2:   {ct2_time:.2f}s")
print(f"Speedup:       {transformers_time/ct2_time:.2f}x faster")
print(f"Time saved:    {transformers_time - ct2_time:.2f}s ({(1 - ct2_time/transformers_time)*100:.1f}%)")
print()

# Per-sentence
print(f"Per sentence:")
print(f"  Transformers: {transformers_time/len(test_texts):.3f}s")
print(f"  CTranslate2:  {ct2_time/len(test_texts):.3f}s")
print("=" * 60)
