# backend/exercises/bicep_curl.py
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


class BicepCurlSession(BaseExerciseSession):
    """
    Bicep curls:
      - Rep counting using elbow angle (bottom/top positions)
      - Form checks:
          * Full extension at bottom
          * Full contraction at top
          * Shoulder swing (shoulders moving too much)
          * Wrist alignment (avoid excessive bending)
    """

    def __init__(self, side: str = "right"):
        """
        Parameters
        ----------
        side : 'left' or 'right'
            Which arm to track primarily. We still look at both for some checks.
        """
        super().__init__(name="Bicep curl", angle_history_size=5)

        side = side.lower()
        self.side = "left" if side == "left" else "right"

        # Choose indices based on side
        if self.side == "left":
            self.SHOULDER = LEFT_SHOULDER
            self.ELBOW = LEFT_ELBOW
            self.WRIST = LEFT_WRIST
        else:
            self.SHOULDER = RIGHT_SHOULDER
            self.ELBOW = RIGHT_ELBOW
            self.WRIST = RIGHT_WRIST

        # Rep thresholds (tune as needed)
        self.elbow_angle_bottom: float = 160.0  # arm almost straight
        self.elbow_angle_top: float = 50.0      # fully contracted

        self.state: str = "BOTTOM"  # start from extended position

        # For depth feedback:
        self._current_rep_min_angle: Optional[float] = None
        self._current_rep_max_angle: Optional[float] = None

        # Shoulder swing allowance (in normalized coordinates)
        self.max_shoulder_vertical_movement: float = 0.05
        self.max_shoulder_horizontal_movement: float = 0.05

        # Wrist alignment: max angle between forearm-hand segment and straight line
        self.max_wrist_bend_deg: float = 25.0

        # Reference shoulder position (to detect swing)
        self._ref_shoulder: Optional[tuple] = None

    # ---------- helpers ----------

    def _pt(self, keypoints: List[Dict[str, float]], idx: int):
        lm = keypoints[idx]
        return (lm["x"], lm["y"])

    def _vector(self, a, b):
        return (b[0] - a[0], b[1] - a[1])

    def _angle_between(self, v1, v2) -> float:
        x1, y1 = v1
        x2, y2 = v2
        mag1 = math.sqrt(x1 * x1 + y1 * y1)
        mag2 = math.sqrt(x2 * x2 + y2 * y2)
        if mag1 == 0 or mag2 == 0:
            return 0.0
        dot = x1 * x2 + y1 * y2
        cosang = max(min(dot / (mag1 * mag2), 1.0), -1.0)
        return math.degrees(math.acos(cosang))

    # ---------- main update ----------

    def update(self, keypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        issues: List[str] = []
        extra: Dict[str, Any] = {}

        shoulder = self._pt(keypoints, self.SHOULDER)
        elbow = self._pt(keypoints, self.ELBOW)
        wrist = self._pt(keypoints, self.WRIST)

        # Set reference shoulder position on first frame
        if self._ref_shoulder is None:
            self._ref_shoulder = shoulder

        # --- Elbow angle for reps ---
        elbow_angle = angle_3pts(shoulder, elbow, wrist)
        if elbow_angle is None:
            issues.append("Elbow not clearly visible.")
            return {"rep_count": self.rep_count, "issues": issues, "extra": extra}

        self.angle_history.append(elbow_angle)
        extra["elbow_angle"] = elbow_angle

        # Track min/max within current rep for form feedback
        if self._current_rep_min_angle is None or elbow_angle < self._current_rep_min_angle:
            self._current_rep_min_angle = elbow_angle
        if self._current_rep_max_angle is None or elbow_angle > self._current_rep_max_angle:
            self._current_rep_max_angle = elbow_angle

        # --- Rep state machine ---
        # BOTTOM (extended) → TOP (flexed) → BOTTOM
        if self.state == "BOTTOM":
            # going up: angle getting smaller (toward flexed)
            if elbow_angle < self.elbow_angle_top:
                self.state = "TOP"
        elif self.state == "TOP":
            # going back down: angle opening again
            if elbow_angle > self.elbow_angle_bottom:
                self.rep_count += 1
                self.state = "BOTTOM"

                # Form feedback for that completed rep
                if self._current_rep_max_angle is not None and self._current_rep_max_angle < 150.0:
                    issues.append("Fully extend your arm at the bottom of each rep.")
                if self._current_rep_min_angle is not None and self._current_rep_min_angle > 60.0:
                    issues.append("Curl higher – bring your hand closer to your shoulder.")

                # reset trackers
                self._current_rep_min_angle = None
                self._current_rep_max_angle = None

        extra["state"] = self.state

        # --- Shoulder swing detection ---
        if self._ref_shoulder is not None:
            dx = shoulder[0] - self._ref_shoulder[0]
            dy = shoulder[1] - self._ref_shoulder[1]
            extra["shoulder_dx"] = dx
            extra["shoulder_dy"] = dy

            if abs(dy) > self.max_shoulder_vertical_movement or abs(dx) > self.max_shoulder_horizontal_movement:
                issues.append("Avoid swinging your shoulder; keep your upper arm stable.")

        # --- Wrist alignment ---
        # Angle at wrist between vector elbow->wrist and a straight "vertical" forearm direction.
        # We approximate neutral wrist as forearm pointing roughly up/down.
        forearm_vec = self._vector(elbow, wrist)
        # vertical reference vector (pointing up)
        vertical_ref = (0.0, -1.0)
        wrist_bend = self._angle_between(forearm_vec, vertical_ref)
        extra["wrist_bend_deg"] = wrist_bend

        # we just check large deviations from "mostly vertical" as potentially bent
        if wrist_bend > (90 + self.max_wrist_bend_deg) or wrist_bend < (90 - self.max_wrist_bend_deg):
            issues.append("Keep your wrist neutral – avoid excessive bending while curling.")

        return {
            "rep_count": self.rep_count,
            "issues": issues,
            "extra": extra,
        }
