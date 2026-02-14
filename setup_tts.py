"""
Setup script for BabbleFish TTS Server
Downloads and configures all required models
"""
import os
import sys
from pathlib import Path
import subprocess
import shutil


def check_python_version():
    """Check Python version >= 3.8"""
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher required")
        print(f"  Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]}")


def check_cuda():
    """Check CUDA availability"""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"  VRAM: {vram:.2f} GB")
            return True
        else:
            print("⚠ CUDA not available - will use CPU")
            return False
    except ImportError:
        print("⚠ PyTorch not installed yet")
        return False


def install_requirements():
    """Install Python requirements"""
    print("\nInstalling requirements...")
    req_file = Path(__file__).parent / "server" / "requirements.txt"

    if not req_file.exists():
        print(f"✗ Requirements file not found: {req_file}")
        return False

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True
        )
        print("✓ Requirements installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False


def setup_env_file():
    """Create .env file from example"""
    print("\nSetting up environment configuration...")

    env_file = Path(__file__).parent / "server" / ".env"
    example_file = Path(__file__).parent / "server" / ".env.example"

    if env_file.exists():
        print(f"✓ .env file already exists")
        return True

    if not example_file.exists():
        print(f"✗ .env.example not found")
        return False

    # Copy example to .env
    shutil.copy(example_file, env_file)
    print(f"✓ Created .env from .env.example")

    # Auto-detect GPU and update .env
    try:
        import torch
        if torch.cuda.is_available():
            print("  Configuring for GPU acceleration...")
            # Read .env
            with open(env_file, 'r') as f:
                content = f.read()

            # Update DEVICE to cuda
            content = content.replace('DEVICE=cuda', 'DEVICE=cuda')
            content = content.replace('DEVICE=cpu', 'DEVICE=cuda')

            # Write back
            with open(env_file, 'w') as f:
                f.write(content)

            print("  ✓ GPU acceleration enabled in .env")
        else:
            print("  CPU-only configuration (GPU not available)")
    except:
        pass

    return True


def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")

    dirs = [
        "models",
        "models/xtts",
        "models/whisper",
        "models/nllb",
        "server/api",
        "examples"
    ]

    for dir_path in dirs:
        path = Path(__file__).parent / dir_path
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}")

    return True


def test_imports():
    """Test that key modules can be imported"""
    print("\nTesting imports...")

    modules = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("TTS", "Coqui TTS"),
        ("faster_whisper", "faster-whisper"),
        ("ctranslate2", "CTranslate2"),
        ("fastapi", "FastAPI"),
        ("soundfile", "soundfile"),
        ("numpy", "NumPy")
    ]

    all_ok = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name}")
        except ImportError:
            print(f"  ✗ {display_name} not found")
            all_ok = False

    return all_ok


def print_next_steps():
    """Print next steps for user"""
    print("\n" + "=" * 70)
    print("Setup Complete!")
    print("=" * 70)

    print("\n📝 Next Steps:")
    print("\n1. Review configuration:")
    print("   Edit server/.env to customize settings")

    print("\n2. Start the TTS server:")
    print("   cd server && python tts_server.py")

    print("\n3. Test the API:")
    print("   Open http://localhost:8000/docs in your browser")

    print("\n4. Try the example client:")
    print("   python examples/tts_client.py status")
    print("   python examples/tts_client.py synthesize \"Hello world\" --lang en")

    print("\n📚 Documentation:")
    print("   See TTS_README.md for full API documentation")

    print("\n" + "=" * 70)


def main():
    """Run setup"""
    print("=" * 70)
    print("BabbleFish TTS Server - Setup")
    print("=" * 70)

    # Check Python version
    check_python_version()

    # Install requirements
    if not install_requirements():
        print("\n✗ Setup failed during package installation")
        return 1

    # Check CUDA after installation
    has_cuda = check_cuda()

    # Setup environment
    if not setup_env_file():
        print("\n✗ Setup failed during environment configuration")
        return 1

    # Create directories
    if not create_directories():
        print("\n✗ Setup failed during directory creation")
        return 1

    # Test imports
    if not test_imports():
        print("\n⚠ Some imports failed - check requirements installation")

    # Print next steps
    print_next_steps()

    return 0


if __name__ == "__main__":
    sys.exit(main())
