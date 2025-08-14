# speaker_diarization.py

import os
import tempfile
import subprocess
import torch
import torchaudio
from pathlib import Path
from dotenv import load_dotenv
from pyannote.audio import Pipeline, Inference
from pyannote.core import Segment
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np

# Load .env
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise EnvironmentError("HF_TOKEN not found in .env")

print(f"[INFO] Using HF_TOKEN: {'*' * len(HF_TOKEN)}")

# Load diarization and speaker embedding pipelines
diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=HF_TOKEN)
embedding_model = Inference("pyannote/embedding", use_auth_token=HF_TOKEN)

# Dummy logistic regression gender classifier trained on VoxCeleb-like embeddings (or replace with better)
# In practice: replace with a fine-tuned gender classifier on embeddings.
gender_classifier = LogisticRegression()
scaler = StandardScaler()

# Load simple pretrained mean vectors for male/female for quick prototype (not ideal but functional)
# You can replace this with an actual classifier using a training set
female_proto = np.load(Path(__file__).parent / "D:\\EduDub_Advanced_Template\\edudub\\female_embedding.npy")  # mean female embedding
male_proto = np.load(Path(__file__).parent / "D:\\EduDub_Advanced_Template\\edudub\\male_embedding.npy")      # mean male embedding

FFMPEG_PATH = r"D:\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"# Change this to your actual path

def extract_audio_from_video(video_path: str) -> str:
    audio_path = tempfile.mktemp(suffix=".wav")
    cmd = [
        FFMPEG_PATH, "-i", video_path, "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1", audio_path, "-y", "-loglevel", "error"
    ]
    subprocess.run(cmd, check=True)
    return audio_path


def assign_voices_by_speaker(video_path: str) -> dict:
    print(f"[INFO] Extracting audio from: {video_path}")
    audio_path = extract_audio_from_video(video_path)

    print("[INFO] Running speaker diarization...")
    diarization = diarization_pipeline(audio_path)

    waveform, sample_rate = torchaudio.load(audio_path)
    voice_map = {}

    tracks = list(diarization.itertracks(yield_label=True))
    print(f"[DEBUG] Diarization tracks count: {len(tracks)}")
    print(f"[DEBUG] First few tracks: {tracks[:3]}")

    if not tracks:
        print("[ERROR] No speaker segments detected — cannot proceed with diarization.")
        return {}

    for idx, track in enumerate(tracks):
        try:
            # Handle both formats dynamically
            if len(track) == 3:
                # Flat format: (<Segment>, track_id, speaker)
                turn, track_id, speaker = track
            elif len(track) == 2:
                # Nested format: ((<Segment>, track_id), speaker)
                (turn, track_id), speaker = track
            else:
                raise ValueError(f"Unexpected diarization tuple length: {len(track)}")

            print(f"[OK] Track {idx} - Speaker {speaker} from {turn.start:.2f}s to {turn.end:.2f}s")

            speaker = str(speaker)

            if speaker in voice_map:
                continue

            embedding = embedding_model.crop(audio_path, turn)
            if embedding is None or np.all(embedding == 0):
                print(f"[WARN] No valid embedding for {speaker}, skipping gender detection.")
                voice_map[speaker] = "unknown"
                continue

            sim_female = np.dot(embedding, female_proto) / (
                np.linalg.norm(embedding) * np.linalg.norm(female_proto)
            )
            sim_male = np.dot(embedding, male_proto) / (
                np.linalg.norm(embedding) * np.linalg.norm(male_proto)
            )

            gender = "female" if sim_female > sim_male else "male"
            print(f"[INFO] {speaker} classified as {gender} "
                  f"(sim_f: {sim_female:.2f}, sim_m: {sim_male:.2f})")

            voice_map[speaker] = gender

        except Exception as e:
            print(f"[ERROR] Failed processing diarization item at index {idx}: {e}")

    return voice_map
