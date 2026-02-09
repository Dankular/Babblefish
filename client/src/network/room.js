// Room state management
export class RoomState {
  constructor() {
    this.roomId = null;
    this.participantId = null;
    this.participants = new Map();
    this.isJoined = false;
  }

  handleJoined(message) {
    this.roomId = message.room_id;
    this.participantId = message.participant_id;
    this.isJoined = true;

    // Add initial participants
    if (message.participants && Array.isArray(message.participants)) {
      message.participants.forEach(participant => {
        this.participants.set(participant.id, {
          id: participant.id,
          name: participant.name,
          language: participant.language,
          joinedAt: Date.now()
        });
      });
    }

    console.log(`Joined room ${this.roomId} as ${this.participantId}`);
    console.log(`${this.participants.size} other participants in room`);
  }

  handleParticipantJoined(message) {
    const participant = message.participant;
    if (participant && participant.id !== this.participantId) {
      this.participants.set(participant.id, {
        id: participant.id,
        name: participant.name,
        language: participant.language,
        joinedAt: Date.now()
      });
      console.log(`Participant joined: ${participant.name} (${participant.language})`);
    }
  }

  handleParticipantLeft(message) {
    const participantId = message.participant_id;
    if (this.participants.has(participantId)) {
      const participant = this.participants.get(participantId);
      this.participants.delete(participantId);
      console.log(`Participant left: ${participant.name}`);
    }
  }

  getParticipants() {
    return Array.from(this.participants.values());
  }

  getParticipant(id) {
    return this.participants.get(id);
  }

  getParticipantCount() {
    return this.participants.size;
  }

  getLanguages() {
    const languages = new Set();
    this.participants.forEach(p => languages.add(p.language));
    return Array.from(languages);
  }

  reset() {
    this.roomId = null;
    this.participantId = null;
    this.participants.clear();
    this.isJoined = false;
  }

  getState() {
    return {
      roomId: this.roomId,
      participantId: this.participantId,
      isJoined: this.isJoined,
      participantCount: this.participants.size,
      participants: this.getParticipants()
    };
  }
}
