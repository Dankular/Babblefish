// Message type definitions
export const MessageType = {
  // Client -> Server
  JOIN: 'join',
  AUDIO: 'audio',
  UTTERANCE_END: 'utterance_end',
  LEAVE: 'leave',
  PING: 'ping',

  // Server -> Client
  JOINED: 'joined',
  TRANSLATION: 'translation',
  PARTICIPANT_JOINED: 'participant_joined',
  PARTICIPANT_LEFT: 'participant_left',
  ERROR: 'error',
  PONG: 'pong'
};

export function createJoinMessage(roomId, language, name) {
  return {
    type: MessageType.JOIN,
    room_id: roomId,
    language: language,
    name: name
  };
}

export function createAudioMessage(data, timestamp = Date.now()) {
  return {
    type: MessageType.AUDIO,
    data: data, // base64 encoded Opus
    timestamp: timestamp
  };
}

export function createUtteranceEndMessage(timestamp = Date.now()) {
  return {
    type: MessageType.UTTERANCE_END,
    timestamp: timestamp
  };
}

export function createLeaveMessage() {
  return {
    type: MessageType.LEAVE
  };
}

export function createPingMessage() {
  return {
    type: MessageType.PING,
    timestamp: Date.now()
  };
}

export function parseMessage(data) {
  try {
    if (typeof data === 'string') {
      return JSON.parse(data);
    }
    return data;
  } catch (error) {
    console.error('Failed to parse message:', error);
    return null;
  }
}

export function validateJoinedMessage(msg) {
  return (
    msg.type === MessageType.JOINED &&
    typeof msg.room_id === 'string' &&
    typeof msg.participant_id === 'string' &&
    Array.isArray(msg.participants)
  );
}

export function validateTranslationMessage(msg) {
  return (
    msg.type === MessageType.TRANSLATION &&
    typeof msg.speaker_id === 'string' &&
    typeof msg.speaker_name === 'string' &&
    typeof msg.source_lang === 'string' &&
    typeof msg.source_text === 'string' &&
    typeof msg.translations === 'object' &&
    typeof msg.timestamp === 'number'
  );
}

export function validateParticipantMessage(msg) {
  return (
    (msg.type === MessageType.PARTICIPANT_JOINED || msg.type === MessageType.PARTICIPANT_LEFT) &&
    (msg.participant || msg.participant_id)
  );
}
