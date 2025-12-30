# backend/exercises/base.py

from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, Dict, List, Any
import time

from backend.utils.smoothing import EMASmoother


class BaseExerciseSession(ABC):
    """
    Base class for an exercise session.
    Handles:
      - name
      - rep counting
      - simple angle history
      - timing (for things like planks)
      - angle smoothing helper
    """

    def __init__(self, name: str, angle_history_size: int = 5):
        self.name = name
        self.rep_count: int = 0
        self.state: str = "INIT"
        self.angle_history: Deque[float] = deque(maxlen=angle_history_size)
        self.started_at: float = time.time()
        self.last_update_ts: float = self.started_at

        # Smooth noisy angle values (e.g. knee, elbow) per exercise
        self.angle_smoother = EMASmoother(alpha=0.18)

    @abstractmethod
    def update(self, keypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Called once per frame with the current pose keypoints.

        Parameters
        ----------
        keypoints : list[dict]
            MediaPipe-style keypoints:
            [
              {"x": float, "y": float, "z": float, "visibility": float},
              ...
            ]

        Returns
        -------
        dict:
            {
              "rep_count": int,
              "issues": list[str],
              "extra": dict
            }
        """
        raise NotImplementedError

    @property
    def elapsed_seconds(self) -> float:
        """Seconds since session started."""
        return time.time() - self.started_at
