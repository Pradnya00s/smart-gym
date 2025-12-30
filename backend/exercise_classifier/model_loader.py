import os
import joblib
import requests

MODEL_URL = (
    "https://huggingface.co/pradnya00s/"
    "smart-gym-exercise-classifier/resolve/main/"
    "exercise_classifier.joblib"
)

LOCAL_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "exercise_classifier.joblib"
)


def load_exercise_model():
    """
    Downloads the model once (if missing) and loads it.
    Safe to call at startup.
    """
    if not os.path.exists(LOCAL_MODEL_PATH):
        print("[ML] Model not found locally. Downloading from Hugging Face...")
        response = requests.get(MODEL_URL, timeout=60)
        response.raise_for_status()

        with open(LOCAL_MODEL_PATH, "wb") as f:
            f.write(response.content)

        print("[ML] Model downloaded successfully.")

    print("[ML] Loading exercise classifier...")
    return joblib.load(LOCAL_MODEL_PATH)
