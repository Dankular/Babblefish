# Babblefish WebSocket Protocol Specification

This document describes the WebSocket protocol used for communication between Babblefish clients and server.

## Connection

**Endpoint**: `ws://<server>:<port>/ws/client`

**Default**: `ws://localhost:8000/ws/client`

**Transport**: WebSocket (RFC 6455)
**Encoding**: JSON

---

## Message Format

All messages are JSON objects with a `type` field indicating the message type.

```json
{
  "type": "message_type",
  "field1": "value1",
  "field2": "value2"
}
```

---

## Client → Server Messages

### 1. Join Room

Client joins a translation room.

```json
{
  "type": "join",
  "room_id": "ABC123",
  "language": "en",
  "name": "Alice",
  "capabilities": {
    "webgpu": true,
    "gpu_adapter": "NVIDIA GeForce RTX 3060",
    "vram_estimate": 6144,
    "wasm": true,
    "max_model_size": "large",
    "preferred_mode": "local_tts"
  }
}
```

**Fields**:
- `type`: `"join"` (required)
- `room_id`: Room identifier, 6-character alphanumeric (required)
- `language`: Target language ISO 639-1 code (required)
- `name`: User's display name (required)
- `capabilities`: Client device capabilities (optional, Phase 2/3)
  - `webgpu`: WebGPU support (boolean)
  - `gpu_adapter`: GPU name (string)
  - `vram_estimate`: Estimated VRAM in MB (integer)
  - `wasm`: WebAssembly support (boolean)
  - `max_model_size`: "small" | "medium" | "large"
  - `preferred_mode`: "local_tts" | "server_tts" | "text_only"

**Supported Languages**: See `server/pipeline/language.py`

**Response**: Server sends `joined` message

---

### 2. Audio Chunk

Client sends audio data during speech.

```json
{
  "type": "audio",
  "data": "base64_encoded_opus_audio",
  "timestamp": 1707400000
}
```

**Fields**:
- `type`: `"audio"` (required)
- `data`: Base64-encoded Opus audio (required)
- `timestamp`: Client timestamp in milliseconds (required)

**Audio Format**:
- Codec: Opus
- Sample rate: 16 kHz
- Channels: Mono (1)
- Encoding: Base64 string
- Chunk size: ~200ms recommended

**Behavior**:
- Client should only send audio when VAD detects speech
- Server buffers chunks until `utterance_end` is received
- Chunks sent out of order may cause degraded transcription

---

### 3. Utterance End

Client signals end of speech utterance (VAD detected silence).

```json
{
  "type": "utterance_end",
  "timestamp": 1707400002
}
```

**Fields**:
- `type`: `"utterance_end"` (required)
- `timestamp`: Client timestamp in milliseconds (required)

**Behavior**:
- Triggers server to process buffered audio through ASR → Translation pipeline
- Server sends `translation` message to all participants

---

### 4. Leave Room

Client leaves the room.

```json
{
  "type": "leave"
}
```

**Fields**:
- `type`: `"leave"` (required)

**Behavior**:
- Server removes participant from room
- Server sends `participant_left` message to remaining participants
- WebSocket connection may be closed after this message

---

### 5. Heartbeat (Ping)

Client sends periodic heartbeat to keep connection alive.

```json
{
  "type": "ping"
}
```

**Fields**:
- `type`: `"ping"` (required)

**Response**: Server sends `pong` message

**Recommended**: Send every 30 seconds

---

## Server → Client Messages

### 1. Joined

Confirmation that client successfully joined the room.

```json
{
  "type": "joined",
  "room_id": "ABC123",
  "participant_id": "P_01",
  "participants": [
    {
      "id": "P_02",
      "name": "Bob",
      "language": "es",
      "speaker_id": null,
      "tts_mode": "text_only",
      "tts_model": null
    }
  ],
  "tts_mode": "text_only",
  "tts_model": null
}
```

**Fields**:
- `type`: `"joined"`
- `room_id`: Room identifier
- `participant_id`: Assigned participant ID
- `participants`: Array of other participants in the room
- `tts_mode`: Assigned TTS mode (Phase 2/3): `"local"` | `"server"` | `"text_only"`
- `tts_model`: Assigned TTS model (Phase 2/3): `"f5-tts"` | `"kokoro"` | `null`

**Participant Object**:
- `id`: Participant identifier
- `name`: Display name
- `language`: Target language
- `speaker_id`: Speaker identifier (Phase 3, null in Phase 1)
- `tts_mode`: TTS mode
- `tts_model`: TTS model

---

### 2. Translation

Translation result broadcast to all participants.

```json
{
  "type": "translation",
  "speaker_id": "P_01",
  "speaker_name": "Alice",
  "source_lang": "en",
  "source_text": "Hello everyone",
  "translations": {
    "es": "Hola a todos",
    "fr": "Bonjour à tous",
    "de": "Hallo zusammen"
  },
  "timestamp": 1707400002.5,
  "audio": null
}
```

**Fields**:
- `type`: `"translation"`
- `speaker_id`: ID of participant who spoke
- `speaker_name`: Display name of speaker
- `source_lang`: Detected source language (ISO 639-1)
- `source_text`: Transcribed text in source language
- `translations`: Object mapping language codes to translated text
- `timestamp`: Server timestamp (seconds since epoch)
- `audio`: Base64 Opus audio (Phase 2/3, for server-side TTS clients)

