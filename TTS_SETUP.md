# BabbleFish TTS Setup Guide

## Overview

The TTS-enabled BabbleFish system adds text-to-speech output to your real-time translations with passive speaker voice training.

**Features:**
- 🎵 **Kokoro TTS** - Fast, high-quality TTS (default for English)
- 🎭 **F5-TTS Voice Cloning** - Passive learning from your speech
- 📊 **Training Progress** - Real-time stats on voice training
- 🔊 **Audio Playback** - Automatic TTS audio in browser

## Installation

### 1. Install TTS Dependencies

```bash
pip install -r requirements_tts.txt
```

This installs:
- `kokoro-onnx` - Fast ONNX-based Kokoro TTS
- `F5-TTS` - Voice cloning engine
- `soundfile`, `librosa` - Audio processing
- `faiss-cpu` - Vector search for speaker embeddings

### 2. Verify Installation

Test the TTS engine:

```bash
python tts_engine.py
```

Expected output:
```
Loading Kokoro TTS (kokoro-v0.19)...
[OK] Kokoro TTS loaded
[TTS Engine] Ready
Generated 24000 samples
Saved to test_tts.wav
```

## Running the TTS Server

### Start Server

```bash
python realtime_server_tts.py
```

Server runs on `http://localhost:8002`

### Access Client

Open browser to: `http://localhost:8002`

Or directly open: `realtime_client_tts.html`

## How It Works

### 1. **Kokoro TTS (Default)**

When you translate to English:
- Translation appears instantly
- Kokoro TTS generates speech (fast, ~100ms)
- Audio plays automatically in browser

### 2. **Passive Speaker Training**

As you speak:
- Audio chunks are saved to `./speaker_data/`
- Metadata stored in `metadata.json`
- Progress tracked (need 50 chunks minimum)

### 3. **Voice Cloning (F5-TTS)**

Once 50+ chunks collected:
- "Your Voice" option becomes available
- Click to switch from Kokoro to trained voice
- F5-TTS uses your collected samples

### 4. **Training Progress UI**

Browser shows:
- Chunks collected: `X / 50 chunks`
- Total duration recorded
- Progress bar (0-100%)
- Ready indicator when trainable

## WebSocket Parameters

```
ws://localhost:8002/ws/realtime?target_lang=eng_Latn&enable_tts=true&use_trained_voice=false
```

**Parameters:**
- `target_lang` - Translation target (e.g., `eng_Latn`, `spa_Latn`)
- `enable_tts` - Enable/disable TTS (`true`/`false`)
- `use_trained_voice` - Use F5-TTS trained voice (`true`/`false`)

## File Structure

```
BabbleFish/
├── realtime_server_tts.py      # WebSocket server with TTS
├── realtime_client_tts.html    # Browser client with audio
├── tts_engine.py               # TTS + training engine
├── speaker_data/               # Collected audio chunks
│   ├── chunk_*.wav            # Audio files
│   └── metadata.json          # Training metadata
└── requirements_tts.txt        # TTS dependencies
```

## Usage Tips

### For Best TTS Quality

1. **Kokoro Voice Selection**
   - Default: `af_sky` (female)
   - Options: `am_adam` (male), `af_bella`, `am_michael`
   - Edit in `tts_engine.py` line 54

2. **Speaker Training**
   - Speak clearly and naturally
   - Need 50+ chunks (3-10 seconds each)
   - System collects passively as you use it
   - Total ~2-5 minutes of speech needed

3. **English Only for TTS**
   - TTS only works when `target_lang=eng_Latn`
   - Other languages show translation but no audio
   - (Future: Add multilingual TTS support)

### Training Status

Check training stats via API:

```bash
curl http://localhost:8002/training/stats
```

Response:
```json
{
  "total_chunks": 45,
  "total_duration": 180.5,
  "min_chunks_needed": 50,
  "ready_to_train": false,
  "progress": 90
}
```

### Manual Training Trigger

```bash
curl -X POST http://localhost:8002/training/start
```

## Comparison: Servers

### Port 8001 - Original Real-Time Server
- No TTS
- Lighter weight
- Lower latency
- Good for text-only translation

### Port 8002 - TTS Server (This One)
- Text-to-Speech output
- Passive voice training
- Audio playback
- Best for full experience

## Troubleshooting

### No Audio Playing

**Check:**
1. Browser allows audio playback (click page first)
2. `enable_tts=true` in WebSocket URL
3. Target language is English (`eng_Latn`)
4. Volume is up in browser

### Kokoro Not Loading

**Error:** `[WARNING] Kokoro not installed`

**Fix:**
```bash
pip install kokoro-onnx
```

### Training Not Starting

**Check:**
- Need minimum 50 chunks
- Chunks must be 1-10 seconds each
- View progress in browser UI

### F5-TTS Training (Placeholder)

**Note:** F5-TTS training is currently a placeholder. Full implementation requires:
1. F5-TTS model loading
2. Fine-tuning pipeline
3. Voice checkpoint saving

## Performance

**Expected Latency:**
- Transcription (Whisper): ~1-3s
- Translation (NLLB): ~0.5s
- TTS (Kokoro): ~0.1s
- **Total:** ~2-4s end-to-end

**Memory Usage:**
- Base system: ~2GB
- + Kokoro: +200MB
- + F5-TTS: +500MB (when training)

## Next Steps

1. ✅ Start server: `python realtime_server_tts.py`
2. ✅ Open browser: `http://localhost:8002`
3. ✅ Allow microphone access
4. ✅ Select English as target language
5. ✅ Enable TTS
6. ✅ Start speaking!

Your voice will be passively collected and after 50 chunks, you can switch to your trained voice.

## API Endpoints

### GET /
Serve client HTML

### WebSocket /ws/realtime
Real-time audio streaming with TTS

### GET /training/stats
Get speaker training statistics

### POST /training/start
Manually trigger F5-TTS training

---

**Enjoy real-time translation with your own voice! 🐟🎤**
