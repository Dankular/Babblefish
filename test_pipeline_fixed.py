"""
Full TTS Pipeline with proper audio segment extraction
Extracts clear speech segments and translates to French
"""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from faster_whisper import WhisperModel

sys.path.insert(0, str(Path(__file__).parent))
from server.tts.xtts_engine import XTTSEngine


def extract_speech_segment(audio, sr, start_sec, end_sec):
    """Extract a specific time segment from audio"""
    start_sample = int(start_sec * sr)
    end_sample = int(end_sec * sr)
    return audio[start_sample:end_sample]


def main():
    print("="*80)
    print("Full TTS Pipeline: ASR -> Translation -> TTS with Voice Cloning")
    print("Using clear speech segment")
    print("="*80)

    # Load test audio
    print("\n[1/6] Loading test audio...")
    audio_file = Path(__file__).parent / "test_charlie.mp3"

    if not audio_file.exists():
        print(f"[ERROR] Audio not found. Download it first:")
        print('  curl -L "https://l1w5.c18.e2-1.dev/data/charlie.mp3" -o test_charlie.mp3')
        return 1

    audio, sr = sf.read(str(audio_file))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)

    print(f"[OK] Loaded full audio: {len(audio) / sr:.2f}s")

    # Extract clear speech segment (avoiding music intro)
    # Testing different segments to find clear speech
    speech_segment = extract_speech_segment(audio, sr, 20, 35)  # 20-35 seconds

    print(f"[OK] Extracted speech segment: {len(speech_segment) / sr:.2f}s")

    # Initialize ASR
    print("\n[2/6] Loading ASR (faster-whisper medium)...")
    asr = WhisperModel("medium", device="cpu", compute_type="int8")
    print("[OK] ASR loaded")

    # Transcribe
    print("\n[3/6] Transcribing speech segment...")
    segments, info = asr.transcribe(speech_segment, language="en", beam_size=5)

    text_parts = []
    print("Segments found:")
    for segment in segments:
        segment_text = segment.text.strip()
        if segment_text and len(segment_text) > 3:  # Skip very short segments
            print(f"  [{segment.start:.1f}s] {segment_text}")
            text_parts.append(segment_text)

    text = " ".join(text_parts)

    print(f"\n[OK] Detected language: {info.language}")
    print(f"[OK] Combined transcription: {text}")

    if not text or len(text) < 10:
        print("[ERROR] Insufficient speech detected, trying different segment...")
        # Try segment 60-75
        speech_segment = extract_speech_segment(audio, sr, 60, 75)
        print(f"[OK] Trying segment 60-75s: {len(speech_segment) / sr:.2f}s")

        segments, info = asr.transcribe(speech_segment, language="en", beam_size=5)
        text_parts = []
        for segment in segments:
            segment_text = segment.text.strip()
            if segment_text and len(segment_text) > 3:
                print(f"  [{segment.start:.1f}s] {segment_text}")
                text_parts.append(segment_text)

        text = " ".join(text_parts)
        print(f"[OK] Combined transcription: {text}")

    if not text or len(text) < 10:
        print("[ERROR] No clear speech found")
        return 1

    # Initialize translation
    print("\n[4/6] Loading NLLB-200 translation model...")
    print("  Note: First run will download ~1.2GB model")

    tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")

    print("[OK] Translation model loaded")

    # Translate
    print("\n[5/6] Translating English -> French...")
    tokenizer.src_lang = "eng_Latn"

    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
    translated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids("fra_Latn"),
        max_length=512,
        num_beams=5
    )
    translated_text = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]

    print(f"[OK] Translated: {translated_text}")

    # Initialize XTTS-v2
    print("\n[6/6] Loading XTTS-v2 and synthesizing with voice cloning...")
    print("  Note: First run will download ~2GB model")

    xtts = XTTSEngine()
    xtts.load(use_gpu=torch.cuda.is_available())
    print(f"[OK] XTTS-v2 loaded on {xtts.get_device()}")

    # Resample reference audio to 24kHz (use speech segment as reference)
    import librosa
    ref_audio_24k = librosa.resample(speech_segment, orig_sr=sr, target_sr=24000)

    print(f"  Synthesizing French with cloned voice...")
    print(f"  Reference audio: {len(ref_audio_24k)} samples ({len(ref_audio_24k)/24000:.2f}s)")

    synthesized = xtts.synthesize(
        text=translated_text,
        language="fr",
        reference_audio=ref_audio_24k,
        temperature=0.7,
        speed=1.0
    )

    # Save output
    output_file = Path(__file__).parent / "charlie_french_fixed.wav"
    sf.write(str(output_file), synthesized, 24000)

    # Also save reference segment for comparison
    ref_file = Path(__file__).parent / "charlie_reference_segment.wav"
    sf.write(str(ref_file), speech_segment, sr)

    # Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"\nSource Language: {info.language}")
    print(f"Source Text: {text}")
    print(f"\nTarget Language: fr (French)")
    print(f"Translated Text: {translated_text}")
    print(f"\nGenerated Audio: {len(synthesized)} samples ({len(synthesized)/24000:.2f}s)")
    print(f"\n[OK] Saved synthesized French to: {output_file}")
    print(f"[OK] Saved reference segment to: {ref_file}")
    print("\n" + "="*80)
    print("Pipeline Test Complete!")
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
