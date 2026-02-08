"""
Working NLLB translation using direct sentencepiece + shared vocab
Based on CT2 NLLB examples
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import ctranslate2
import sentencepiece as spm
import json

# Load CT2 model
model_path = "./models/nllb-ct2"
translator = ctranslate2.Translator(model_path, device="cpu", compute_type="int8")

# Load sentencepiece
tokenizer = spm.SentencePieceProcessor()
tokenizer.load(f"{model_path}/sentencepiece.model")

# Load shared vocabulary
with open(f"{model_path}/shared_vocabulary.json", 'r', encoding='utf-8') as f:
    vocab = json.load(f)

print(f"Vocabulary size: {len(vocab)}")
print(f"First few tokens: {vocab[:5]}")
print(f"Last few tokens: {vocab[-5:]}")
print()

# Find language tokens in vocab
eng_idx = vocab.index("eng_Latn") if "eng_Latn" in vocab else -1
spa_idx = vocab.index("spa_Latn") if "spa_Latn" in vocab else -1
print(f"eng_Latn index in shared vocab: {eng_idx}")
print(f"spa_Latn index in shared vocab: {spa_idx}")
print()

# Test input
text = "Hello world"

# Encode with sentencepiece
pieces = tokenizer.encode_as_pieces(text)
print(f"SP pieces: {pieces}")
print()

# For NLLB with CT2, we need to use the shared vocabulary tokens
# Add language code at start
source_tokens = ["eng_Latn"] + pieces

print(f"Source tokens: {source_tokens}")
print()

# Translate with target language prefix
result = translator.translate_batch(
    [source_tokens],
    target_prefix=[["spa_Latn"]],
    beam_size=4,
    max_decoding_length=50
)

output_tokens = result[0].hypotheses[0]
print(f"Output tokens: {output_tokens}")
print()

# Decode - skip language token
if output_tokens[0] in ["spa_Latn", "eng_Latn"]:
    output_tokens = output_tokens[1:]

translation = tokenizer.decode_pieces(output_tokens)
print(f"Translation: {translation}")
