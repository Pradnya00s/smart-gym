# backend/exercises/lat_pulldown.py
from typing import Dict, List, Any, Optional
import math

from .base import BaseExerciseSession
from backend.utils.angles import angle_3pts

# MediaPipe indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
NOSE = 0  # for chin-level reference


class LatPulldownSession(BaseExerciseSession):
    """
    Lat Pull-Down logic:
      - Rep counting based on bar height (wrist y-position)
      - Form checks:
          * Lean-back control
          * Elbow path (moving straight down)
          * Not pulling below chin level
          * Shoulder elevation (shrug)
    """

    def __init__(self):
        super().__init__(name="Lat pull-down", angle_history_size=5)

        # Rep thresholds: based on bar (wrist) vertical position
        self.hand_top_y: Optional[float] = None   # set first frame
        self.bottom_fraction: float = 0.25        # % of range from top to bottom position
        self.state: str = "TOP"

        # Lean-back threshold (degrees)
        self.max_lean_deg: float = 25.0

        # Shoulder elevation tolerance
        self.max_shoulder_lift: float = 0.05

        # Elbow flaring / path
        self.max_elbow_drift_x: float = 0.08

    # ---------- helpers ----------

    def _pt(self, keypoints: List[Dict[str, float]], idx: int):
        lm = keypoints[idx]
        return (lm["x"], lm["y"])

    def _avg_pt(self, keypoints, idx1, idx2):
        p1 = self._pt(keypoints, idx1)
        p2 = self._pt(keypoints, idx2)
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    # ---------- main update ----------

    def update(self, keypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        issues = []
        extra = {}

        # Keypoints
        shoulder_center = self._avg_pt(keypoints, LEFT_SHOULDER, RIGHT_SHOULDER)
        elbow_center = self._avg_pt(keypoints, LEFT_ELBOW, RIGHT_ELBOW)
        wrist_center = self._avg_pt(keypoints, LEFT_WRIST, RIGHT_WRIST)
        nose_pt = self._pt(keypoints, NOSE)

        sh_x, sh_y = shoulder_center
        wr_x, wr_y = wrist_center
        el_x, el_y = elbow_center

        # Initialize the top-hand position on first frame
        if self.hand_top_y is None:
            self.hand_top_y = wr_y

        # --- Rep Logic Based on Wrist Vertical Movement ---

        total_range = abs(wr_y - self.hand_top_y)
        bottom_threshold = self.hand_top_y + self.bottom_fraction * (
            total_range if total_range > 0 else 0.25
        )

        extra["hand_top_y"] = self.hand_top_y
        extra["current_wrist_y"] = wr_y
        extra["bottom_threshold_y"] = bottom_threshold

        # State machine:
        # TOP → moving down → BOTTOM → moving up → TOP

        if self.state == "TOP":
            if wr_y > bottom_threshold:
                self.state = "BOTTOM"
        elif self.state == "BOTTOM":
            if wr_y <= self.hand_top_y + 0.02:  # close to top again
                self.rep_count += 1
                self.state = "TOP"

        extra["state"] = self.state

        # --- FORM CHECKS ---

        # 1️⃣ Lean-back control
        # Torso is shoulder_center -> midpoint between hips (approx shoulder vertical line)
        # Lean-back measured by horizontal displacement of shoulders vs wrists
        torso_vertical = (0, 1)
        torso_vec = (wrist_center[0] - shoulder_center[0], wrist_center[1] - shoulder_center[1])

        # angle between torso_vec and vertical
        tv_len = math.sqrt(torso_vec[0] ** 2 + torso_vec[1] ** 2)
        if tv_len > 0:
            dot = torso_vec[0] * torso_vertical[0] + torso_vec[1] * torso_vertical[1]
            cosang = max(min(dot / tv_len, 1.0), -1.0)
            lean_deg = math.degrees(math.acos(abs(cosang)))
        else:
            lean_deg = 0.0

        extra["lean_deg"] = lean_deg

        if lean_deg > self.max_lean_deg:
            issues.append("Avoid leaning back excessively – stay more upright.")

        # 2️⃣ Elbow path (vertical)
        elbow_drift_x = abs(el_x - sh_x)
        extra["elbow_drift_x"] = elbow_drift_x
        if elbow_drift_x > self.max_elbow_drift_x:
            issues.append("Keep elbows closer to your sides – pull straight down.")

        # 3️⃣ Not pulling below chin level
        if wr_y < nose_pt[1] - 0.03:  # wrist too high above chin
            issues.append("Pull the bar only to chin level – not lower.")

        # 4️⃣ Shoulder elevation (shrugging up)
        shoulder_height = sh_y
        elbow_height = el_y
        extra["shoulder_elevation"] = shoulder_height - elbow_height

        if shoulder_height < elbow_height - self.max_shoulder_lift:
            issues.append("Relax your shoulders – avoid shrugging during the pull.")

        # Pack output
        return {
            "rep_count": self.rep_count,
            "issues": issues,
            "extra": extra,
        }
