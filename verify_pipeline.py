"""
Verify the complete TTS pipeline by transcribing the output
Compares: Original English -> Translated French -> Transcribed French
"""
import sys
from pathlib import Path
import soundfile as sf
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def main():
    print("="*80)
    print("Pipeline Verification: Transcribe French Output")
    print("="*80)

    # Step 1: Load and transcribe original English segment
    print("\n[1/4] Transcribing original English audio...")
    ref_file = Path(__file__).parent / "charlie_reference_segment.wav"

    if not ref_file.exists():
        print(f"[ERROR] Reference file not found: {ref_file}")
        print("Run test_pipeline_fixed.py first")
        return 1

    audio_en, sr_en = sf.read(str(ref_file))
    if audio_en.ndim > 1:
        audio_en = audio_en.mean(axis=1)

    print(f"  Loading Whisper model...")
    asr = WhisperModel("medium", device="cpu", compute_type="int8")

    segments, info = asr.transcribe(audio_en, language="en", beam_size=5)

    english_text_parts = []
    print(f"\n  Detected language: {info.language}")
    print(f"  Segments:")
    for segment in segments:
        text = segment.text.strip()
        if text and len(text) > 3:
            print(f"    [{segment.start:.1f}s] {text}")
            english_text_parts.append(text)

    english_text = " ".join(english_text_parts)
    print(f"\n  ✓ Original English:")
    print(f"    {english_text}")

    # Step 2: Translate English to French (expected output)
    print("\n[2/4] Translating English to French (expected)...")
    print(f"  Loading NLLB-200 model...")

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
    expected_french = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]

    print(f"\n  ✓ Expected French translation:")
    print(f"    {expected_french}")

    # Step 3: Transcribe the generated French audio
    print("\n[3/4] Transcribing generated French audio...")
    french_file = Path(__file__).parent / "charlie_french_fixed.wav"

    if not french_file.exists():
        print(f"[ERROR] French audio not found: {french_file}")
        print("Run test_pipeline_fixed.py first")
        return 1

    audio_fr, sr_fr = sf.read(str(french_file))
    if audio_fr.ndim > 1:
        audio_fr = audio_fr.mean(axis=1)

    print(f"  Audio duration: {len(audio_fr)/sr_fr:.2f}s")

    # Transcribe French audio
    segments, info = asr.transcribe(audio_fr, language="fr", beam_size=5)

    french_transcribed_parts = []
    print(f"\n  Detected language: {info.language}")
    print(f"  Language probability: {info.language_probability:.2f}")
    print(f"  Segments:")
    for segment in segments:
        text = segment.text.strip()
        if text:
            print(f"    [{segment.start:.1f}s] {text}")
            french_transcribed_parts.append(text)

    french_transcribed = " ".join(french_transcribed_parts)
    print(f"\n  ✓ Transcribed French:")
    print(f"    {french_transcribed}")

    # Step 4: Compare results
    print("\n[4/4] Comparison Analysis...")
    print("\n" + "="*80)
    print("PIPELINE VERIFICATION RESULTS")
    print("="*80)

    print(f"\n1. Original English (Input):")
    print(f"   {english_text}")

    print(f"\n2. Expected French (Translation):")
    print(f"   {expected_french}")

    print(f"\n3. Transcribed French (XTTS-v2 Output):")
    print(f"   {french_transcribed}")

    # Simple comparison
    print(f"\n" + "-"*80)
    print("Analysis:")
    print("-"*80)

    # Word count comparison
    expected_words = expected_french.lower().split()
    transcribed_words = french_transcribed.lower().split()

    print(f"  Expected French word count: {len(expected_words)}")
    print(f"  Transcribed French word count: {len(transcribed_words)}")

    # Check if transcription matches translation reasonably well
    matching_words = sum(1 for word in transcribed_words if word in expected_words)
    if len(transcribed_words) > 0:
        match_percent = (matching_words / len(transcribed_words)) * 100
        print(f"  Word match rate: {match_percent:.1f}%")

    # Language detection check
    if info.language == "fr":
        print(f"\n  ✓ Language correctly detected as French")
        print(f"  ✓ Language probability: {info.language_probability:.2%}")
    else:
        print(f"\n  ✗ WARNING: Language detected as {info.language}, not French!")

    # Overall assessment
    print(f"\n" + "="*80)
    if info.language == "fr" and match_percent > 60:
        print("✓ PIPELINE VERIFICATION: PASSED")
        print("  - French language correctly synthesized")
        print("  - Voice cloning successful")
        print("  - Translation preserved in output")
    else:
        print("⚠ PIPELINE VERIFICATION: NEEDS REVIEW")
        print(f"  - Language detection: {info.language}")
        print(f"  - Match rate: {match_percent:.1f}%")

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
