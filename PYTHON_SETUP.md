# Python Environment Setup for XTTS-v2

XTTS-v2 (Coqui TTS) requires **Python 3.9, 3.10, or 3.11** (not 3.12+).

## Option 1: Using Conda (Recommended)

```bash
# Create Python 3.11 environment
conda create -n babblefish python=3.11 -y
conda activate babblefish

# Install dependencies
pip install -r server/requirements.txt

# Test installation
python test_pipeline.py
```

## Option 2: Using pyenv (Linux/Mac)

```bash
# Install Python 3.11
pyenv install 3.11.9
pyenv local 3.11.9

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r server/requirements.txt

# Test installation
python test_pipeline.py
```

## Option 3: System Python 3.11

### Windows

1. Download Python 3.11 from [python.org](https://www.python.org/downloads/)
2. Install to custom location (e.g., `C:\Python311`)
3. Create virtual environment:

```bash
C:\Python311\python.exe -m venv venv
venv\Scripts\activate
pip install -r server/requirements.txt
```

### Linux/Mac

```bash
# Install Python 3.11 via package manager
sudo apt install python3.11 python3.11-venv  # Ubuntu/Debian
# or
brew install python@3.11  # macOS

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt
```

## Current Python Version Check

```bash
python --version
# Should show: Python 3.9.x, 3.10.x, or 3.11.x
```

## Alternative: Use Existing Chatterbox TTS

If you can't change Python version, the existing Chatterbox TTS already works:

```bash
# Test with Chatterbox (works on Python 3.13)
python test_pipeline_existing.py
```

This uses:
- ✅ faster-whisper ASR (works on all Python versions)
- ✅ NLLB-200 Translation (works on all Python versions)
- ✅ Chatterbox ONNX TTS with voice cloning (works on all Python versions)

**Note**: XTTS-v2 has better voice cloning quality, but Chatterbox is still very capable.

## Verifying Installation

```bash
# Check all imports work
python test_tts_api.py

# Run full pipeline test
python test_pipeline.py  # XTTS-v2 (requires Python 3.9-3.11)
# or
python test_pipeline_existing.py  # Chatterbox (works on any Python)
```

## Running the Server

```bash
# Activate environment
conda activate babblefish  # or: source venv/bin/activate

# Start server
cd server
python tts_server.py
```

Access the API at: http://localhost:8000/docs
