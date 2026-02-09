// Room state hook
import { useState, useEffect, useCallback } from 'react';
import { RoomState } from '../network/room';
import { MessageType } from '../network/protocol';

export function useRoom(messages) {
  const [roomState] = useState(() => new RoomState());
  const [participants, setParticipants] = useState([]);
  const [isJoined, setIsJoined] = useState(false);

  useEffect(() => {
    if (!messages || messages.length === 0) return;

    const latestMessage = messages[messages.length - 1];

    switch (latestMessage.type) {
      case MessageType.JOINED:
        roomState.handleJoined(latestMessage);
        setIsJoined(true);
        setParticipants(roomState.getParticipants());
        break;

      case MessageType.PARTICIPANT_JOINED:
        roomState.handleParticipantJoined(latestMessage);
        setParticipants(roomState.getParticipants());
        break;

      case MessageType.PARTICIPANT_LEFT:
        roomState.handleParticipantLeft(latestMessage);
        setParticipants(roomState.getParticipants());
        break;

      default:
        break;
    }
  }, [messages, roomState]);

  const getParticipant = useCallback((id) => {
    return roomState.getParticipant(id);
  }, [roomState]);

  const getParticipants = useCallback(() => {
    return roomState.getParticipants();
  }, [roomState]);

  const getLanguages = useCallback(() => {
    return roomState.getLanguages();
  }, [roomState]);

  return {
    isJoined,
    roomId: roomState.roomId,
    participantId: roomState.participantId,
    participants,
    getParticipant,
    getParticipants,
    getLanguages,
    participantCount: participants.length
  };
}
