# backend/exercise_classifier/autotrainer.py

import threading
import joblib
import time
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from backend.exercise_classifier.dataset_manager import DatasetManager
from backend.exercise_classifier.features import FEATURE_NAMES

MODEL_PATH = "backend/exercise_classifier/exercise_classifier.joblib"


class AutoTrainer:
    """
    Runs background retraining whenever new autolabel data is added.
    """

    _lock = threading.Lock()
    _scheduled = False

    def __init__(self):
        self.ds = DatasetManager()

    def schedule_retrain(self):
        """Start retraining in a separate thread (non-blocking)."""
        with self._lock:
            if not self._scheduled:
                self._scheduled = True
                t = threading.Thread(target=self._run_retrain)
                t.daemon = True
                t.start()

    def _run_retrain(self):
        time.sleep(2)  # short delay to accumulate multiple uploads

        print("[AutoTrainer] Retraining model with auto-collected data...")

        df = self.ds.merged()

        X = df[FEATURE_NAMES].values
        y = df["label"].values

        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=18,
            class_weight="balanced",
            n_jobs=-1
        )

        model.fit(X, y)
        joblib.dump(model, MODEL_PATH)

        print("[AutoTrainer] Model retrained & saved!")

        with self._lock:
            self._scheduled = False
