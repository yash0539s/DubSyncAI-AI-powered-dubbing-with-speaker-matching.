# check_prototypes.py
import numpy as np
from pathlib import Path

female_path = Path(r"D:\EduDub_Advanced_Template\edudub\female_embedding.npy")
male_path = Path(r"D:\EduDub_Advanced_Template\edudub\male_embedding.npy")

def check_file(path):
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return None
    try:
        arr = np.load(path)
        if arr is None:
            print(f"[ERROR] Loaded array is None: {path}")
            return None
        if arr.ndim == 2:
            arr = arr.mean(axis=0)  # Average multiple embeddings
            print(f"[OK] {path.name} loaded & averaged to shape: {arr.shape}")
        else:
            print(f"[OK] {path.name} loaded. Shape: {arr.shape}")
        return arr
    except Exception as e:
        print(f"[ERROR] Could not load {path.name}: {e}")
        return None

if __name__ == "__main__":
    female_proto = check_file(female_path)
    male_proto = check_file(male_path)

    if female_proto is not None and male_proto is not None:
        test_embedding = np.random.rand(*female_proto.shape)
        sim_female = np.dot(test_embedding, female_proto) / (np.linalg.norm(test_embedding) * np.linalg.norm(female_proto))
        sim_male = np.dot(test_embedding, male_proto) / (np.linalg.norm(test_embedding) * np.linalg.norm(male_proto))

        print(f"[TEST] sim_female: {sim_female:.2f}, sim_male: {sim_male:.2f}")
    else:
        print("[WARNING] One or both prototype files are missing or invalid.")
