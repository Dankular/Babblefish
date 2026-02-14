"""
Example client for BabbleFish TTS API

Usage:
    python tts_client.py --help
"""
import argparse
import requests
from pathlib import Path


class TTSClient:
    """Simple client for TTS API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/tts"

    def check_status(self):
        """Check server status"""
        response = requests.get(f"{self.api_url}/status")
        response.raise_for_status()
        return response.json()

    def synthesize(
        self,
        text: str,
        language: str = 'en',
        output_file: str = 'output.wav',
        voice_profile: str = None,
        reference_audio: str = None,
        temperature: float = 0.7,
        speed: float = 1.0
    ):
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize
            language: Target language code
            output_file: Output WAV file path
            voice_profile: Voice profile name
            reference_audio: Path to reference audio file
            temperature: Voice variation (0.1-1.0)
            speed: Speech speed (0.5-2.0)
        """
        files = {
            'text': (None, text),
            'language': (None, language),
            'temperature': (None, str(temperature)),
            'speed': (None, str(speed))
        }

        if voice_profile:
            files['voice_profile'] = (None, voice_profile)

        if reference_audio:
            with open(reference_audio, 'rb') as f:
                files['reference_audio'] = f
                response = requests.post(f"{self.api_url}/synthesize", files=files)
        else:
            response = requests.post(f"{self.api_url}/synthesize", files=files)

        response.raise_for_status()

        # Save audio
        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"✓ Saved to: {output_file}")
        return output_file

    def transcribe(self, audio_file: str):
        """
        Transcribe audio to text

        Args:
            audio_file: Path to audio file

        Returns:
            dict with 'text', 'language', 'duration'
        """
        with open(audio_file, 'rb') as f:
            files = {'audio_file': f}
            response = requests.post(f"{self.api_url}/transcribe", files=files)

        response.raise_for_status()
        return response.json()

    def translate(self, text: str, source_lang: str, target_lang: str):
        """
        Translate text

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            dict with translation result
        """
        data = {
            'text': text,
            'source_lang': source_lang,
            'target_lang': target_lang
        }
        response = requests.post(f"{self.api_url}/translate", json=data)
        response.raise_for_status()
        return response.json()

    def process_pipeline(
        self,
        audio_file: str,
        target_language: str,
        output_file: str = 'translated_output.wav',
        voice_profile: str = None,
        temperature: float = 0.7,
        speed: float = 1.0
    ):
        """
        Full pipeline: Audio → ASR → Translation → TTS

        Args:
            audio_file: Input audio file
            target_language: Target language for output
            output_file: Output WAV file path
            voice_profile: Voice profile name
            temperature: Voice variation
            speed: Speech speed

        Returns:
            dict with metadata
        """
        files = {
            'target_language': (None, target_language),
            'temperature': (None, str(temperature)),
            'speed': (None, str(speed))
        }

        if voice_profile:
            files['voice_profile'] = (None, voice_profile)

        with open(audio_file, 'rb') as f:
            files['audio_file'] = f
            response = requests.post(f"{self.api_url}/process", files=files)

        response.raise_for_status()

        # Save audio
        with open(output_file, 'wb') as f:
            f.write(response.content)

        # Extract metadata from headers
        metadata = {
            'source_text': response.headers.get('X-Source-Text', ''),
            'source_lang': response.headers.get('X-Source-Lang', ''),
            'translated_text': response.headers.get('X-Translated-Text', ''),
            'output_file': output_file
        }

        print(f"✓ Saved to: {output_file}")
        return metadata

    def add_voice_profile(self, name: str, audio_file: str, description: str = ""):
        """
        Add voice profile

        Args:
            name: Profile name
            audio_file: Reference audio file
            description: Optional description
        """
        files = {
            'name': (None, name),
            'description': (None, description)
        }

        with open(audio_file, 'rb') as f:
            files['audio_file'] = f
            response = requests.post(f"{self.api_url}/voice-profile/add", files=files)

        response.raise_for_status()
        return response.json()

    def list_voice_profiles(self):
        """List all voice profiles"""
        response = requests.get(f"{self.api_url}/voice-profiles")
        response.raise_for_status()
        return response.json()

    def list_languages(self):
        """List supported languages"""
        response = requests.get(f"{self.api_url}/languages")
        response.raise_for_status()
        return response.json()


