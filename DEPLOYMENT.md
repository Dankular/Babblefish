# BabbleFish Deployment Guide

## Quick Start (5 minutes)

### Server Setup (One-time)

```bash
# 1. Clone/copy project to server
scp -r BabbleFish/ user@server:/path/to/

# 2. SSH to server
ssh user@server

# 3. Navigate to project
cd /path/to/BabbleFish

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 5. Install dependencies
pip install -r requirements_server.txt

# 6. Authenticate with Hugging Face (for pyannote)
pip install huggingface_hub
huggingface-cli login
# Enter your HF token

# 7. Accept model terms
# Visit: https://huggingface.co/pyannote/embedding
# Click: "Agree and access repository"

# 8. Test server
python server_cpu.py
# Should see: [OK] Server ready for clients
```

### Client Setup (Instant)

```bash
# On laptop or phone:
# 1. Open browser
# 2. Navigate to: file:///path/to/BabbleFish/client_thin.html
# 3. Or open the file directly

# Configure:
# - Server URL: ws://YOUR-SERVER-IP:9000/ws/client
# - Your name: Dan
# - Target language: English

# Click microphone and speak!
```

## Production Deployment

### Server (Systemd Service)

Create `/etc/systemd/system/babelfish.service`:

```ini
[Unit]
Description=BabbleFish CPU Translation Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/BabbleFish
Environment="PATH=/path/to/BabbleFish/venv/bin"
ExecStart=/path/to/BabbleFish/venv/bin/python server_cpu.py
Restart=always
RestartSec=10

# Resource limits
CPUQuota=70%      # Max 70% of all cores
MemoryLimit=8G    # Max 8GB RAM

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable babelfish
sudo systemctl start babelfish

# Check status
sudo systemctl status babelfish

# View logs
sudo journalctl -u babelfish -f
```

### Firewall Configuration

```bash
# Allow port 9000
sudo ufw allow 9000/tcp

# Or iptables
sudo iptables -A INPUT -p tcp --dport 9000 -j ACCEPT
```

### Nginx Reverse Proxy (Optional)

If you want to use standard ports (80/443):

```nginx
server {
    listen 80;
    server_name babelfish.local;

    location /ws/ {
        proxy_pass http://localhost:9000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:9000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then clients connect to: `ws://babelfish.local/ws/client`

## Network Configuration

### LAN Deployment (Recommended)

**Scenario:** Server and clients on same local network

```
Server:      192.168.1.100:9000
Dan's phone: 192.168.1.101 → ws://192.168.1.100:9000/ws/client
Marek phone: 192.168.1.102 → ws://192.168.1.100:9000/ws/client
```

**Pros:**
- Low latency
- No internet required
- Secure (LAN only)

**Cons:**
- Limited to same network
- No remote access

### Internet Deployment (Advanced)

**Scenario:** Server accessible from internet

```
Server:   babelfish.yourdomain.com (port 9000)
Clients:  Connect from anywhere
```

**Requirements:**
1. Static IP or dynamic DNS
2. Port forwarding on router
3. SSL/TLS encryption (WSS)
4. Authentication tokens

**Security:**
- Use WSS (WebSocket Secure)
- Implement client authentication
- Rate limiting
- Firewall rules

## Client Distribution

### Mobile Devices (iOS/Android)

**Option 1: Progressive Web App (PWA)**

Add to `client_thin.html`:

```html
<link rel="manifest" href="manifest.json">

<!-- manifest.json -->
{
  "name": "BabbleFish Translator",
  "short_name": "BabbleFish",
  "start_url": ".",
  "display": "standalone",
  "icons": [{
    "src": "icon.png",
    "sizes": "192x192",
    "type": "image/png"
  }]
}
```

Users can "Add to Home Screen" for app-like experience.

**Option 2: Web Server**

Host client on simple HTTP server:

```bash
# Python HTTP server
cd /path/to/BabbleFish
python3 -m http.server 8080

# Access from phone browser
# http://server-ip:8080/client_thin.html
```

**Option 3: Native App (Future)**

Wrap client in React Native or Flutter app.

### Desktop Clients

**Option 1: Browser (Easiest)**

Just open `client_thin.html` in Chrome/Firefox/Safari

**Option 2: Electron App (Future)**

Package as standalone desktop application.

## Monitoring

### Server Health

```bash
# CPU usage
htop
# Look for python process, should be <60% total

# Memory usage
free -h
# BabbleFish should use ~5-6GB

# Network connections
netstat -an | grep 9000
# Should show ESTABLISHED connections for each client
```

### Server Logs

```bash
# Real-time logs
sudo journalctl -u babelfish -f

# Last 100 lines
sudo journalctl -u babelfish -n 100

# Errors only
sudo journalctl -u babelfish -p err
```

### Performance Metrics

Add to server:

```python
import psutil
import time

@app.get("/metrics")
async def metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        "clients": len(multi_client_handler.clients),
        "uptime_seconds": time.time() - start_time
    }
```

Access: `http://server:9000/metrics`

## Troubleshooting

### Server won't start

**Error:** `ModuleNotFoundError: No module named 'transformers'`

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements_server.txt
```

**Error:** `You need to accept the model's terms`

