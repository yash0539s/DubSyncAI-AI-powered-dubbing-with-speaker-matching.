# elevenlabs_dubbing.py

import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import generate, save, set_api_key

# Load .env from parent directory
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

# Set API key
api_key = os.getenv("ELEVEN_API_KEY")
if not api_key:
    raise ValueError("❌ ELEVEN_API_KEY not found in .env")
set_api_key(api_key)

# Voice map by language and gender
VOICE_MAP = {
    "en": {"male": "onwK4e9ZLuTAKqWW03F9", "female": "EXAVITQu4vr4xnSDxMaL"},
    "hi": {"male": "XB0fDUnXU5powFXDhCwa", "female": "cgSgspJ2msm6clMCkdW9"},
    "gu": {"male": "pqHfZKP75CvOlQylNhV4", "female": "pFZP5JQG7iQjIQuC4Bku"},
    "pa": {"male": "bIHbv24MWmeRgasZH58o", "female": "XrExE9yKIg1WjnnlVkGX"},
    "bn": {"male": "cjVigY5qzO86Huf0OWal", "female": "Xb7hH8MSUJpSbSDYk0k2"},
    "ta": {"male": "nPczCjzI2devNBz1zQrb", "female": "FGY2WhTYpPnrIDTdsKH5"},
    "te": {"male": "iP95p4xoKVk53GoZ742B", "female": "SAz9YHcvj6GT2YYXdXww"},
    "ml": {"male": "TX3LPaxmHKxFdv7VOQHJ", "female": "9BWtsMINqrJLrRacOk9x"},
    "kn": {"male": "JBFqnCBsd6RMkjVDRZzb", "female": "z9fAnlkpzviPz146aGWa"},
    "mr": {"male": "IKne3meq5aSn9XLyUdCD", "female": "XB0fDUnXU5powFXDhCwa"},
    "ur": {"male": "bVMeCyTHy58xNoL34h3p", "female": "pNInz6obpgDQGcFmaJgB"},
    "es": {"male": "TxGEqnHWrfWFTfGW9XjX", "female": "z9fAnlkpzviPz146aGWa"},
    "fr": {"male": "bVMeCyTHy58xNoL34h3p", "female": "pNInz6obpgDQGcFmaJgB"},
}

# Default fallback
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah (neutral)

def get_voice_id(gender: str, lang: str) -> str:
    gender = gender.lower()
    lang = lang.lower()
    return VOICE_MAP.get(lang, {}).get(gender, DEFAULT_VOICE_ID)

def generate_dub(transcript: list, lang: str, voice_map: dict) -> str:
    """
    Generate a full dubbed audio track from transcript with speaker-based voices.

    Parameters:
    - transcript: List of dicts with 'text', 'speaker' keys
    - lang: Language code (e.g., 'en', 'hi')
    - voice_map: Dict like {'SPEAKER_00': 'female', 'SPEAKER_01': 'male'}

    Returns:
    - Path to final stitched MP3 audio
    """
    from pydub import AudioSegment

    combined_audio = AudioSegment.silent(duration=0)

    for i, entry in enumerate(transcript):
        text = entry.get("text", "").strip()
        speaker = entry.get("speaker", "SPEAKER_00")

        if not text:
            print(f"[WARN] Skipping empty text at entry #{i}")
            continue

        gender = voice_map.get(speaker, "female").lower()
        voice_id = get_voice_id(gender, lang)

        print(f"[INFO] Generating voice for {speaker} ({gender}) → {voice_id}")
        try:
            audio = generate(
                text=text,
                voice=voice_id,
                model="eleven_multilingual_v2"
            )
        except Exception as e:
            print(f"[ERROR] Failed to generate for {speaker}: {e}")
            continue

        temp_path = Path(tempfile.mktemp(suffix=".mp3"))
        save(audio, str(temp_path))

        segment = AudioSegment.from_file(temp_path)
        combined_audio += segment

    output_path = Path(tempfile.mktemp(suffix=".mp3"))
    combined_audio.export(str(output_path), format="mp3")
    print(f"[INFO] ✅ Dubbed audio saved to: {output_path}")
    return str(output_path)
