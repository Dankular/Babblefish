# Babblefish Deployment Guide

This guide covers deploying Babblefish without Docker on various platforms.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Production Deployment](#production-deployment)
5. [Troubleshooting](#troubleshooting)
6. [Performance Tuning](#performance-tuning)

---

## System Requirements

### Minimum Requirements

**Server**:
- **OS**: Linux, macOS, or Windows
- **CPU**: 4 cores (8 recommended)
- **RAM**: 8 GB (4 GB for models + 4 GB for OS/app)
- **Storage**: 10 GB free space
- **Network**: Stable internet for model downloads

**Client**:
- **Browser**: Chrome 121+, Safari 26+, Firefox 141+, or Edge 121+
- **Device**: Any phone, tablet, or computer with microphone
- **Network**: WiFi or cellular (LAN recommended for lowest latency)

### Recommended Requirements (Production)

**Server**:
- **CPU**: 8-16 cores (128 cores is luxury, scales linearly)
- **RAM**: 16 GB
- **Storage**: 50 GB (for logs, temporary files)
- **Network**: 1 Gbps connection
- **OS**: Linux (Ubuntu 22.04 LTS recommended)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git

### 1. Clone Repository

```bash
git clone https://github.com/Dankular/Babblefish.git
cd Babblefish
```

### 2. Server Setup

```bash
cd server

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download models (~3GB, one-time)
cd ../models
python download_server_models.py
cd ../server

# Run server
python main.py
```

Server starts at: `http://localhost:8000`

### 3. Client Setup

```bash
# In a new terminal
cd client

# Install dependencies
npm install

# Run development server
npm run dev
```

Client starts at: `http://localhost:3000`

### 4. Test

1. Open `http://localhost:3000` in 2 browser tabs
2. Tab 1: Name "Alice", Language "English", Room "TEST"
3. Tab 2: Name "Bob", Language "Spanish", Room "TEST"
4. Alice speaks → Bob sees Spanish translation
5. Bob speaks → Alice sees English translation

---

## Detailed Setup

### Server Setup (Step by Step)

#### 1. Install Python 3.11+

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**macOS**:
```bash
brew install python@3.11
```

**Windows**:
Download from https://www.python.org/downloads/

#### 2. Install System Dependencies

**Ubuntu/Debian**:
```bash
sudo apt install build-essential libsndfile1 ffmpeg
```

**macOS**:
```bash
brew install libsndfile ffmpeg
```

**Windows**:
- Install Visual C++ Build Tools
- ffmpeg: Download from https://ffmpeg.org/

#### 3. Set Up Virtual Environment

```bash
cd server
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

#### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies installed**:
- FastAPI + Uvicorn (web server)
- faster-whisper (ASR)
- CTranslate2 (model inference)
- sentencepiece (tokenizer)
- numpy, soundfile, librosa (audio processing)
- opuslib (Opus codec)
- pydantic (data validation)

#### 5. Download Models

```bash
cd ../models
python download_server_models.py
```

**What this does**:
1. Downloads faster-whisper medium (~1.5 GB) to cache
2. Provides instructions for NLLB download (~1.2 GB)

**Manual NLLB Setup** (if script fails):

```bash
# Install Hugging Face CLI
pip install huggingface-hub

# Download model
huggingface-cli download facebook/nllb-200-distilled-600M \
  --local-dir models/nllb-200-distilled-600M-hf

# Convert to CTranslate2 (requires ~4GB RAM)
pip install ctranslate2
ct2-transformers-converter \
  --model models/nllb-200-distilled-600M-hf \
  --output_dir models/nllb-200-distilled-600M-ct2 \
  --quantization int8
```

#### 6. Configure Server

Create `.env` file in `server/` directory:

```bash
# Server settings
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Model paths
MODELS_DIR=../models
WHISPER_MODEL_SIZE=medium
NLLB_MODEL_PATH=../models/nllb-200-distilled-600M-ct2

# Device settings (cpu or cuda)
DEVICE=cpu
COMPUTE_TYPE=int8

# Room settings
MAX_PARTICIPANTS_PER_ROOM=10
MAX_ROOMS=100
ROOM_TIMEOUT_SECONDS=3600
```

#### 7. Run Server

**Development**:
```bash
cd server
python main.py
```

**Production** (with Gunicorn):
```bash
pip install gunicorn
gunicorn server.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

**As systemd service** (Linux):

Create `/etc/systemd/system/babblefish.service`:

```ini
[Unit]
Description=Babblefish Translation Server
After=network.target

[Service]
Type=simple
User=babblefish
WorkingDirectory=/opt/Babblefish/server
Environment="PATH=/opt/Babblefish/server/venv/bin"
ExecStart=/opt/Babblefish/server/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable babblefish
sudo systemctl start babblefish
sudo systemctl status babblefish
```

---

### Client Setup (Step by Step)

#### 1. Install Node.js 20+

**Ubuntu/Debian**:
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

**macOS**:
```bash
brew install node@20
```

**Windows**:
Download from https://nodejs.org/

#### 2. Install Dependencies

```bash
cd client
npm install
```

**Dependencies installed**:
- React 19 + React DOM
- onnxruntime-web (Silero VAD)
- Tailwind CSS (styling)
- Vite (build tool)

#### 3. Configure Client

Update `client/vite.config.js` if server is not on localhost:

```javascript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/ws': {
        target: 'ws://your-server-ip:8000',  // Change this
        ws: true,
      },
    },
  },
  // ...
})
```

Or update WebSocket URL in `client/src/pages/RoomPage.jsx`:

```javascript
const { status, messages, send } = useWebSocket(
  `ws://your-server-ip:8000/ws/client`  // Change this
)
```

#### 4. Run Client

**Development**:
```bash
npm run dev
```

Access at: `http://localhost:3000`

**Production Build**:
```bash
npm run build
```

This creates `client/dist/` with optimized static files.

**Serve Production Build**:

With static file server:
```bash
npm install -g serve
serve -s dist -p 3000
```

With nginx (recommended):

Create `/etc/nginx/sites-available/babblefish`:

```nginx
server {
    listen 80;
    server_name babblefish.example.com;

    root /opt/Babblefish/client/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

Enable and reload:
```bash
sudo ln -s /etc/nginx/sites-available/babblefish /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Production Deployment

### Security Checklist

- [ ] Use HTTPS (Let's Encrypt recommended)
- [ ] Configure firewall (allow 80, 443, deny 8000 from external)
- [ ] Set up authentication (future feature)
- [ ] Enable rate limiting
- [ ] Use strong CORS policy
- [ ] Keep dependencies updated
- [ ] Monitor logs for abuse
- [ ] Set up automated backups

### HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d babblefish.example.com
```

### Firewall Configuration

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to server
sudo ufw enable
```

### Monitoring

**Install Prometheus + Grafana** (optional):

```bash
# FastAPI metrics
pip install prometheus-fastapi-instrumentator

# Add to server/main.py
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

**Basic Logging**:

Server logs to stdout. Redirect to file:

```bash
python main.py > logs/babblefish.log 2>&1
```

Or use systemd journal:
```bash
sudo journalctl -u babblefish -f
```

---

## Troubleshooting

### Server Issues

#### Error: "faster-whisper model not found"

**Solution**:
```bash
cd models
python download_server_models.py
```

Or manually:
```bash
python -c "from faster_whisper import WhisperModel; WhisperModel('medium')"
```

#### Error: "NLLB model not found"

**Solution**: Follow manual NLLB setup (see Detailed Setup section)

Check path in `.env`:
```bash
NLLB_MODEL_PATH=../models/nllb-200-distilled-600M-ct2
```

#### Server crashes with "Out of memory"

**Solutions**:
1. Use smaller Whisper model: `WHISPER_MODEL_SIZE=small`
2. Increase system swap: `sudo swapon --show`
3. Add more RAM
4. Limit concurrent rooms: `MAX_ROOMS=10`

#### WebSocket connection refused

**Check**:
1. Server is running: `curl http://localhost:8000/health`
2. Firewall allows port 8000
3. CORS settings in `server/main.py`

### Client Issues

#### Error: "Failed to load ONNX model"

**Solution**: Check browser console for specific error

Common causes:
- Browser doesn't support WebAssembly
- Network blocked CDN (jsdelivr.net)
- Use local VAD model instead (download to `client/public/`)

#### Microphone access denied

**Solutions**:
1. Grant microphone permissions in browser
2. Use HTTPS (required on modern browsers)
3. Check browser settings → Privacy → Microphone

#### No audio/translations appearing

**Debugging**:
1. Open browser DevTools → Network → WS
2. Check WebSocket messages
3. Verify server logs show "Transcribed" messages
4. Test with simple phrase like "hello"

---

## Performance Tuning

### Server Optimization

**CPU-bound workload**:
- Use all available cores
- faster-whisper auto-uses multiple threads
- Run one server process per machine

**Memory optimization**:
- Use int8 quantization (already configured)
- Limit max rooms and participants
- Clean up idle rooms (auto-enabled)

**Network optimization**:
- Deploy server geographically close to users
- Use CDN for client static files
- Enable gzip compression in nginx

### Client Optimization

**Reduce bundle size**:
- Lazy load TTS models (Phase 2/3)
- Use code splitting
- Enable production build optimizations

**Audio optimization**:
- Use 16kHz sample rate (configured)
- Adjust VAD thresholds for noise environment
- Compress audio with Opus (configured)

### Scaling

**Horizontal scaling** (multiple servers):
- Use Redis for shared room state (future)
- Load balancer with sticky sessions
- WebSocket support in load balancer

**Vertical scaling** (bigger server):
- Linear scaling up to ~64 cores
- Diminishing returns beyond 64 cores
- More RAM = more concurrent users

---

## Next Steps

After successful deployment:

1. **Test thoroughly**: Try different languages, accents, noise levels
2. **Monitor usage**: Track rooms, participants, errors
3. **Plan Phase 2**: Add Kokoro TTS for audio output
4. **Plan Phase 3**: Add F5-TTS for voice cloning
5. **Get feedback**: Share with users, iterate

---

## Support

- **Issues**: https://github.com/Dankular/Babblefish/issues
- **Docs**: This repository
- **Email**: dan@khosa.co

---

## License

MIT License - See LICENSE file for details
