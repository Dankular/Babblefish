"""
Proper NLLB to CTranslate2 conversion
Based on official CT2 documentation for NLLB models
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("NLLB CTranslate2 Conversion Fix")
print("=" * 60)
print()

# Check if model exists
original_model = "./cache/models--facebook--nllb-200-distilled-1.3B/snapshots/7be3e24664b38ce1cac29b8aeed6911aa0cf0576"
output_dir = "./models/nllb-ct2-fixed"

if not os.path.exists(original_model):
    print("Error: Original model not found!")
    print(f"Expected at: {original_model}")
    sys.exit(1)

# Create output directory
os.makedirs(output_dir, exist_ok=True)

print(f"Source model: {original_model}")
print(f"Output directory: {output_dir}")
print()

# The issue: NLLB models need special handling in CT2
# They use a different tokenizer setup than standard seq2seq models

print("Converting NLLB model with proper settings...")
print()

# Import converter
try:
    import ctranslate2
    from ctranslate2.converters import TransformersConverter
except ImportError as e:
    print(f"Error importing ctranslate2: {e}")
    print("Make sure ctranslate2 and transformers are installed")
    sys.exit(1)

# Convert with proper NLLB settings
# Key: Use TransformersConverter directly with proper vocab handling
try:
    converter = TransformersConverter(
        original_model,
        load_as_float16=False,  # We'll quantize to int8 after
        copy_files=["sentencepiece.bpe.model", "tokenizer_config.json"]
    )

    print("Starting conversion...")
    converter.convert(
        output_dir,
        vmap=None,  # Let it auto-detect vocabulary
        quantization="int8",
        force=True
    )

    print()
    print("[OK] Conversion completed!")
    print()

    # Verify files
    print("Checking output files...")
    required_files = ["model.bin", "config.json"]
    for f in required_files:
        path = os.path.join(output_dir, f)
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024*1024)
            print(f"  ✓ {f} ({size:.1f} MB)")
        else:
            print(f"  ✗ {f} MISSING")

    # Check for tokenizer
    tokenizer_files = ["sentencepiece.bpe.model", "tokenizer_config.json", "shared_vocabulary.json", "shared_vocabulary.txt"]
    print()
    print("Tokenizer files:")
    for f in tokenizer_files:
        path = os.path.join(output_dir, f)
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024*1024)
            print(f"  ✓ {f} ({size:.1f} MB)")

    print()
    print("=" * 60)
    print("Conversion complete!")
    print("=" * 60)

except Exception as e:
    print(f"Error during conversion: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
