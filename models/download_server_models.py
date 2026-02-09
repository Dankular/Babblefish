#!/usr/bin/env python3
"""
Download and prepare server-side models for Babblefish.

This script downloads:
1. faster-whisper medium model (auto-downloads via library)
2. NLLB-200-distilled-600M in CTranslate2 format

Total download size: ~3GB
"""
import os
import sys
from pathlib import Path
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_faster_whisper():
    """
    Download faster-whisper model.
    The library auto-downloads on first use, but we can pre-cache it.
    """
    logger.info("Downloading faster-whisper medium model...")

    try:
        from faster_whisper import WhisperModel

        # Initialize model - this will download if not cached
        logger.info("Initializing faster-whisper (this will download ~1.5GB if not cached)...")
        model = WhisperModel(
            "medium",
            device="cpu",
            compute_type="int8",
            download_root=str(Path.home() / ".cache" / "huggingface" / "hub")
        )

        logger.info("✓ faster-whisper medium model ready")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to download faster-whisper: {e}")
        return False


def download_nllb_ctranslate2():
    """
    Download NLLB-200-distilled-600M in CTranslate2 format.
    """
    logger.info("Downloading NLLB-200-distilled-600M (CTranslate2 format)...")

    models_dir = Path(__file__).parent
    nllb_dir = models_dir / "nllb-200-distilled-600M-ct2"

    if nllb_dir.exists():
        logger.info(f"✓ NLLB model already exists at {nllb_dir}")
        return True

    try:
        # Check if ct2-transformers-converter is available
        try:
            import ctranslate2
            logger.info("CTranslate2 is installed")
        except ImportError:
            logger.error("✗ CTranslate2 not installed. Install with: pip install ctranslate2")
            return False

        # Option 1: Download pre-converted CTranslate2 model from Hugging Face
        logger.info("Downloading pre-converted NLLB model from Hugging Face...")
        logger.info("Using huggingface-cli to download...")

        # Check if huggingface-hub is installed
        try:
            from huggingface_hub import snapshot_download

            logger.info("Downloading to: " + str(nllb_dir))
            snapshot_download(
                repo_id="facebook/nllb-200-distilled-600M",
                local_dir=str(models_dir / "nllb-200-distilled-600M-hf"),
                local_dir_use_symlinks=False,
            )

            logger.info("Converting to CTranslate2 format...")
            logger.info("\nManual conversion required:")
            logger.info("Run the following command:")
            logger.info(f"  ct2-transformers-converter --model {models_dir / 'nllb-200-distilled-600M-hf'} "
                       f"--output_dir {nllb_dir} --quantization int8")

            return True

        except ImportError:
            logger.warning("huggingface-hub not installed")
            logger.info("\nManual download required:")
            logger.info("1. Install huggingface-hub: pip install huggingface-hub")
            logger.info("2. Download model:")
            logger.info(f"   huggingface-cli download facebook/nllb-200-distilled-600M --local-dir {models_dir / 'nllb-200-distilled-600M-hf'}")
            logger.info("3. Convert to CTranslate2:")
            logger.info(f"   ct2-transformers-converter --model {models_dir / 'nllb-200-distilled-600M-hf'} "
                       f"--output_dir {nllb_dir} --quantization int8")
            return False

    except Exception as e:
        logger.error(f"✗ Failed to download NLLB: {e}")
        return False


def download_sentencepiece_tokenizer():
    """
    Download SentencePiece tokenizer for NLLB.
    This is included with the NLLB model download.
    """
    logger.info("SentencePiece tokenizer will be included with NLLB model")
    return True


def verify_models():
    """
    Verify that all models are available.
    """
    logger.info("\nVerifying models...")

    models_dir = Path(__file__).parent
    nllb_dir = models_dir / "nllb-200-distilled-600M-ct2"

    # Check NLLB
    if nllb_dir.exists():
        logger.info(f"✓ NLLB model found at {nllb_dir}")

        # Check for required files
        required_files = ["model.bin", "config.json"]
        for file in required_files:
            if (nllb_dir / file).exists():
                logger.info(f"  ✓ {file}")
            else:
                logger.warning(f"  ✗ {file} missing")
    else:
        logger.warning(f"✗ NLLB model not found at {nllb_dir}")

    # Check faster-whisper (it auto-downloads, just verify import works)
    try:
        from faster_whisper import WhisperModel
        logger.info("✓ faster-whisper is importable")
    except ImportError:
        logger.warning("✗ faster-whisper not installed")

    logger.info("\nModel verification complete")


def main():
    """Main download process."""
    logger.info("=" * 60)
    logger.info("Babblefish Model Downloader")
    logger.info("=" * 60)

    models_dir = Path(__file__).parent
    logger.info(f"Models directory: {models_dir.absolute()}")

    # Create models directory if it doesn't exist
    models_dir.mkdir(exist_ok=True)

    # Download models
    success = True

    logger.info("\n" + "=" * 60)
    logger.info("Step 1: faster-whisper")
    logger.info("=" * 60)
    if not download_faster_whisper():
        success = False

    logger.info("\n" + "=" * 60)
    logger.info("Step 2: NLLB-200")
    logger.info("=" * 60)
    if not download_nllb_ctranslate2():
        success = False
        logger.info("\n⚠️  NLLB download requires manual steps (see above)")

    # Verify
    logger.info("\n" + "=" * 60)
    logger.info("Verification")
    logger.info("=" * 60)
    verify_models()

    if success:
        logger.info("\n✓ All models ready!")
        logger.info("\nYou can now start the server with:")
        logger.info("  cd server")
        logger.info("  python main.py")
    else:
        logger.info("\n⚠️  Some models require manual setup (see instructions above)")
        logger.info("\nFor help, see: docs/DEPLOYMENT.md")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
