import joblib
import numpy as np
from typing import Optional


class ExerciseClassifier:
    """
    Exercise classifier with confidence-based rejection.
    """

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.6,
        reject_label: Optional[str] = None,
    ):
        self.model = joblib.load(model_path)
        self.confidence_threshold = confidence_threshold
        self.reject_label = reject_label

        # sanity check
        if not hasattr(self.model, "predict_proba"):
            raise ValueError(
                "Loaded model does not support predict_proba(). "
                "Use a probabilistic classifier (e.g., RandomForest)."
            )

    def predict(self, X):
        """
        Returns:
          - class label if confident
          - reject_label (None) if not confident
        """
        probs = self.model.predict_proba(X)  # shape: (1, n_classes)
        max_prob = float(np.max(probs))
        pred_idx = int(np.argmax(probs))

        if max_prob < self.confidence_threshold:
            return self.reject_label

        return self.model.classes_[pred_idx]
