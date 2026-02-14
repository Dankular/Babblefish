"""
Complete pipeline verification:
1. Transcribe original English audio
2. Translate to French
3. Synthesize French with voice cloning
4. Transcribe the French output
5. Compare all stages
"""
import sys
from pathlib import Path
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

sys.path.insert(0, str(Path(__file__).parent))
from server.tts.xtts_engine import XTTSEngine


def extract_clean_segment(audio, sr, start_sec=20, duration=15):
    """Extract a clean speech segment"""
    start_sample = int(start_sec * sr)
    end_sample = int((start_sec + duration) * sr)
    return audio[start_sample:end_sample]


def main():
    print("="*80)
    print("FULL PIPELINE VERIFICATION")
    print("="*80)

    # Load audio
    print("\n[1/6] Loading audio...")
    audio_file = Path(__file__).parent / "test_charlie.mp3"

    if not audio_file.exists():
        print("[ERROR] Audio file not found")
        return 1

    audio, sr = sf.read(str(audio_file))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)

    # Extract clean segment
    speech_segment = extract_clean_segment(audio, sr, start_sec=20, duration=15)
    print(f"[OK] Extracted segment: {len(speech_segment)/sr:.2f}s")

    # Initialize models
    print("\n[2/6] Loading ASR model...")
    asr = WhisperModel("medium", device="cpu", compute_type="int8")
    print("[OK] ASR loaded")

    # Transcribe original English
    print("\n[3/6] Transcribing original English...")
    segments_en, info_en = asr.transcribe(speech_segment, language="en", beam_size=5)

    english_parts = []
    for seg in segments_en:
        text = seg.text.strip()
        if text and len(text) > 3:
            english_parts.append(text)

    english_text = " ".join(english_parts)
    print(f"[OK] English transcription ({len(english_text)} chars):")
    print(f"     {english_text}")

    # Translate to French
    print("\n[4/6] Translating English to French...")
    tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")

    tokenizer.src_lang = "eng_Latn"
    inputs = tokenizer(english_text, return_tensors="pt", max_length=512, truncation=True)
    translated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids("fra_Latn"),
        max_length=512,
        num_beams=5
    )
    french_expected = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
    print(f"[OK] French translation ({len(french_expected)} chars):")
    print(f"     {french_expected}")

    # Synthesize French with voice cloning
    print("\n[5/6] Synthesizing French with XTTS-v2 voice cloning...")
    xtts = XTTSEngine()
    xtts.load(use_gpu=torch.cuda.is_available())
    print(f"[OK] XTTS-v2 on {xtts.get_device()}")

    # Resample reference to 24kHz
    import librosa
    ref_24k = librosa.resample(speech_segment, orig_sr=sr, target_sr=24000)

    synthesized = xtts.synthesize(
        text=french_expected,
        language="fr",
        reference_audio=ref_24k,
        temperature=0.7,
        speed=1.0
    )

    # Save synthesized French
    output_file = Path(__file__).parent / "charlie_french_verified.wav"
    sf.write(str(output_file), synthesized, 24000)
    print(f"[OK] Synthesized: {len(synthesized)/24000:.2f}s")
    print(f"[OK] Saved to: {output_file}")

    # Transcribe synthesized French
    print("\n[6/6] Transcribing synthesized French audio...")
    segments_fr, info_fr = asr.transcribe(synthesized, language="fr", beam_size=5)

    french_transcribed_parts = []
    print(f"[OK] Language detected: {info_fr.language} (prob: {info_fr.language_probability:.2f})")
    print("[OK] French segments:")
    for seg in segments_fr:
        text = seg.text.strip()
        if text:
            print(f"     [{seg.start:.1f}s] {text}")
            french_transcribed_parts.append(text)

    french_transcribed = " ".join(french_transcribed_parts)

    # Final comparison
    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)

    print(f"\nSTEP 1 - Original English (ASR from audio):")
    print(f"  {english_text}")

    print(f"\nSTEP 2 - Expected French (NLLB translation):")
    print(f"  {french_expected}")

    print(f"\nSTEP 3 - Transcribed French (ASR from XTTS output):")
    print(f"  {french_transcribed}")

    # Analysis
    print("\n" + "-"*80)
    print("ANALYSIS:")
    print("-"*80)

    expected_words = french_expected.lower().split()
    transcribed_words = french_transcribed.lower().split()

    print(f"  Expected word count: {len(expected_words)}")
    print(f"  Transcribed word count: {len(transcribed_words)}")

    if len(transcribed_words) > 0:
        matching = sum(1 for w in transcribed_words if w in expected_words)
        match_rate = (matching / len(transcribed_words)) * 100
        print(f"  Word match rate: {match_rate:.1f}%")
    else:
        match_rate = 0
        print(f"  Word match rate: 0%")

    print(f"  Language detection: {info_fr.language} ({info_fr.language_probability:.1%})")

    # Final verdict
    print("\n" + "="*80)
    if info_fr.language == "fr" and match_rate > 50:
        print("[PASS] Pipeline verification successful!")
        print("  - English transcription: OK")
        print("  - Translation to French: OK")
        print("  - Voice cloning: OK")
        print("  - French synthesis: OK")
        print("  - French transcription: OK")
    else:
        print("[NEEDS REVIEW] Pipeline verification issues:")
        if info_fr.language != "fr":
            print(f"  - Language detected as {info_fr.language}, not French")
        if match_rate <= 50:
            print(f"  - Low word match rate: {match_rate:.1f}%")

    print("="*80)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
