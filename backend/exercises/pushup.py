# backend/exercises/pushup.py
from typing import Dict, List, Any, Optional
import math

from .base import BaseExerciseSession
from backend.utils.angles import angle_3pts

# MediaPipe Pose landmark indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


class PushupSession(BaseExerciseSession):
    """
    Push-up exercise logic:
      - Rep counting using elbow angle (top/bottom positions)
      - Basic form checks:
          * Hip sag / pike
          * Depth (not going low enough)
          * Hand placement vs shoulder width
    """

    def __init__(self):
        super().__init__(name="Push-up", angle_history_size=5)

        # Rep thresholds (tune experimentally)
        self.elbow_angle_top: float = 160.0   # arms nearly straight
        self.elbow_angle_bottom: float = 90.0 # chest near bottom position

        self.state: str = "TOP"  # starting position

        # Hip alignment thresholds (relative vertical offset)
        self.hip_high_thresh: float = -0.05
        self.hip_low_thresh: float = 0.05

        # Depth threshold: if minimum elbow angle never gets below this, cue to go deeper
        self.min_depth_angle: float = 110.0

        # Hand placement thresholds (normalized distance)
        self.min_hand_width_factor: float = 0.8   # min multiple of shoulder width
        self.max_hand_width_factor: float = 1.5   # max multiple of shoulder width

        # Track min elbow angle within current rep (for depth feedback)
        self._current_rep_min_angle: Optional[float] = None

    # ---------- helpers ----------

    def _pt(self, keypoints: List[Dict[str, float]], idx: int):
        lm = keypoints[idx]
        return (lm["x"], lm["y"])

    def _avg_pt(self, keypoints: List[Dict[str, float]], idx1: int, idx2: int):
        p1 = self._pt(keypoints, idx1)
        p2 = self._pt(keypoints, idx2)
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    def _avg(self, a: float, b: float) -> float:
        return (a + b) / 2.0

    # ---------- main update ----------

    def update(self, keypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        issues: List[str] = []
        extra: Dict[str, Any] = {}

        # --- compute elbow angles (left + right) ---
        left_elbow_angle = angle_3pts(
            self._pt(keypoints, LEFT_SHOULDER),
            self._pt(keypoints, LEFT_ELBOW),
            self._pt(keypoints, LEFT_WRIST),
        )
        right_elbow_angle = angle_3pts(
            self._pt(keypoints, RIGHT_SHOULDER),
            self._pt(keypoints, RIGHT_ELBOW),
            self._pt(keypoints, RIGHT_WRIST),
        )

        if left_elbow_angle is None or right_elbow_angle is None:
            issues.append("Elbows not clearly visible.")
            return {
                "rep_count": self.rep_count,
                "issues": issues,
                "extra": extra,
            }

        elbow_angle = self._avg(left_elbow_angle, right_elbow_angle)
        self.angle_history.append(elbow_angle)

        extra["elbow_angle"] = elbow_angle

        # --- REP STATE MACHINE ---
        # TOP → going down → BOTTOM
        if self.state == "TOP":
            # user going down into push-up
            if elbow_angle < self.elbow_angle_bottom:
                self.state = "BOTTOM"
                # reset min angle tracker
                self._current_rep_min_angle = elbow_angle
        elif self.state == "BOTTOM":
            # track min angle while in bottom state
            if self._current_rep_min_angle is None or elbow_angle < self._current_rep_min_angle:
                self._current_rep_min_angle = elbow_angle

            # user coming back up → count rep when arms nearly straight
            if elbow_angle > self.elbow_angle_top:
                self.rep_count += 1
                self.state = "TOP"

                # Check depth for that completed rep
                if (
                    self._current_rep_min_angle is not None
                    and self._current_rep_min_angle > self.min_depth_angle
                ):
                    issues.append("Go lower – bend your elbows more for full push-ups.")
                # reset for next rep
                self._current_rep_min_angle = None

        extra["state"] = self.state

        # --- FORM CHECKS ---

        # 1) Hip sag / pike
        shoulders = self._avg_pt(keypoints, LEFT_SHOULDER, RIGHT_SHOULDER)
        hips = self._avg_pt(keypoints, LEFT_HIP, RIGHT_HIP)
        ankles = self._avg_pt(keypoints, LEFT_ANKLE, RIGHT_ANKLE)

        sx, sy = shoulders
        ax, ay = ankles
        hx, hy = hips

        bax = ax - sx
        bay = ay - sy
        body_len_sq = bax * bax + bay * bay
        hip_offset = 0.0

        if body_len_sq > 0:
            t = ((hx - sx) * bax + (hy - sy) * bay) / body_len_sq
            px = sx + t * bax
            py = sy + t * bay
            hip_offset = hy - py  # +ve: hips lower than line

        extra["hip_offset"] = hip_offset

        if hip_offset < self.hip_high_thresh:
            issues.append("Avoid piking – lower your hips to form a straight line.")
        elif hip_offset > self.hip_low_thresh:
            issues.append("Avoid sagging – tighten your core and lift your hips slightly.")

        # 2) Hand placement vs shoulder width
        left_shoulder = self._pt(keypoints, LEFT_SHOULDER)
        right_shoulder = self._pt(keypoints, RIGHT_SHOULDER)
        left_hand = self._pt(keypoints, LEFT_WRIST)
        right_hand = self._pt(keypoints, RIGHT_WRIST)

        shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
        hand_width = abs(right_hand[0] - left_hand[0])

        extra["shoulder_width"] = shoulder_width
        extra["hand_width"] = hand_width

        if shoulder_width > 0:
            width_ratio = hand_width / shoulder_width
            extra["hand_width_ratio"] = width_ratio

            if width_ratio < self.min_hand_width_factor:
                issues.append("Hands are too close – place them slightly wider than shoulders.")
            elif width_ratio > self.max_hand_width_factor:
                issues.append("Hands are too wide – bring them closer to shoulder-width.")

        return {
            "rep_count": self.rep_count,
            "issues": issues,
            "extra": extra,
        }
