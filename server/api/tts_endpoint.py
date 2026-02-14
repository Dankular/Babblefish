"""
TTS API Endpoint - FastAPI endpoints for TTS Manager V2
Provides REST API for ASR, Translation, and TTS with voice cloning
"""
import logging
import io
import numpy as np
import soundfile as sf
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from typing import Optional
from pydantic import BaseModel
from server.tts.tts_manager_v2 import TTSManagerV2

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/tts", tags=["TTS"])

# Global TTS Manager instance
tts_manager: Optional[TTSManagerV2] = None


# ========== Pydantic Models ==========

class TTSRequest(BaseModel):
    """Request model for text-to-speech synthesis"""
    text: str
    language: str = 'en'
    voice_profile: Optional[str] = None
    temperature: float = 0.7
    speed: float = 1.0


class TranslationRequest(BaseModel):
    """Request model for text translation"""
    text: str
    source_lang: str
    target_lang: str


class ASRResponse(BaseModel):
    """Response model for ASR"""
    text: str
    language: str
    duration: float


class TranslationResponse(BaseModel):
    """Response model for translation"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str


class StatusResponse(BaseModel):
    """Response model for status check"""
    status: str
    device: str
    compute_type: str
    supported_languages: list
    voice_profiles: list


# ========== Initialization ==========

def initialize_tts_manager(use_gpu: bool = True, compute_type: str = "int8"):
    """
    Initialize the global TTS manager

    Args:
        use_gpu: Enable GPU acceleration
        compute_type: Compute type for quantization
    """
    global tts_manager

    if tts_manager is None:
        logger.info("Initializing TTS Manager V2...")
        tts_manager = TTSManagerV2(use_gpu=use_gpu, compute_type=compute_type)
        tts_manager.load()
        logger.info("TTS Manager V2 ready")


def get_tts_manager() -> TTSManagerV2:
    """Get the TTS manager instance"""
    if tts_manager is None:
        raise HTTPException(
            status_code=503,
            detail="TTS Manager not initialized. Call /api/tts/status first."
        )
    return tts_manager


# ========== Endpoints ==========

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get TTS manager status and capabilities

    Returns device info, supported languages, and available voice profiles
    """
    try:
        # Initialize if needed
        if tts_manager is None:
            initialize_tts_manager()

        manager = get_tts_manager()
        device_info = manager.get_device_info()

        return StatusResponse(
            status="ready",
            device=device_info['device'],
            compute_type=device_info['compute_type'],
            supported_languages=manager.get_supported_languages(),
            voice_profiles=manager.get_voice_profiles()
        )

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    language: str = Form('en'),
    voice_profile: Optional[str] = Form(None),
    temperature: float = Form(0.7),
    speed: float = Form(1.0),
    reference_audio: Optional[UploadFile] = File(None)
):
    """
    Synthesize speech from text with optional voice cloning

    Args:
        text: Text to synthesize
        language: Target language code (ISO 639-1)
        voice_profile: Name of voice profile to use
        temperature: Voice variation (0.1-1.0)
        speed: Speech speed multiplier (0.5-2.0)
        reference_audio: Reference audio file for voice cloning (WAV/MP3)

    Returns:
        WAV audio file (24kHz, mono, float32)
    """
    try:
        manager = get_tts_manager()

        # Handle reference audio if provided
        ref_audio = None
        if reference_audio:
            audio_bytes = await reference_audio.read()
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

            # Convert to mono if stereo
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)

            # Resample to 24kHz if needed
            if sample_rate != 24000:
                import librosa
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=24000)

            ref_audio = audio_data.astype(np.float32)
            logger.info(f"Loaded reference audio: {len(ref_audio)} samples")

        # Synthesize speech
        audio = manager.synthesize(
            text=text,
            language=language,
            voice_profile=voice_profile,
            reference_audio=ref_audio,
            temperature=temperature,
            speed=speed
        )

        # Convert to WAV bytes
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio, manager.get_sample_rate(), format='WAV')
        wav_bytes = wav_buffer.getvalue()

        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )

    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe", response_model=ASRResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...)
):
    """
    Transcribe audio to text with language detection (ASR)

    Args:
        audio_file: Audio file to transcribe (WAV/MP3)

    Returns:
        Transcribed text and detected language
    """
    try:
        manager = get_tts_manager()

        # Read audio file
        audio_bytes = await audio_file.read()
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

        # Convert to mono if stereo
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        # Convert to float32
        audio_data = audio_data.astype(np.float32)

        # Transcribe
        text, language = manager.transcribe(audio_data, sample_rate)

        duration = len(audio_data) / sample_rate

        return ASRResponse(
            text=text,
            language=language,
            duration=duration
        )

    except Exception as e:
        logger.error(f"ASR transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text between languages

    Args:
        text: Text to translate
        source_lang: Source language code (ISO 639-1)
        target_lang: Target language code (ISO 639-1)

    Returns:
        Translated text
    """
    try:
        manager = get_tts_manager()

        translated = manager.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )

        return TranslationResponse(
            original_text=request.text,
            translated_text=translated,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_full_pipeline(
    audio_file: UploadFile = File(...),
    target_language: str = Form(...),
    voice_profile: Optional[str] = Form(None),
    temperature: float = Form(0.7),
    speed: float = Form(1.0)
):
    """
    Complete pipeline: Audio → ASR → Translation → TTS

    Takes input audio, transcribes it, translates to target language,
    and synthesizes speech in target language with voice cloning

    Args:
        audio_file: Input audio file (WAV/MP3)
        target_language: Target language for output speech
        voice_profile: Voice profile for TTS
        temperature: Voice variation (0.1-1.0)
        speed: Speech speed multiplier (0.5-2.0)

    Returns:
        WAV audio file with synthesized speech in target language
    """
    try:
        manager = get_tts_manager()

        # Read audio file
        audio_bytes = await audio_file.read()
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

        # Convert to mono if stereo
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        # Convert to float32
        audio_data = audio_data.astype(np.float32)

        # Process full pipeline
        synthesized_audio, metadata = manager.process_audio(
            audio=audio_data,
            target_language=target_language,
            sample_rate=sample_rate,
            voice_profile=voice_profile,
            temperature=temperature,
            speed=speed
        )

        # Convert to WAV bytes
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, synthesized_audio, manager.get_sample_rate(), format='WAV')
        wav_bytes = wav_buffer.getvalue()

        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=translated_{target_language}.wav",
                "X-Source-Text": metadata.get('source_text', ''),
                "X-Source-Lang": metadata.get('source_lang', ''),
                "X-Translated-Text": metadata.get('translated_text', '')
            }
        )

    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-profile/add")
async def add_voice_profile(
    name: str = Form(...),
    description: str = Form(""),
    audio_file: UploadFile = File(...)
):
    """
    Add a new voice profile for voice cloning

    Args:
        name: Profile name
        description: Optional description
        audio_file: Reference audio file (WAV/MP3, 24kHz recommended)

    Returns:
        Success message
    """
    try:
        manager = get_tts_manager()

        # Read audio file
        audio_bytes = await audio_file.read()
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

        # Convert to mono if stereo
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        # Resample to 24kHz if needed
        if sample_rate != 24000:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=24000)

        audio_data = audio_data.astype(np.float32)

        # Add voice profile
        manager.add_voice_profile(name, audio_data, description)

        return {"status": "success", "message": f"Voice profile '{name}' added"}

    except Exception as e:
        logger.error(f"Failed to add voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice-profiles")
async def list_voice_profiles():
    """
    List all available voice profiles

    Returns:
        List of voice profile names
    """
    try:
        manager = get_tts_manager()
        profiles = manager.get_voice_profiles()
        return {"voice_profiles": profiles}

    except Exception as e:
        logger.error(f"Failed to list voice profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages

    Returns:
        List of language codes (ISO 639-1)
    """
    try:
        manager = get_tts_manager()
        languages = manager.get_supported_languages()
        return {"languages": languages}

    except Exception as e:
        logger.error(f"Failed to get languages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
