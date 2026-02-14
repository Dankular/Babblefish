"""
Simple XTTS-v2 test without translation
Just tests: ASR -> TTS with voice cloning
"""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent))

from server.tts.xtts_engine import XTTSEngine
from server.pipeline.asr import FasterWhisperASR


def main():
    print("="*80)
    print("XTTS-v2 Voice Cloning Test")
    print("="*80)

    # Load test audio
    print("\n[1/5] Loading test audio...")
    audio_file = Path(__file__).parent / "test_charlie.mp3"

    if not audio_file.exists():
        print(f"[ERROR] Audio file not found: {audio_file}")
        return 1

    audio, sample_rate = sf.read(str(audio_file))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)

    print(f"[OK] Loaded: {audio_file.name}")
    print(f"  Duration: {len(audio) / sample_rate:.2f}s")

    # Initialize ASR
    print("\n[2/5] Loading ASR (faster-whisper)...")
    asr = FasterWhisperASR(device="cpu", compute_type="int8")
    asr.load()
    print("[OK] ASR loaded")

    # Transcribe
    print("\n[3/5] Transcribing audio...")
    text, detected_lang = asr.transcribe(audio, sample_rate)
    print(f"[OK] Detected language: {detected_lang}")
    print(f"[OK] Text: {text[:200]}")

    if not text.strip():
        print("[ERROR] No speech detected")
        return 1

    # Initialize XTTS-v2
    print("\n[4/5] Loading XTTS-v2...")
    print("  Note: First run will download ~2GB model")
    xtts = XTTSEngine()
    xtts.load(use_gpu=True)
    print(f"[OK] XTTS-v2 loaded on {xtts.get_device()}")

    # Synthesize French with voice cloning
    print("\n[5/5] Synthesizing French speech with voice cloning...")

    # Resample reference audio to 24kHz
    import librosa
    ref_audio_24k = librosa.resample(audio, orig_sr=sample_rate, target_sr=24000)

    # Translate text manually for demo (just a simple example)
    french_text = "Bonjour, je suis Charlie. Comment allez-vous aujourd'hui?"

    print(f"  Text: {french_text}")
    print(f"  Using reference audio: {len(ref_audio_24k)} samples")

    synthesized = xtts.synthesize(
        text=french_text,
        language="fr",
        reference_audio=ref_audio_24k,
        temperature=0.7,
        speed=1.0
    )

    # Save output
    output_file = Path(__file__).parent / "charlie_french_xtts.wav"
    sf.write(str(output_file), synthesized, 24000)

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"\nOriginal language: {detected_lang}")
    print(f"Original text: {text[:100]}...")
    print(f"\nSynthesized language: fr (French)")
    print(f"Synthesized text: {french_text}")
    print(f"\nGenerated audio: {len(synthesized)} samples ({len(synthesized)/24000:.2f}s)")
    print(f"\n[OK] Saved to: {output_file}")
    print("\n" + "="*80)
    print("Test Complete!")
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
