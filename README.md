# BabbleFish - Real-Time Multi-Speaker Translation

Three-tier progressive TTS system for real-time conversations.

## Quick Start

### Server (128-core machine)
```bash
pip install -r requirements_server.txt
huggingface-cli login  # Accept pyannote terms
python server_cpu.py   # Port 9000
```

### Laptop TTS Accelerator (3050 GPU - optional)
```bash
pip install chatterbox-tts
python laptop_tts_accelerator.py --strategy both --model multilingual
```

### Clients (phones/browsers)
Open `client_thin.html` and configure server URL.

## Architecture

```
📱 Phones → 🖥 Server (SeamlessM4T + Kokoro) → 💻 Laptop (Chatterbox Multilingual + F5-TTS)

Tier 1: Kokoro                  ~2.0s | 5 langs  | Server CPU
Tier 2: Chatterbox Multilingual ~2.3s | 23 langs | Laptop GPU (1.5GB)
Tier 3: F5-TTS                  ~2.8s | Any lang | Laptop GPU (2.5GB)
```

## Components

- **Server:** SeamlessM4T (ASR+MT), Kokoro TTS, Pyannote speaker ID
- **Laptop:** Chatterbox Multilingual (23 langs, zero-shot cloning), F5-TTS (voice cloning)
- **Clients:** Thin (mic + playback only)

## Resources

- Server: 60/128 cores (~47%), ~5GB RAM
- Laptop: 4GB VRAM (perfect for 3050)
- Clients: <10% CPU, GPU free

## Files

- `server_cpu.py` - Main server
- `laptop_tts_accelerator.py` - Optional TTS accelerator
- `client_thin.html` - Browser client
- `requirements_server.txt` - Dependencies

## Strategy Options

```bash
# Chatterbox Multilingual only (23 languages, fast)
python laptop_tts_accelerator.py --strategy chatterbox --model multilingual

# Both Chatterbox Multilingual + F5-TTS (recommended)
python laptop_tts_accelerator.py --strategy both --model multilingual

# Use Turbo variant (faster, experimental)
python laptop_tts_accelerator.py --strategy both --model turbo
```

## License

MIT