**Behavior**:
- Broadcast to all participants except the speaker
- Each participant receives translations for all languages in the room
- Client should display translation matching their target language

---

### 3. Participant Joined

Notification that a new participant joined the room.

```json
{
  "type": "participant_joined",
  "participant": {
    "id": "P_03",
    "name": "Charlie",
    "language": "fr",
    "speaker_id": null,
    "tts_mode": "text_only",
    "tts_model": null
  }
}
```

**Fields**:
- `type`: `"participant_joined"`
- `participant`: Participant object (see `joined` message)

---

### 4. Participant Left

Notification that a participant left the room.

```json
{
  "type": "participant_left",
  "participant_id": "P_03"
}
```

**Fields**:
- `type`: `"participant_left"`
- `participant_id`: ID of participant who left

---

### 5. Error

Error message from server.

```json
{
  "type": "error",
  "code": "ROOM_FULL",
  "message": "Room is full (max 10 participants)"
}
```

**Fields**:
- `type`: `"error"`
- `code`: Error code (string)
- `message`: Human-readable error message

**Error Codes**:
- `ROOM_FULL`: Room has reached maximum participants
- `PIPELINE_ERROR`: Server failed to process audio
- `INVALID_MESSAGE`: Malformed message from client
- `UNAUTHORIZED`: Authentication failed (future)

---

### 6. Heartbeat Response (Pong)

Response to client ping.

```json
{
  "type": "pong"
}
```

**Fields**:
- `type`: `"pong"`

---

## Phase 2/3: Additional Messages

These messages will be used in future phases when TTS is implemented.

### Speaker Enrolled (Server → Client)

Broadcast when a participant completes voice enrollment.

```json
{
  "type": "speaker_enrolled",
  "participant_id": "P_01",
  "name": "Alice",
  "language": "en",
  "reference_audio": "base64_encoded_pcm_audio",
  "reference_text": "This is my voice sample for enrollment."
}
```

**Fields**:
- `reference_audio`: 15-second voice sample, 16kHz mono PCM, base64 (~200KB)
- `reference_text`: Transcription of the reference audio

**Purpose**: Distribute voice references to all participants for F5-TTS synthesis

---

### Enrol (Client → Server)

Client sends voice enrollment audio.

```json
{
  "type": "enrol",
  "audio": "base64_encoded_pcm_audio"
}
```

**Fields**:
- `audio`: 15-second clean speech sample, 16kHz mono PCM, base64

---

## Connection Lifecycle

### 1. Connect

```
Client                          Server
  |                               |
  |------ WebSocket Connect ----->|
  |<----- WebSocket Accept -------|
  |                               |
```

### 2. Join Room

```
Client                          Server
  |                               |
  |------ join message ---------->|
  |                               | [Add to room]
  |<----- joined message ---------|
  |<----- participant_joined -----|  (broadcast to others)
  |                               |
```

### 3. Speak & Translate

```
Client A                        Server                        Client B (Spanish)
  |                               |                               |
  |-- audio chunks (streaming) -->|                               |
  |-- utterance_end ------------->|                               |
  |                               | [ASR + Translation]           |
  |                               |---- translation message ----->|
  |                               |                               | "Hola a todos"
  |                               |                               |
```

### 4. Leave Room

```
Client                          Server
  |                               |
  |------ leave message --------->|
  |                               | [Remove from room]
  |                               |---- participant_left ------->| (broadcast)
  |<----- WebSocket Close --------|
  |                               |
```

---

## Best Practices

### Client Implementation

1. **Reconnection**: Implement exponential backoff reconnection (max 10 attempts, up to 30s delay)
2. **VAD**: Use client-side VAD to only send speech, not silence
3. **Buffering**: Buffer audio chunks locally before sending (reduces network overhead)
4. **Heartbeat**: Send ping every 30 seconds to detect connection loss
5. **Error Handling**: Display user-friendly error messages from server

### Server Implementation

1. **Validation**: Validate all incoming messages (Pydantic schemas recommended)
2. **Rate Limiting**: Limit audio chunks per second to prevent abuse
3. **Cleanup**: Remove disconnected clients and empty rooms
4. **Logging**: Log all translation events for debugging and analytics

---

## Security Considerations

**Phase 1** (Current): No authentication, open access

**Future Phases**:
- JWT-based authentication
- Room passwords
- Participant limits per user
- Rate limiting per IP/user
- Audio content filtering

---

## Testing

### Manual Testing with `wscat`

```bash
npm install -g wscat

# Connect
wscat -c ws://localhost:8000/ws/client

# Send join message
> {"type":"join","room_id":"TEST","language":"en","name":"TestUser"}

# Server responds with joined message
< {"type":"joined","room_id":"TEST",...}
```

### Automated Testing

See `server/tests/test_transport.py` for WebSocket protocol tests.

---

## Version History

- **v0.1.0** (2025-02-09): Initial protocol specification (Phase 1 MVP)
- Future: TTS messages (Phase 2/3)
- Future: Authentication & encryption