**Solution:**
```bash
# Login to Hugging Face
huggingface-cli login

# Visit and accept terms
# https://huggingface.co/pyannote/embedding
```

**Error:** `Address already in use`

**Solution:**
```bash
# Kill existing process on port 9000
lsof -ti:9000 | xargs kill -9

# Or change port in server_cpu.py
```

### Client can't connect

**Error:** `WebSocket connection failed`

**Solutions:**

1. Check server IP:
   ```bash
   # On server
   ip addr show  # Linux
   ipconfig      # Windows
   ```

2. Check firewall:
   ```bash
   sudo ufw status
   # Should allow port 9000
   ```

3. Test connection:
   ```bash
   # From client machine
   telnet server-ip 9000
   # Should connect
   ```

4. Check server logs:
   ```bash
   sudo journalctl -u babelfish -f
   # Should show connection attempts
   ```

### High latency (>3s)

**Symptoms:**
- Translations taking too long
- Users experiencing delays

**Solutions:**

1. Check CPU usage:
   ```bash
   htop
   # Should be <70%, if higher:
   # - Reduce concurrent clients
   # - Check for other processes
   ```

2. Check thread allocation:
   ```python
   # In server_cpu.py
   torch.set_num_threads(32)  # Increase if available
   ```

3. Use lighter model:
   ```python
   # Change in server_cpu.py
   model_name = "facebook/seamless-m4t-medium"  # Instead of large
   ```

4. Profile server:
   ```python
   import cProfile
   cProfile.run('process_audio()')
   ```

### Audio not playing on client

**Symptoms:**
- Transcription shows but no audio
- Console shows audio errors

**Solutions:**

1. Check browser permissions:
   - Allow audio playback
   - User must interact with page first

2. Check audio format:
   ```javascript
   // In client_thin.html
   console.log('Audio format:', audioBuffer);
   ```

3. Test with simple audio:
   ```javascript
   // Play test tone
   const audioContext = new AudioContext();
   const oscillator = audioContext.createOscillator();
   oscillator.connect(audioContext.destination);
   oscillator.start();
   ```

## Backup & Recovery

### Server Data

**What to backup:**
- Speaker embeddings: `speaker_metadata` dict
- Configuration: `server_cpu.py` settings
- Client list: `clients` dict (optional, recreated)

**Backup script:**

```python
import json
import time

def backup_server_state():
    state = {
        "timestamp": time.time(),
        "speakers": speaker_diarization.speaker_metadata,
        "known_embeddings": {
            sid: emb.tolist()
            for sid, emb in speaker_diarization.known_speakers.items()
        }
    }

    with open(f"backup_{int(time.time())}.json", "w") as f:
        json.dump(state, f)
```

**Restore:**

```python
def restore_server_state(backup_file):
    with open(backup_file, "r") as f:
        state = json.load(f)

    speaker_diarization.speaker_metadata = state["speakers"]
    speaker_diarization.known_speakers = {
        sid: np.array(emb)
        for sid, emb in state["known_embeddings"].items()
    }
```

### Disaster Recovery

**Server failure:**

1. Check logs: `sudo journalctl -u babelfish -n 100`
2. Restart service: `sudo systemctl restart babelfish`
3. If persistent, restore from backup
4. Notify clients to reconnect

**Model corruption:**

1. Remove cached models: `rm -rf ~/.cache/huggingface`
2. Reinstall: `pip install --force-reinstall transformers`
3. Restart server

## Scaling

### Vertical Scaling (More powerful server)

Current: 2×64-core CPUs
Upgrade: 4×64-core CPUs (256 cores total)

**Benefits:**
- 2× concurrent capacity
- ~100 clients supported
- Lower latency

**Changes needed:**
```python
torch.set_num_threads(64)  # Increase from 32
```

### Horizontal Scaling (Multiple servers)

**Architecture:**

```
Load Balancer (Nginx)
      ├─ Server 1 (192.168.1.100:9000)
      ├─ Server 2 (192.168.1.101:9000)
      └─ Server 3 (192.168.1.102:9000)
```

**Nginx config:**

```nginx
upstream babelfish {
    least_conn;
    server 192.168.1.100:9000;
    server 192.168.1.101:9000;
    server 192.168.1.102:9000;
}

server {
    location /ws/ {
        proxy_pass http://babelfish/ws/;
        # ... WebSocket config
    }
}
```

**Challenges:**
- Speaker embeddings not shared across servers
- Solution: Shared Redis cache for embeddings

## Cost Estimation

### Hardware (One-time)

- Server: 2×64-core CPUs, 256GB RAM - $5,000-10,000
- Network switch (gigabit) - $100
- Total: ~$10,000

### Operating Costs (Monthly)

- Electricity (server running 24/7):
  - 300W × 24h × 30d × $0.12/kWh = ~$26/month

- Internet (if public):
  - 100Mbps dedicated = ~$50-100/month

- Total: ~$80-130/month

### vs. Cloud Alternative

Google Cloud Translation API:
- $20 per million characters
- 10,000 conversations/month × 100 chars avg = 1M chars
- Cost: $20/month + compute (~$200/month)
- Total: ~$220/month

**Savings:** Self-hosted saves ~$90-140/month

---

**Deployment Status:** Production-ready for LAN
**Last Updated:** 2026-02-08
