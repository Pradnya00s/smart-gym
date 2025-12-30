# backend/utils/smoothing.py
from collections import deque
from typing import List, Dict, Optional
import numpy as np


class EMASmoother:
    """
    Smooth a single float value (angle, distance) using exponential moving average.
    alpha = 0.2 → light smoothing
    alpha = 0.05 → heavy smoothing
    """
    def __init__(self, alpha: float = 0.2):
        self.alpha = alpha
        self.value: Optional[float] = None

    def update(self, new_v: float) -> float:
        if new_v is None:
            return self.value if self.value is not None else None
        if self.value is None:
            self.value = new_v
        else:
            self.value = self.alpha * new_v + (1 - self.alpha) * self.value
        return self.value


class RollingAverageSmoother:
    """
    Smooth x,y coordinates using a rolling average window.
    """
    def __init__(self, window: int = 5):
        self.window = window
        self.xs = deque(maxlen=window)
        self.ys = deque(maxlen=window)

    def update(self, x: float, y: float):
        self.xs.append(x)
        self.ys.append(y)
        return float(sum(self.xs)/len(self.xs)), float(sum(self.ys)/len(self.ys))


class VisibilityFilter:
    """
    Ensures stability of keypoints:
    - skip frames with low visibility
    - require stable visibility for N frames before accepting
    """
    def __init__(self, min_visibility: float = 0.5, stable_frames: int = 2):
        self.min_visibility = min_visibility
        self.stable_frames = stable_frames
        self.window = deque(maxlen=stable_frames)

    def update(self, visibility: float) -> bool:
        self.window.append(visibility >= self.min_visibility)
        return all(self.window)


def smooth_keypoints(keypoints: List[Dict[str, float]], smoothers: List[RollingAverageSmoother]):
    """
    Apply rolling average to each keypoint’s x,y.
    """
    for i, kp in enumerate(keypoints):
        smooth_x, smooth_y = smoothers[i].update(kp["x"], kp["y"])
        kp["x"], kp["y"] = smooth_x, smooth_y
    return keypoints
