# backend/exercises/bench_press.py
from typing import Dict, List, Any, Optional
import math

from .base import BaseExerciseSession
from utils.angles import angle_3pts

# MediaPipe indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16


class BenchPressSession(BaseExerciseSession):
    """
    Bench press logic:
      - Rep counting using elbow angle (top/bottom positions)
      - Form checks:
          * Elbow flaring (upper arm vs torso)
          * Bar path (hands moving too far horizontally)
          * Range of motion (bar not going low enough)
    """

    def __init__(self):
        super().__init__(name="Bench press", angle_history_size=5)

        # Rep thresholds (tune experimentally)
        self.elbow_angle_top: float = 160.0   # arms almost straight
        self.elbow_angle_bottom: float = 80.0 # bar near chest

        self.state: str = "TOP"

        # ROM: how low should the bar go compared to shoulders (normalized y-distance)
        self.min_bar_drop: float = 0.06  # tweak based on testing

        # Elbow flare threshold (angle between upper arm and torso)
        self.max_elbow_flare_deg: float = 70.0

        # Bar path horizontal deviation from "midline"
        self.max_bar_horizontal_drift: float = 0.08

        # For bar path, store reference midline (hands over mid-chest at start)
        self._ref_hand_mid_x: Optional[float] = None

        # Track min elbow angle & max bar drop in current rep for ROM feedback
        self._current_rep_min_elbow_angle: Optional[float] = None
        self._current_rep_max_drop: float = 0.0

    # ---------- helpers ----------

    def _pt(self, keypoints, idx):
        lm = keypoints[idx]
        return (lm["x"], lm["y"])

    def _avg_pt(self, keypoints, idx1, idx2):
        p1 = self._pt(keypoints, idx1)
        p2 = self._pt(keypoints, idx2)
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    # ---------- main update ----------

    def update(self, keypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        issues: List[str] = []
        extra: Dict[str, Any] = {}

        # Key points
        left_shoulder = self._pt(keypoints, LEFT_SHOULDER)
        right_shoulder = self._pt(keypoints, RIGHT_SHOULDER)
        left_elbow = self._pt(keypoints, LEFT_ELBOW)
        right_elbow = self._pt(keypoints, RIGHT_ELBOW)
        left_wrist = self._pt(keypoints, LEFT_WRIST)
        right_wrist = self._pt(keypoints, RIGHT_WRIST)

        shoulder_center = self._avg_pt(keypoints, LEFT_SHOULDER, RIGHT_SHOULDER)
        hand_center = self._avg_pt(keypoints, LEFT_WRIST, RIGHT_WRIST)

        # Init bar midline reference on first frame
        if self._ref_hand_mid_x is None:
            self._ref_hand_mid_x = hand_center[0]

        # --- Elbow angle for reps (average of both arms) ---
        left_elbow_angle = angle_3pts(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = angle_3pts(right_shoulder, right_elbow, right_wrist)

        if left_elbow_angle is None or right_elbow_angle is None:
            issues.append("Elbows not clearly visible.")
            return {"rep_count": self.rep_count, "issues": issues, "extra": extra}

        elbow_angle = (left_elbow_angle + right_elbow_angle) / 2.0
        self.angle_history.append(elbow_angle)
        extra["elbow_angle"] = elbow_angle

        # Track rep ROM
        if self._current_rep_min_elbow_angle is None or elbow_angle < self._current_rep_min_elbow_angle:
            self._current_rep_min_elbow_angle = elbow_angle

        # Bar vertical drop relative to shoulders (y increases downward)
        bar_drop = hand_center[1] - shoulder_center[1]
        self._current_rep_max_drop = max(self._current_rep_max_drop, bar_drop)
        extra["bar_drop"] = bar_drop

        # --- Rep state machine ---
        if self.state == "TOP":
            # Going down
            if elbow_angle < self.elbow_angle_bottom:
                self.state = "BOTTOM"
        elif self.state == "BOTTOM":
            # Coming back up
            if elbow_angle > self.elbow_angle_top:
                self.rep_count += 1
                self.state = "TOP"

                # ROM feedback on completed rep
                if self._current_rep_min_elbow_angle is not None and \
                   self._current_rep_min_elbow_angle > self.elbow_angle_bottom + 10.0:
                    issues.append("Lower the bar more for a full range of motion.")

                if self._current_rep_max_drop < self.min_bar_drop:
                    issues.append("Bring the bar closer to your chest at the bottom of the rep.")

                # Reset counters for next rep
                self._current_rep_min_elbow_angle = None
                self._current_rep_max_drop = 0.0

        extra["state"] = self.state

        # --- FORM CHECKS ---

        # 1) Elbow flaring: angle between upper arm and torso
        # For each side: angle at shoulder between torso (hip direction) & upper arm (elbow direction).
        # We approximate torso direction using the line between the two shoulders.
        # Upper arm vector: shoulder -> elbow.
        torso_vec = (
            right_shoulder[0] - left_shoulder[0],
            right_shoulder[1] - left_shoulder[1],
        )
        torso_len = math.sqrt(torso_vec[0] ** 2 + torso_vec[1] ** 2)
        if torso_len == 0:
            torso_unit = (1.0, 0.0)
        else:
            torso_unit = (torso_vec[0] / torso_len, torso_vec[1] / torso_len)

        def upper_arm_flare(shoulder, elbow):
            ua_vec = (elbow[0] - shoulder[0], elbow[1] - shoulder[1])
            ua_len = math.sqrt(ua_vec[0] ** 2 + ua_vec[1] ** 2)
            if ua_len == 0:
                return 0.0
            ua_unit = (ua_vec[0] / ua_len, ua_vec[1] / ua_len)
            dot = ua_unit[0] * torso_unit[0] + ua_unit[1] * torso_unit[1]
            cosang = max(min(dot, 1.0), -1.0)
            return math.degrees(math.acos(cosang))

        left_flare = upper_arm_flare(left_shoulder, left_elbow)
        right_flare = upper_arm_flare(right_shoulder, right_elbow)
        avg_flare = (left_flare + right_flare) / 2.0
        extra["elbow_flare_deg"] = avg_flare

        if avg_flare > self.max_elbow_flare_deg:
            issues.append("Tuck your elbows slightly – avoid excessive flaring out to the sides.")

        # 2) Bar path horizontal drift from reference midline
        bar_horizontal_drift = abs(hand_center[0] - self._ref_hand_mid_x)
        extra["bar_horizontal_drift"] = bar_horizontal_drift

        if bar_horizontal_drift > self.max_bar_horizontal_drift:
            issues.append("Press the bar in a more controlled, straight path over your mid-chest.")

        return {
            "rep_count": self.rep_count,
            "issues": issues,
            "extra": extra,
        }
