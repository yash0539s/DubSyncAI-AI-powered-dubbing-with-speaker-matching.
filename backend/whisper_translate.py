import tempfile
import os
import whisper
from deep_translator import GoogleTranslator
import torch
import warnings

warnings.filterwarnings("ignore")

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base", device=device)

def transcribe_and_translate(audio_bytes, target_lang="es"):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        result = model.transcribe(tmp_path)
        transcription = result["text"] if isinstance(result, dict) else str(result)
        transcription = transcription.strip()
        print("[INFO] Transcription:", transcription)

        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(transcription)
        translated_text = str(translated_text).strip()
        print("[INFO] Translated Text:", translated_text)

        # ✅ Return a list of dicts
        return [{"text": translated_text, "speaker": "SPEAKER_00"}]

    except Exception as e:
        print("❌ Error in transcribe_and_translate():", str(e))
        return [{"text": "", "speaker": "SPEAKER_00"}]

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

