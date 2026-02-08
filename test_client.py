"""
Simple test client for BabbleFish API

Usage examples for all endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_translation():
    """Test text translation"""
    print("\n=== Testing Translation ===")

    data = {
        "text": "Hello, how are you today?",
        "source_lang": "eng_Latn",
        "target_lang": "spa_Latn"
    }

    response = requests.post(f"{BASE_URL}/translate", json=data)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_transcription(audio_file: str):
    """Test audio transcription"""
    print("\n=== Testing Transcription ===")

    with open(audio_file, 'rb') as f:
        files = {'file': f}
        data = {'language': 'en'}
        response = requests.post(f"{BASE_URL}/transcribe", files=files, data=data)

    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_transcribe_translate(audio_file: str):
    """Test transcription + translation"""
    print("\n=== Testing Transcribe + Translate ===")

    with open(audio_file, 'rb') as f:
        files = {'file': f}
        data = {'target_lang': 'fra_Latn'}
        response = requests.post(f"{BASE_URL}/transcribe-translate", files=files, data=data)

    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_languages():
    """Test supported languages endpoint"""
    print("\n=== Testing Supported Languages ===")
    response = requests.get(f"{BASE_URL}/languages")
    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"\nWhisper languages: {len(data['whisper_languages'])} languages")
    print(f"NLLB languages: {len(data['nllb_languages'])} languages")
    print("\nFirst 10 NLLB languages:")
    print(data['nllb_languages'][:10])

def main():
    """Run all tests"""
    print("BabbleFish API Test Client")
    print("=" * 60)

    try:
        # Test health
        test_health()

        # Test languages
        test_languages()

        # Test translation
        test_translation()

        # Test transcription (if you have an audio file)
        # Uncomment and provide path to test
        # test_transcription("path/to/audio.mp3")
        # test_transcribe_translate("path/to/audio.mp3")

        print("\n" + "=" * 60)
        print("All tests completed!")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
