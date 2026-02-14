"""
Test the complete TTS pipeline with Charlie audio
Demonstrates: Audio → ASR → Translation → TTS with voice cloning
"""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))

from server.tts.tts_manager_v2 import TTSManagerV2


def main():
    print("=" * 80)
    print("Testing TTS Pipeline: Audio → ASR → Translation → TTS")
    print("=" * 80)

    # Initialize TTS Manager
    print("\n[1/4] Initializing TTS Manager...")
    print("Note: First run will download models (~5GB total)")
    print("      This may take several minutes...")

    manager = TTSManagerV2(use_gpu=True, compute_type="int8")

    # Load all models
    print("\n[2/4] Loading Models...")
    manager.load()

    # Load test audio
    print("\n[3/4] Loading Test Audio...")
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

    # Run full pipeline
    print("\n[4/4] Running Full Pipeline: English → French")
    print("-" * 80)

    target_language = "fr"  # French

    synthesized_audio, metadata = manager.process_audio(
        audio=audio,
        target_language=target_language,
        sample_rate=sample_rate,
        temperature=0.7,
        speed=1.0
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nSource Language: {metadata['source_lang']}")
    print(f"Source Text: '{metadata['source_text']}'")
    print(f"\nTarget Language: {target_language}")
    print(f"Translated Text: '{metadata['translated_text']}'")
    print(f"\nGenerated Audio: {len(synthesized_audio)} samples ({len(synthesized_audio) / 24000:.2f}s)")

    # Save output
    output_file = Path(__file__).parent / "charlie_french_cloned.wav"
    sf.write(str(output_file), synthesized_audio, 24000)
    print(f"\n✓ Saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Pipeline Test Complete!")
    print("=" * 80)

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
