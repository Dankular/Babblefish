"""
Model setup and conversion script

This script downloads and converts models to CTranslate2 format
Run this once before starting the API server
"""

import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download

def setup_nllb_model(output_dir: str = "./models/nllb-ct2"):
    """
    Download and convert NLLB model to CTranslate2 format

    This requires: pip install ctranslate2 transformers sentencepiece
    """
    print("Setting up NLLB-200 model...")

    # Download model from HuggingFace
    model_name = "facebook/nllb-200-distilled-1.3B"
    print(f"Downloading {model_name}...")

    model_path = snapshot_download(
        repo_id=model_name,
        cache_dir="./cache"
    )

    print(f"Model downloaded to: {model_path}")

    # Convert to CTranslate2
    print("Converting to CTranslate2 format...")
    print("Running ct2-transformers-converter...")

    os.makedirs(output_dir, exist_ok=True)

    # Use the ct2-transformers-converter command
    cmd = f'ct2-transformers-converter --model {model_path} --output_dir {output_dir} --quantization int8'

    print(f"Running: {cmd}")
    result = os.system(cmd)

    if result == 0:
        print(f"✓ NLLB model successfully converted to {output_dir}")
    else:
        print("✗ Conversion failed. Please install: pip install ctranslate2 transformers")
        sys.exit(1)

def setup_whisper_model(model_size: str = "medium"):
    """
    Download Whisper model

    faster-whisper will download models automatically on first use
    But we can pre-download them
    """
    print(f"Setting up Whisper {model_size} model...")

    from faster_whisper import WhisperModel

    # This will download the model if not present
    print("Downloading Whisper model (first run only)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"✓ Whisper {model_size} model ready")

def main():
    """Setup all models"""
    print("=" * 60)
    print("BabbleFish Model Setup")
    print("=" * 60)

    # Create directories
    os.makedirs("./models", exist_ok=True)
    os.makedirs("./cache", exist_ok=True)

    # Setup Whisper (easier, no conversion needed)
    print("\n[1/2] Setting up Whisper...")
    try:
        setup_whisper_model("medium")
    except Exception as e:
        print(f"Error setting up Whisper: {e}")

    # Setup NLLB (requires conversion)
    print("\n[2/2] Setting up NLLB...")
    try:
        setup_nllb_model("./models/nllb-ct2")
    except Exception as e:
        print(f"Error setting up NLLB: {e}")
        print("\nManual conversion required:")
        print("1. Install: pip install ctranslate2 transformers sentencepiece")
        print("2. Run: ct2-transformers-converter --model facebook/nllb-200-distilled-1.3B \\")
        print("           --output_dir ./models/nllb-ct2 --quantization int8")

    print("\n" + "=" * 60)
    print("Setup complete! You can now run: python main.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
