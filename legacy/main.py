from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from faster_whisper import WhisperModel
import tempfile
import os
from pathlib import Path

# Import configuration
try:
    from config import (
        DEVICE, COMPUTE_TYPE, WHISPER_MODEL_SIZE, NLLB_CT2_PATH,
        WHISPER_VAD_FILTER, WHISPER_VAD_MIN_SILENCE_MS, NLLB_BEAM_SIZE,
        NLLB_MAX_BATCH_SIZE, PRELOAD_MODELS, CPU_THREADS
    )
except ImportError:
    # Defaults if config.py not found
    DEVICE = "cpu"
    COMPUTE_TYPE = "int8"
    WHISPER_MODEL_SIZE = "medium"
    NLLB_CT2_PATH = "./models/nllb-ct2"
    WHISPER_VAD_FILTER = True
    WHISPER_VAD_MIN_SILENCE_MS = 500
    NLLB_BEAM_SIZE = 4
    NLLB_MAX_BATCH_SIZE = 32
    PRELOAD_MODELS = True
    CPU_THREADS = 4

# Import NLLB translator
# Using CTranslate2 for 3x faster inference!
from nllb_ct2_fixed import NLLBTranslatorCT2 as NLLBTranslator

app = FastAPI(
    title="BabbleFish Translation Service",
    description="NLLB-200 translation and Whisper transcription via CTranslate2",
    version="1.0.0"
)

# Global model holders
nllb_translator = None
whisper_model = None

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class TranslationResponse(BaseModel):
    translation: str
    source_lang: str
    target_lang: str

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    segments: Optional[List[dict]] = None

class TranscribeTranslateResponse(BaseModel):
    transcription: str
    detected_language: str
    translation: str
    target_lang: str

@app.on_event("startup")
async def load_models():
    """Load models on startup"""
    global nllb_translator, whisper_model

    if not PRELOAD_MODELS:
        print("Model preloading disabled. Models will load on first request.")
        return

    print(f"Loading models on {DEVICE} with {COMPUTE_TYPE}...")

    # Load NLLB-200 model (using CTranslate2 for 3x speed boost!)
    try:
        print("Loading NLLB model (CTranslate2 optimized)...")
        nllb_translator = NLLBTranslator(
            model_path="./models/nllb-ct2-fixed",
            original_model="facebook/nllb-200-distilled-1.3B",
            cache_dir="./cache",
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        nllb_translator.load_model()

    except Exception as e:
        print(f"[WARNING] Error loading NLLB: {e}")
        print("          NLLB translation will not be available.")

    # Load Whisper model
    try:
        print(f"Loading Whisper {WHISPER_MODEL_SIZE} model...")
        whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            cpu_threads=CPU_THREADS if DEVICE == "cpu" else 0
        )
        print(f"[OK] Whisper model loaded successfully on {DEVICE}")
    except Exception as e:
        print(f"[WARNING] Error loading Whisper: {e}")
        print("          Audio transcription will not be available.")

