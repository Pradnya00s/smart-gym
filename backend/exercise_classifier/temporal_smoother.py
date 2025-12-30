from collections import deque
from typing import Optional


class TemporalExerciseSmoother:
    """
    Stabilizes exercise predictions using temporal majority voting.
    """

    def __init__(self, window_size: int = 7, min_agreement: float = 0.6):
        """
        window_size: number of recent predictions to consider
        min_agreement: fraction of same-label votes required
        """
        self.window_size = window_size
        self.min_agreement = min_agreement
        self.buffer = deque(maxlen=window_size)

    def update(self, prediction: Optional[str]) -> Optional[str]:
        """
        Add a new prediction and return a stabilized label or None.
        """

        # Ignore None predictions (idle / rejected)
        if prediction is None:
            self.buffer.clear()
            return None

        self.buffer.append(prediction)

        # Count votes
        counts = {}
        for p in self.buffer:
            counts[p] = counts.get(p, 0) + 1

        label, freq = max(counts.items(), key=lambda x: x[1])

        if freq / len(self.buffer) >= self.min_agreement:
            return label

        return None
