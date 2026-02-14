"""
Test the complete pipeline with existing models (Chatterbox + ASR + Translation)
Demonstrates: Audio → ASR → Translation → TTS with voice cloning

Note: XTTS-v2 requires Python 3.9-3.11. This test uses the existing Chatterbox TTS.
For XTTS-v2, use Python 3.9-3.11 environment.
"""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))

from server.pipeline.asr import FasterWhisperASR
from server.pipeline.translate import NLLBTranslator
from server.tts.chatterbox_onnx import ChatterboxONNX


def main():
    print("=" * 80)
    print("Testing TTS Pipeline: Audio → ASR → Translation → TTS")
    print("Using: faster-whisper (ASR) + NLLB-200 (Translation) + Chatterbox (TTS)")
    print("=" * 80)

    # Load test audio
    print("\n[1/5] Loading Test Audio...")
    audio_file = Path(__file__).parent / "test_charlie.mp3"

    if not audio_file.exists():
        print(f"✗ Audio file not found: {audio_file}")
        print("  Download it first:")
        print('  curl -L "https://l1w5.c18.e2-1.dev/data/charlie.mp3" -o test_charlie.mp3')
        return 1

    # Load audio
    audio, sample_rate = sf.read(str(audio_file))

    # Convert to mono if stereo
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    audio = audio.astype(np.float32)

    print(f"✓ Loaded: {audio_file.name}")
    print(f"  Duration: {len(audio) / sample_rate:.2f}s")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Shape: {audio.shape}")

    # Initialize ASR
    print("\n[2/5] Loading ASR (faster-whisper)...")
    asr = FasterWhisperASR(device="cpu", compute_type="int8")
    asr.load()
    print("✓ ASR loaded")

    # Initialize Translation
    print("\n[3/5] Loading Translation (NLLB-200)...")
    translator = NLLBTranslator(device="cpu")
    translator.load()
    print("✓ Translator loaded")

    # Initialize TTS
    print("\n[4/5] Loading TTS (Chatterbox)...")
    tts = ChatterboxONNX()
    tts.load(use_gpu=False)
    print("✓ TTS loaded")

    # Run pipeline
    print("\n[5/5] Running Pipeline...")
    print("-" * 80)

    # Step 1: ASR
    print("\nStep 1: Transcribing audio...")
    text, detected_lang = asr.transcribe(audio, sample_rate)
    print(f"✓ Detected language: {detected_lang}")
    print(f"✓ Transcribed text: '{text[:200]}...'")

    if not text.strip():
        print("✗ No speech detected")
        return 1

    # Step 2: Translation
    target_lang = "fr"  # French
    print(f"\nStep 2: Translating {detected_lang} → {target_lang}...")
    translated_text = translator.translate(text, detected_lang, target_lang)
    print(f"✓ Translated: '{translated_text[:200]}...'")

    # Step 3: TTS with voice cloning
    print(f"\nStep 3: Synthesizing French speech with voice cloning...")

    # Use original audio as reference for voice cloning
    # Resample to 24kHz for Chatterbox
    import librosa
    reference_audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=24000)

    synthesized_audio = tts.synthesize(
        text=translated_text,
        language=target_lang,
        reference_audio=reference_audio,
        exaggeration=0.5
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nSource Language: {detected_lang}")
    print(f"Source Text: '{text}'")
    print(f"\nTarget Language: {target_lang}")
    print(f"Translated Text: '{translated_text}'")
    print(f"\nGenerated Audio: {len(synthesized_audio)} samples ({len(synthesized_audio) / 24000:.2f}s)")

    # Save output
    output_file = Path(__file__).parent / "charlie_french_output.wav"
    sf.write(str(output_file), synthesized_audio, 24000)
    print(f"\n✓ Saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Pipeline Test Complete!")
    print("=" * 80)
    print("\nNote: For XTTS-v2 with better voice cloning, use Python 3.9-3.11")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
