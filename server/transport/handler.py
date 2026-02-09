"""
WebSocket connection handler for Babblefish.
"""
import time
import logging
import uuid
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from server.rooms.manager import RoomManager
from server.rooms.participant import Participant, ClientCapabilities
from server.pipeline.orchestrator import PipelineOrchestrator
from server.transport.protocol import (
    JoinMessage,
    AudioMessage,
    UtteranceEndMessage,
    LeaveMessage,
    ClientErrorMessage,
    TranslationMessage,
    VoiceReferenceMessage,
    VoiceReferenceBroadcastMessage,
)
from server.transport.audio_codec import decode_opus
from server.config import settings

logger = logging.getLogger(__name__)


async def handle_client(
    websocket: WebSocket,
    client_id: str,
    room_manager: RoomManager,
    pipeline: PipelineOrchestrator,
) -> None:
    """
    Handle a WebSocket client connection.

    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
        room_manager: Global room manager
        pipeline: Pipeline orchestrator for ASR + translation
    """
    await websocket.accept()
    logger.info(f"Client {client_id} connected")

    participant = None
    room = None
    audio_buffer = []

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "join":
                # Handle join message
                join_msg = JoinMessage(**data)

                # Get or create room
                room = room_manager.get_or_create_room(join_msg.room_id)

                # Check room capacity
                if room.get_participant_count() >= settings.MAX_PARTICIPANTS_PER_ROOM:
                    await websocket.send_json({
                        "type": "error",
                        "code": "ROOM_FULL",
                        "message": f"Room is full (max {settings.MAX_PARTICIPANTS_PER_ROOM} participants)",
                    })
                    break

                # Parse client capabilities (Phase 2/3)
                capabilities = ClientCapabilities()
                if join_msg.capabilities:
                    capabilities = ClientCapabilities.from_dict(join_msg.capabilities)

                # Create participant
                participant = Participant(
                    participant_id=client_id,
                    name=join_msg.name,
                    language=join_msg.language,
                    websocket=websocket,
                    joined_at=time.time(),
                    capabilities=capabilities,
                )

                # TODO Phase 2/3: Assign TTS mode based on capabilities
                # participant.tts_mode = assign_tts_mode(capabilities)

                # Add to room
                await room.add_participant(participant)

                # Send joined confirmation
                await websocket.send_json({
                    "type": "joined",
                    "room_id": room.room_id,
                    "participant_id": participant.participant_id,
                    "participants": [
                        p.to_dict() for p in room.get_other_participants(participant.participant_id)
                    ],
                    "tts_mode": participant.tts_mode,
                    "tts_model": participant.tts_model,
                })

                logger.info(
                    f"Participant {participant.name} ({client_id}) joined room {room.room_id} "
                    f"(language: {participant.language})"
                )

            elif msg_type == "audio":
                # Handle audio chunk
                if not participant or not room:
                    logger.warning(f"Received audio from client {client_id} before join")
                    continue

                audio_msg = AudioMessage(**data)

                # Decode Opus audio
                audio_chunk = decode_opus(audio_msg.data)

                if len(audio_chunk) > 0:
                    audio_buffer.append(audio_chunk)

            elif msg_type == "utterance_end":
                # Handle end of utterance
                if not participant or not room:
                    logger.warning(f"Received utterance_end from client {client_id} before join")
                    continue

                if not audio_buffer:
                    logger.debug(f"Empty audio buffer for participant {participant.name}")
                    continue

                # Concatenate audio buffer
                full_audio = np.concatenate(audio_buffer)
                audio_buffer = []

                logger.debug(
                    f"Processing utterance from {participant.name}: "
                    f"{len(full_audio)/16000:.1f}s audio"
                )

                # Get target languages from room (excluding speaker's language)
                target_langs = room.get_target_languages(exclude=participant.participant_id)

                if not target_langs:
                    logger.debug(f"No target languages in room {room.room_id}")
                    continue

                # Process through pipeline
                try:
                    result = await pipeline.process_utterance(full_audio, target_langs)

                    # Broadcast translation to room
                    translation_msg = TranslationMessage(
                        speaker_id=participant.participant_id,
                        speaker_name=participant.name,
                        source_lang=result["source_lang"],
                        source_text=result["source_text"],
                        translations=result["translations"],
                        timestamp=time.time(),
                    )

                    await room.broadcast(
                        translation_msg.dict(), exclude=participant.participant_id
                    )

                    logger.info(
                        f"Broadcasted translation from {participant.name}: "
                        f"'{result['source_text']}' ({result['source_lang']}) → "
                        f"{len(result['translations'])} languages"
                    )

                except Exception as e:
                    logger.error(f"Pipeline processing error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "code": "PIPELINE_ERROR",
                        "message": "Failed to process audio",
                    })

            elif msg_type == "leave":
                # Handle leave message
                logger.info(f"Participant {participant.name if participant else client_id} leaving")
                break

            elif msg_type == "voice_reference":
                # Handle voice reference upload (Phase 3)
                if not participant or not room:
                    logger.warning(f"Received voice_reference from client {client_id} before join")
                    continue

                voice_msg = VoiceReferenceMessage(**data)

                # Broadcast voice reference to other participants in the room
                broadcast_msg = VoiceReferenceBroadcastMessage(
                    speaker_id=participant.participant_id,
                    speaker_name=participant.name,
                    voice_data=voice_msg.voice_data,
                    sample_rate=voice_msg.sample_rate,
                    timestamp=time.time(),
                )

                await room.broadcast(
                    broadcast_msg.dict(), exclude=participant.participant_id
                )

                logger.info(
                    f"Broadcasted voice reference from {participant.name} to room {room.room_id}"
                )

            elif msg_type == "client_error":
                # Handle client error report
                error_msg = ClientErrorMessage(**data)
                logger.error(
                    f"Client error from {participant.name if participant else client_id}: "
                    f"[{error_msg.error_type}] {error_msg.error_message}",
                    extra={"context": error_msg.context}
                )

            elif msg_type == "ping":
                # Handle heartbeat
                await websocket.send_json({"type": "pong"})

            else:
                logger.warning(f"Unknown message type from client {client_id}: {msg_type}")

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")

    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}", exc_info=True)

    finally:
        # Cleanup
        if room and participant:
            await room.remove_participant(participant.participant_id)

            # Delete room if empty
            if room.is_empty():
                room_manager.delete_room(room.room_id)

        logger.info(f"Client {client_id} connection closed")