def main():
    parser = argparse.ArgumentParser(description="BabbleFish TTS Client")
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Status command
    subparsers.add_parser('status', help='Check server status')

    # Synthesize command
    synth = subparsers.add_parser('synthesize', help='Synthesize speech from text')
    synth.add_argument('text', help='Text to synthesize')
    synth.add_argument('--lang', default='en', help='Language code (default: en)')
    synth.add_argument('--output', default='output.wav', help='Output file')
    synth.add_argument('--voice', help='Voice profile name')
    synth.add_argument('--ref', help='Reference audio file for voice cloning')
    synth.add_argument('--temp', type=float, default=0.7, help='Temperature (0.1-1.0)')
    synth.add_argument('--speed', type=float, default=1.0, help='Speed (0.5-2.0)')

    # Transcribe command
    transcribe = subparsers.add_parser('transcribe', help='Transcribe audio to text')
    transcribe.add_argument('audio', help='Audio file to transcribe')

    # Translate command
    translate = subparsers.add_parser('translate', help='Translate text')
    translate.add_argument('text', help='Text to translate')
    translate.add_argument('--from', dest='source', required=True, help='Source language')
    translate.add_argument('--to', dest='target', required=True, help='Target language')

    # Process command
    process = subparsers.add_parser('process', help='Full pipeline: Audio → Translation → TTS')
    process.add_argument('audio', help='Input audio file')
    process.add_argument('--to', dest='target', required=True, help='Target language')
    process.add_argument('--output', default='translated.wav', help='Output file')
    process.add_argument('--voice', help='Voice profile name')

    # Voice profile commands
    add_voice = subparsers.add_parser('add-voice', help='Add voice profile')
    add_voice.add_argument('name', help='Profile name')
    add_voice.add_argument('audio', help='Reference audio file')
    add_voice.add_argument('--desc', default='', help='Description')

    subparsers.add_parser('list-voices', help='List voice profiles')
    subparsers.add_parser('list-languages', help='List supported languages')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create client
    client = TTSClient(args.url)

    try:
        if args.command == 'status':
            status = client.check_status()
            print(f"Status: {status['status']}")
            print(f"Device: {status['device']}")
            print(f"Compute Type: {status['compute_type']}")
            print(f"Languages: {len(status['supported_languages'])}")
            print(f"Voice Profiles: {len(status['voice_profiles'])}")

        elif args.command == 'synthesize':
            client.synthesize(
                args.text,
                args.lang,
                args.output,
                args.voice,
                args.ref,
                args.temp,
                args.speed
            )

        elif args.command == 'transcribe':
            result = client.transcribe(args.audio)
            print(f"Language: {result['language']}")
            print(f"Duration: {result['duration']:.2f}s")
            print(f"Text: {result['text']}")

        elif args.command == 'translate':
            result = client.translate(args.text, args.source, args.target)
            print(f"Original ({result['source_lang']}): {result['original_text']}")
            print(f"Translated ({result['target_lang']}): {result['translated_text']}")

        elif args.command == 'process':
            metadata = client.process_pipeline(
                args.audio,
                args.target,
                args.output,
                args.voice
            )
            print(f"Source ({metadata['source_lang']}): {metadata['source_text']}")
            print(f"Translated: {metadata['translated_text']}")

        elif args.command == 'add-voice':
            result = client.add_voice_profile(args.name, args.audio, args.desc)
            print(f"✓ {result['message']}")

        elif args.command == 'list-voices':
            result = client.list_voice_profiles()
            profiles = result['voice_profiles']
            if profiles:
                print(f"Voice Profiles ({len(profiles)}):")
                for profile in profiles:
                    print(f"  - {profile}")
            else:
                print("No voice profiles available")

        elif args.command == 'list-languages':
            result = client.list_languages()
            languages = result['languages']
            print(f"Supported Languages ({len(languages)}):")
            for i in range(0, len(languages), 8):
                print("  " + ", ".join(languages[i:i+8]))

    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to {args.url}")
        print("  Make sure the server is running: python server/tts_server.py")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
