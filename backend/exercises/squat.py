# backend/exercises/squat.py
from typing import Dict, List, Any, Optional

from .base import BaseExerciseSession
from utils.angles import angle_3pts

# MediaPipe Pose landmark indices (BlazePose full body)
# Reference: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


class SquatSession(BaseExerciseSession):
    """
    Squat exercise logic:
      - Rep counting based on average knee angle
      - Basic form checks:
          * Depth
          * Back lean
          * Knee symmetry
    """

    def __init__(self):
        super().__init__(name="Squat", angle_history_size=5)

        # You can tune these thresholds experimentally
        self.knee_angle_up: float = 160.0    # standing almost straight
        self.knee_angle_down: float = 100.0  # bottom / parallel-ish
        self.state: str = "UP"               # assume starting from standing

        # Back angle thresholds
        self.max_forward_lean_deg: float = 45.0

        # How much asymmetry between left/right knees we tolerate (in degrees)
        self.max_knee_asymmetry_deg: float = 15.0

    # ---------- helper methods ----------

    def _pt(self, keypoints: List[Dict[str, float]], idx: int):
        """Return (x, y) tuple for a given landmark index."""
        lm = keypoints[idx]
        return (lm["x"], lm["y"])

    def _avg(self, a: Optional[float], b: Optional[float]) -> Optional[float]:
        if a is None or b is None:
            return None
        return (a + b) / 2.0

    # ---------- main update ----------

    def update(self, keypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        issues: List[str] = []
        extra: Dict[str, Any] = {}

        # --- compute knee angles (left + right) ---
        left_knee_angle = angle_3pts(
            self._pt(keypoints, LEFT_HIP),
            self._pt(keypoints, LEFT_KNEE),
            self._pt(keypoints, LEFT_ANKLE),
        )
        right_knee_angle = angle_3pts(
            self._pt(keypoints, RIGHT_HIP),
            self._pt(keypoints, RIGHT_KNEE),
            self._pt(keypoints, RIGHT_ANKLE),
        )

        if left_knee_angle is None or right_knee_angle is None:
            issues.append("Knee joints not clearly visible.")
            return {
                "rep_count": self.rep_count,
                "issues": issues,
                "extra": extra,
            }

        knee_angle = self._avg(left_knee_angle, right_knee_angle)
        if knee_angle is None:
            issues.append("Cannot compute knee angle.")
            return {
                "rep_count": self.rep_count,
                "issues": issues,
                "extra": extra,
            }

        # Save to history for possible smoothing later
        self.angle_history.append(knee_angle)

        # --- simple rep state machine ---
        # State "UP": user is standing / top
        if self.state == "UP":
            # They start going down into the squat
            if knee_angle < self.knee_angle_down:
                self.state = "DOWN"

        # State "DOWN": user is in bottom position
        elif self.state == "DOWN":
            # They come back up → count 1 rep
            if knee_angle > self.knee_angle_up:
                self.rep_count += 1
                self.state = "UP"

        extra["knee_angle"] = knee_angle
        extra["state"] = self.state

        # --- form checks ---

        # 1) Depth check at the "bottom"
        # If the knee angle is too large (not bent enough), encourage deeper squat.
        if knee_angle > 130:
            issues.append("Go deeper – bend your knees more for a full squat.")

        # 2) Back angle (forward lean)
        # Use the line from hips to shoulders to approximate torso.
        shoulder_center = (
            (keypoints[LEFT_SHOULDER]["x"] + keypoints[RIGHT_SHOULDER]["x"]) / 2.0,
            (keypoints[LEFT_SHOULDER]["y"] + keypoints[RIGHT_SHOULDER]["y"]) / 2.0,
        )
        hip_center = (
            (keypoints[LEFT_HIP]["x"] + keypoints[RIGHT_HIP]["x"]) / 2.0,
            (keypoints[LEFT_HIP]["y"] + keypoints[RIGHT_HIP]["y"]) / 2.0,
        )

        # Angle between torso vector and vertical
        # vertical reference: point straight up from hips
        import math

        torso_vec = (shoulder_center[0] - hip_center[0], shoulder_center[1] - hip_center[1])
        vertical_vec = (0.0, -1.0)  # up in normalized image space (y decreases upward)

        torso_len = math.sqrt(torso_vec[0] ** 2 + torso_vec[1] ** 2)
        if torso_len > 0:
            dot = torso_vec[0] * vertical_vec[0] + torso_vec[1] * vertical_vec[1]
            cosang = max(min(dot / torso_len, 1.0), -1.0)
            torso_angle_from_vertical = math.degrees(math.acos(cosang))
            extra["torso_angle_from_vertical"] = torso_angle_from_vertical

            if torso_angle_from_vertical > self.max_forward_lean_deg:
                issues.append("Try to keep your chest more upright – avoid leaning too far forward.")

        # 3) Knee asymmetry (valgus / one knee collapsing inward more)
        knee_diff = abs(left_knee_angle - right_knee_angle)
        extra["knee_angle_diff"] = knee_diff
        if knee_diff > self.max_knee_asymmetry_deg:
            issues.append("Keep both knees moving symmetrically – avoid letting one knee cave in.")

        return {
            "rep_count": self.rep_count,
            "issues": issues,
            "extra": extra,
        }



