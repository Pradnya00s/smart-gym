# backend/exercise_classifier/train_classifier.py

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from .features import FEATURE_NAMES


def load_dataset(csv_path: str):
    """
    Expects a CSV with columns:
      - all FEATURE_NAMES
      - 'label' (string: 'squat', 'pushup', etc.)
    """
    df = pd.read_csv(csv_path)

    # Basic check
    missing = [f for f in FEATURE_NAMES if f not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in CSV: {missing}")

    if "label" not in df.columns:
        raise ValueError("CSV must contain a 'label' column.")

    X = df[FEATURE_NAMES].values.astype(np.float32)
    y = df["label"].astype(str).values

    return X, y


def train_and_save(
    csv_path: str,
    model_out_path: str = "exercise_classifier.joblib",
    n_estimators: int = 200,
    max_depth: int = None,
):
    X, y = load_dataset(csv_path)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
        n_jobs=-1,
    )

    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_val)
    print("Validation report:")
    print(classification_report(y_val, y_pred))

    joblib.dump(clf, model_out_path)
    print(f"Saved classifier to {model_out_path}")


if __name__ == "__main__":
    # Example usage:
    # python -m backend.exercise_classifier.train_classifier data/exercise_features.csv
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m backend.exercise_classifier.train_classifier <csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    train_and_save(csv_path)
