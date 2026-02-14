"""
Test script for TTS API endpoints
Tests basic functionality without requiring actual API server
"""
import sys
from pathlib import Path
import numpy as np

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from server.tts.xtts_engine import XTTSEngine
        print("✓ XTTSEngine imported")
    except Exception as e:
        print(f"✗ XTTSEngine import failed: {e}")

    try:
        from server.tts.tts_manager_v2 import TTSManagerV2
        print("✓ TTSManagerV2 imported")
    except Exception as e:
        print(f"✗ TTSManagerV2 import failed: {e}")

    try:
        from server.pipeline.asr import FasterWhisperASR
        print("✓ FasterWhisperASR imported")
    except Exception as e:
        print(f"✗ FasterWhisperASR import failed: {e}")

    try:
        from server.pipeline.translate import NLLBTranslator
        print("✓ NLLBTranslator imported")
    except Exception as e:
        print(f"✗ NLLBTranslator import failed: {e}")


def test_manager_initialization():
    """Test TTS manager initialization (without loading models)"""
    print("\nTesting TTSManagerV2 initialization...")

    try:
        from server.tts.tts_manager_v2 import TTSManagerV2

        # Initialize without loading models
        manager = TTSManagerV2(use_gpu=False)
        print("✓ TTSManagerV2 initialized")

        # Test device info before loading
        device_info = manager.get_device_info()
        print(f"  Device: {device_info['device']}")
        print(f"  Compute Type: {device_info['compute_type']}")
        print(f"  GPU Enabled: {device_info['use_gpu']}")

        # Test language support
        languages = manager.get_supported_languages()
        print(f"  Supported Languages: {len(languages)}")
        print(f"  Sample Languages: {languages[:5]}")

    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()


def test_xtts_engine():
    """Test XTTS engine initialization"""
    print("\nTesting XTTSEngine...")

    try:
        from server.tts.xtts_engine import XTTSEngine

        engine = XTTSEngine()
        print("✓ XTTSEngine created")

        # Test language mapping
        languages = engine.get_supported_languages()
        print(f"  Supported Languages: {len(languages)}")
        print(f"  Languages: {', '.join(languages[:10])}...")

        print(f"  Sample Rate: {engine.get_sample_rate()} Hz")
        print(f"  Device: {engine.get_device()}")

    except Exception as e:
        print(f"✗ XTTSEngine test failed: {e}")
        import traceback
        traceback.print_exc()


def test_configuration():
    """Test configuration loading"""
    print("\nTesting Configuration...")

    try:
        from server.config import settings

        print(f"✓ Configuration loaded")
        print(f"  Device: {settings.DEVICE}")
        print(f"  Compute Type: {settings.COMPUTE_TYPE}")
        print(f"  Whisper Model: {settings.WHISPER_MODEL_SIZE}")
        print(f"  NLLB Model: {settings.NLLB_MODEL_PATH}")
        print(f"  Host: {settings.HOST}:{settings.PORT}")

    except Exception as e:
        print(f"✗ Configuration failed: {e}")


def test_api_endpoints():
    """Test API endpoint imports"""
    print("\nTesting API Endpoints...")

    try:
        from server.api.tts_endpoint import router
        print("✓ API router imported")

        # Check routes
        routes = [route.path for route in router.routes]
        print(f"  Available endpoints ({len(routes)}):")
        for route in routes:
            print(f"    - {route}")

    except Exception as e:
        print(f"✗ API endpoints failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("=" * 60)
    print("BabbleFish TTS API - Component Tests")
    print("=" * 60)

    test_imports()
    test_configuration()
    test_manager_initialization()
    test_xtts_engine()
    test_api_endpoints()

    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)
    print("\nNote: These tests only check imports and initialization.")
    print("To fully test the system, start the server with:")
    print("  cd server && python tts_server.py")
    print("\nThen test the API at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
