"""
Direct NLLB translation test using transformers tokenizer
"""

import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import ctranslate2
from transformers import NllbTokenizer

# Load model
model_path = "./models/nllb-ct2"
original_model_path = "./cache/models--facebook--nllb-200-distilled-1.3B/snapshots/7be3e24664b38ce1cac29b8aeed6911aa0cf0576"

translator = ctranslate2.Translator(model_path, device="cpu", compute_type="int8")

# Load tokenizer using transformers
tokenizer = NllbTokenizer.from_pretrained(original_model_path)

# Test input
text = "Hello, how are you?"
source_lang = "eng_Latn"
target_lang = "spa_Latn"

print(f"Input: {text}")
print(f"Source: {source_lang} -> Target: {target_lang}")
print()

# Set source language
tokenizer.src_lang = source_lang

# Encode using transformers tokenizer - returns list of token strings
encoded = tokenizer(text, return_tensors=None, add_special_tokens=False)
tokens = tokenizer.convert_ids_to_tokens(encoded['input_ids'])

print(f"Encoded tokens: {tokens}")
print()

# Translate
result = translator.translate_batch(
    [tokens],
    beam_size=4,
    target_prefix=[[tokenizer.convert_tokens_to_string([target_lang])]],
    max_decoding_length=100
)

print(f"Number of results: {len(result)}")
print()

# Get output
output_tokens = result[0].hypotheses[0]
print(f"Output tokens ({len(output_tokens)}): {output_tokens[:20]}")
print()

# Convert tokens to text
translation = tokenizer.convert_tokens_to_string(output_tokens)
print(f"Final translation: {translation}")
