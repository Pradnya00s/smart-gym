# backend/exercises/lunge.py
from typing import Dict, List, Any, Optional
import math

from .base import BaseExerciseSession
from utils.angles import angle_3pts

# MediaPipe indices
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12


class LungeSession(BaseExerciseSession):
    """
    Forward lunges:
      - Rep counting based on front-knee angle (down -> up)
      - Form checks:
          * Knee alignment (avoid valgus collapse)
          * Knee-over-toe (excessive forward travel)
          * Torso lean control
          * Hip alignment
          * Lateral sway (stability)
    """

    def __init__(self, side: str = "right"):
        """
        Parameters
        ----------
        side : 'left' or 'right'
            Which leg is stepping forward for reps.
        """
        super().__init__(name="Lunge", angle_history_size=5)

        side = side.lower()
        self.side = "left" if side == "left" else "right"

        # Assign indices depending on the selected forward leg
        if self.side == "left":
            self.FRONT_HIP = LEFT_HIP
            self.FRONT_KNEE = LEFT_KNEE
            self.FRONT_ANKLE = LEFT_ANKLE
            self.BACK_HIP = RIGHT_HIP
            self.BACK_KNEE = RIGHT_KNEE
            self.BACK_ANKLE = RIGHT_ANKLE
        else:
            self.FRONT_HIP = RIGHT_HIP
            self.FRONT_KNEE = RIGHT_KNEE
            self.FRONT_ANKLE = RIGHT_ANKLE
            self.BACK_HIP = LEFT_HIP
            self.BACK_KNEE = LEFT_KNEE
            self.BACK_ANKLE = LEFT_ANKLE

        # Rep thresholds (tune experimentally)
        self.knee_angle_top: float = 165.0    # Standing
        self.knee_angle_bottom: float = 90.0  # Deep lunge

        self.state: str = "TOP"

        # Form thresholds
        self.max_knee_valgus_offset: float = 0.05
        self.max_knee_over_toe_offset: float = 0.1
        self.max_torso_lean_deg: float = 35.0
        self.max_lateral_sway: float = 0.05

        # Reference vertical alignment for stability
        self._ref_shoulder_center = None

    # ---------- helpers ----------

    def _pt(self, keypoints, idx):
        lm = keypoints[idx]
        return (lm["x"], lm["y"])

    def _avg_pt(self, keypoints, idx1, idx2):
        p1 = self._pt(keypoints, idx1)
        p2 = self._pt(keypoints, idx2)
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    def _angle(self, a, b, c):
        return angle_3pts(a, b, c)

    # ---------- main update ----------

    def update(self, keypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        issues = []
        extra = {}

        shoulder_center = self._avg_pt(keypoints, LEFT_SHOULDER, RIGHT_SHOULDER)

        # Set reference shoulder for sway detection
        if self._ref_shoulder_center is None:
            self._ref_shoulder_center = shoulder_center

        # --- Extract points ---
        hip_f = self._pt(keypoints, self.FRONT_HIP)
        knee_f = self._pt(keypoints, self.FRONT_KNEE)
        ankle_f = self._pt(keypoints, self.FRONT_ANKLE)

        hip_b = self._pt(keypoints, self.BACK_HIP)
        knee_b = self._pt(keypoints, self.BACK_KNEE)
        ankle_b = self._pt(keypoints, self.BACK_ANKLE)

        # --- Angles ---
        # Front knee controls rep counting
        front_knee_angle = self._angle(hip_f, knee_f, ankle_f)
        if front_knee_angle is None:
            issues.append("Front knee not clearly visible.")
            return {"rep_count": self.rep_count, "issues": issues, "extra": extra}

        extra["front_knee_angle"] = front_knee_angle

        self.angle_history.append(front_knee_angle)

        # --- Rep state machine ---
        if self.state == "TOP":
            if front_knee_angle < self.knee_angle_bottom:
                self.state = "BOTTOM"
        elif self.state == "BOTTOM":
            if front_knee_angle > self.knee_angle_top:
                self.rep_count += 1
                self.state = "TOP"

        extra["state"] = self.state

        # --- FORM CHECKS ---

        # 1️⃣ Knee-over-toe (front knee shouldn't travel too far forward)
        knee_toe_offset = abs(knee_f[0] - ankle_f[0])
        extra["knee_over_toe_offset"] = knee_toe_offset
        if knee_toe_offset > self.max_knee_over_toe_offset:
            issues.append("Keep your front knee behind your toes when lowering.")

        # 2️⃣ Knee valgus (inward collapse)
        # Compare knee x-position to hip/ankle to detect sideways collapse
        hip_x = hip_f[0]
        knee_x = knee_f[0]
        ankle_x = ankle_f[0]

        # if knee is significantly inside the midline between hip and ankle
        mid_x = (hip_x + ankle_x) / 2.0
        valgus_offset = mid_x - knee_x
        extra["knee_valgus_offset"] = valgus_offset

        if abs(valgus_offset) > self.max_knee_valgus_offset:
            issues.append("Avoid knee valgus – keep your knee tracking straight.")

        # 3️⃣ Torso lean check:
        # Angle between torso and vertical
        torso_vec = (
            hip_f[0] - shoulder_center[0],
            hip_f[1] - shoulder_center[1]
        )

        # vertical reference (straight down)
        vertical_ref = (0, 1)

        # compute angle
        dot = torso_vec[0] * vertical_ref[0] + torso_vec[1] * vertical_ref[1]
        torso_len = math.sqrt(torso_vec[0]**2 + torso_vec[1]**2)
        if torso_len > 0:
            cosang = max(min(dot / torso_len, 1.0), -1.0)
            torso_angle_deg = math.degrees(math.acos(abs(cosang)))
        else:
            torso_angle_deg = 0.0

        extra["torso_angle_deg"] = torso_angle_deg

        if torso_angle_deg > self.max_torso_lean_deg:
            issues.append("Keep your torso upright; avoid leaning too far forward.")

        # 4️⃣ Stability (lateral sway)
        sway = abs(shoulder_center[0] - self._ref_shoulder_center[0])
        extra["lateral_sway"] = sway

        if sway > self.max_lateral_sway:
            issues.append("Try to stay balanced – reduce side-to-side movement.")

        return {
            "rep_count": self.rep_count,
            "issues": issues,
            "extra": extra,
        }
