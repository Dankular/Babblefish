"""
Simple NLLB test - check if model works at all
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import ctranslate2
from transformers import NllbTokenizer

# Load
model_path = "./models/nllb-ct2"
orig_path = "./cache/models--facebook--nllb-200-distilled-1.3B/snapshots/7be3e24664b38ce1cac29b8aeed6911aa0cf0576"

translator = ctranslate2.Translator(model_path, device="cpu", compute_type="int8")
tokenizer = NllbTokenizer.from_pretrained(orig_path)

# Check language tokens
print(f"spa_Latn token: {tokenizer.convert_tokens_to_ids('spa_Latn')}")
print(f"eng_Latn token: {tokenizer.convert_tokens_to_ids('eng_Latn')}")
print()

# Try simple translation without language prefixes
text = "Hello world"
tokenizer.src_lang = "eng_Latn"
tokenizer.tgt_lang = "spa_Latn"

# Encode properly for NLLB
inputs = tokenizer(text, return_tensors=None)
token_ids = inputs['input_ids']

print(f"Token IDs: {token_ids}")
tokens = [tokenizer.convert_ids_to_tokens([tid])[0] for tid in token_ids]
print(f"Tokens: {tokens}")
print()

# Try translating with token IDs as strings
tokens_as_strings = [str(tid) for tid in token_ids]
print(f"As strings: {tokens_as_strings[:10]}")

result = translator.translate_batch(
    [tokens_as_strings],
    beam_size=1
)

output = result[0].hypotheses[0]
print(f"Output: {output[:20]}")