@app.get("/")
async def root():
    """API information"""
    return {
        "service": "BabbleFish Translation Service",
        "endpoints": {
            "translate": "/translate - Translate text",
            "transcribe": "/transcribe - Transcribe audio",
            "transcribe_translate": "/transcribe-translate - Transcribe and translate audio",
            "health": "/health - Service health check",
            "languages": "/languages - Supported languages"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models": {
            "nllb": nllb_translator is not None,
            "whisper": whisper_model is not None
        }
    }

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text from source language to target language using NLLB-200

    Language codes follow the Flores-200 format, e.g.:
    - eng_Latn (English)
    - spa_Latn (Spanish)
    - fra_Latn (French)
    - deu_Latn (German)
    - zho_Hans (Chinese Simplified)
    """
    if nllb_translator is None:
        raise HTTPException(status_code=503, detail="NLLB model not loaded")

    try:
        # Translate using NLLB
        translation = nllb_translator.translate(
            request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )

        return TranslationResponse(
            translation=translation,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    task: str = "transcribe"
):
    """
    Transcribe audio file using Whisper

    Args:
        file: Audio file (mp3, wav, m4a, etc.)
        language: Optional language code (e.g., 'en', 'es', 'fr')
        task: 'transcribe' or 'translate' (translate will translate to English)
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")

    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Transcribe
        segments, info = whisper_model.transcribe(
            tmp_file_path,
            language=language,
            task=task,
            vad_filter=WHISPER_VAD_FILTER,
            vad_parameters=dict(min_silence_duration_ms=WHISPER_VAD_MIN_SILENCE_MS)
        )

        # Collect segments
        segments_list = []
        full_text = []

        for segment in segments:
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            full_text.append(segment.text)

        # Clean up
        os.unlink(tmp_file_path)

        return TranscriptionResponse(
            text=" ".join(full_text),
            language=info.language,
            segments=segments_list
        )

    except Exception as e:
        # Clean up on error
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe-translate", response_model=TranscribeTranslateResponse)
async def transcribe_and_translate(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    source_lang: Optional[str] = None
):
    """
    Transcribe audio and translate to target language

    This combines Whisper transcription with NLLB translation
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")
    if nllb_translator is None:
        raise HTTPException(status_code=503, detail="NLLB model not loaded")

    try:
        # First, transcribe
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        segments, info = whisper_model.transcribe(
            tmp_file_path,
            language=source_lang,
            task="transcribe"
        )

        # Collect text
        full_text = " ".join([segment.text for segment in segments])
        detected_lang = info.language

        # Clean up audio file
        os.unlink(tmp_file_path)

        # Convert language codes
        # Whisper uses ISO codes (en, es, fr)
        # NLLB uses Flores codes (eng_Latn, spa_Latn, fra_Latn)
        flores_source = convert_to_flores(detected_lang)
        flores_target = target_lang if "_" in target_lang else convert_to_flores(target_lang)

        # Translate using NLLB
        translation = nllb_translator.translate(
            full_text,
            source_lang=flores_source,
            target_lang=flores_target
        )

        return TranscribeTranslateResponse(
            transcription=full_text,
            detected_language=detected_lang,
            translation=translation,
            target_lang=flores_target
        )

    except Exception as e:
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_supported_languages():
    """Get supported language codes"""
    return {
        "whisper_languages": [
            "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ja",
            "ko", "zh", "ar", "tr", "hi", "vi", "id", "th", "uk", "ro"
            # Add more as needed
        ],
        "nllb_languages": [
            "eng_Latn", "spa_Latn", "fra_Latn", "deu_Latn", "ita_Latn",
            "por_Latn", "rus_Cyrl", "jpn_Jpan", "kor_Hang", "zho_Hans",
            "ara_Arab", "hin_Deva", "vie_Latn", "tha_Thai", "ind_Latn"
            # NLLB supports 200 languages - add more as needed
        ],
        "note": "Whisper uses ISO 639-1 codes, NLLB uses Flores-200 codes"
    }

def convert_to_flores(iso_code: str) -> str:
    """Convert ISO 639-1 to Flores-200 language code"""
    mapping = {
        "en": "eng_Latn",
        "es": "spa_Latn",
        "fr": "fra_Latn",
        "de": "deu_Latn",
        "it": "ita_Latn",
        "pt": "por_Latn",
        "ru": "rus_Cyrl",
        "ja": "jpn_Jpan",
        "ko": "kor_Hang",
        "zh": "zho_Hans",
        "ar": "ara_Arab",
        "hi": "hin_Deva",
        "vi": "vie_Latn",
        "th": "tha_Thai",
        "id": "ind_Latn",
        "tr": "tur_Latn",
        "nl": "nld_Latn",
        "pl": "pol_Latn",
        "uk": "ukr_Cyrl",
        "ro": "ron_Latn"
    }
    return mapping.get(iso_code, f"{iso_code}_Latn")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
