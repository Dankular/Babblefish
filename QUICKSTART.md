# BabbleFish Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- 4GB RAM minimum (8GB+ recommended)
- ~5GB disk space for models

## Installation

### Option 1: Quick Start (Windows)

```bash
# Double-click run.bat
# OR from command line:
run.bat
```

### Option 2: Quick Start (Linux/Mac)

```bash
chmod +x run.sh
./run.sh
```

### Option 3: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup models (one-time, takes ~10 minutes)
python setup_models.py

# 5. Start the server
python main.py
```

## First Test

Once the server is running, open a new terminal:

```bash
# Test the API
python test_client.py
```

Or visit in your browser:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Quick Examples

### 1. Translate Text

```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world!",
    "source_lang": "eng_Latn",
    "target_lang": "spa_Latn"
  }'
```

### 2. Transcribe Audio

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@your_audio.mp3"
```

### 3. Transcribe + Translate

```bash
curl -X POST "http://localhost:8000/transcribe-translate" \
  -F "file=@your_audio.mp3" \
  -F "target_lang=fra_Latn"
```

## Common Language Codes

### NLLB (for translation)
- `eng_Latn` - English
- `spa_Latn` - Spanish
- `fra_Latn` - French
- `deu_Latn` - German
- `zho_Hans` - Chinese (Simplified)
- `jpn_Jpan` - Japanese
- `kor_Hang` - Korean
- `ara_Arab` - Arabic
- `rus_Cyrl` - Russian
- `hin_Deva` - Hindi

### Whisper (for transcription)
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean
- Leave blank for auto-detection

## Troubleshooting

### Models not loading?

```bash
# Re-run the setup
python setup_models.py
```

### Out of memory?

Edit `config.py`:
```python
WHISPER_MODEL_SIZE = "small"  # Use smaller model
NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"  # Use 600M instead of 1.3B
```

### Slow on CPU?

This is normal. For better performance:
1. Use smaller models (see above)
2. Use GPU if available (edit `config.py`: `DEVICE = "cuda"`)
3. Enable quantization (already default for CPU)

## Next Steps

- Read the full [README.md](README.md) for advanced configuration
- Check [config.py](config.py) for all settings
- See API documentation at http://localhost:8000/docs
- Try the interactive examples in `test_client.py`

## Docker (Alternative)

```bash
# Build
docker-compose build

# Run
docker-compose up

# Or with Docker directly
docker build -t babelfish .
docker run -p 8000:8000 -v $(pwd)/models:/app/models babelfish
```

## Need Help?

- Check the logs for error messages
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.8+)
- Make sure you have enough disk space (~5GB)

Happy translating! 🐟✨
