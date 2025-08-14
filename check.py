import os
import numpy as np

def verify_embedding(npy_path, label):
    if not os.path.exists(npy_path):
        print(f"[❌] {label} embedding file not found at: {npy_path}")
        return False

    try:
        emb = np.load(npy_path)

        # Check shape
        if emb.ndim != 2 or emb.shape[1] != 512:
            print(f"[❌] {label} embedding has invalid shape: {emb.shape}")
            return False

        # Check for NaNs or all-zeros
        if np.isnan(emb).any():
            print(f"[❌] {label} embedding contains NaNs.")
            return False

        if np.all(emb == 0):
            print(f"[❌] {label} embedding is all zeros.")
            return False

        print(f"[✅] {label} embedding is valid. Shape: {emb.shape}")
        return True

    except Exception as e:
        print(f"[❌] Failed to load {label} embedding: {e}")
        return False


# --- Check both embeddings ---
verify_embedding("D:\EduDub_Advanced_Template\edudub\male_embedding2.npy", "Male")
verify_embedding("D:\\EduDub_Advanced_Template\\edudub\\female_embedding.npy", "Female")
