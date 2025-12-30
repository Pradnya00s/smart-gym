# backend/exercises/deadlift.py
from typing import Dict, List, Any, Optional
import math

from .base import BaseExerciseSession
from backend.utils.angles import angle_3pts

# MediaPipe indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_WRIST = 15
RIGHT_WRIST = 16


class DeadliftSession(BaseExerciseSession):
    """
    Deadlift logic:
      - Rep counting based on hip & knee angles (top/bottom positions)
      - Form checks:
          * Neutral spine (avoid rounding back)
          * Hip hinge vs. excessive knee bend (turning it into a squat)
          * Bar path close to body (hands close to shins)
          * Knee position (avoid knees drifting too far forward)
    """

    def __init__(self):
        super().__init__(name="Deadlift", angle_history_size=5)

        # Rep thresholds (tune experimentally)
        self.hip_angle_top: float = 160.0   # near full extension
        self.hip_angle_bottom: float = 70.0 # hinged over

        self.state: str = "TOP"  # assume starting standing

        # Spine / torso thresholds
        self.max_back_round_deg: float = 45.0  # angle from neutral we tolerate

        # Knee flex threshold to detect "too squatty"
        self.max_knee_bend_for_deadlift: float = 120.0  # smaller angle = more bend

        # Bar path thresholds (distance hands->ankles)
        self.max_bar_distance_normalized: float = 0.12  # tweak as needed

    # ---------- helpers ----------

    def _pt(self, keypoints: List[Dict[str, float]], idx: int):
        lm = keypoints[idx]
        return (lm["x"], lm["y"])

    def _avg_pt(self, keypoints: List[Dict[str, float]], idx1: int, idx2: int):
        p1 = self._pt(keypoints, idx1)
        p2 = self._pt(keypoints, idx2)
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    # ---------- main update ----------

    def update(self, keypoints: List[Dict[str, float]]) -> Dict[str, Any]:
        issues: List[str] = []
        extra: Dict[str, Any] = {}

        # --- key joints ---
        left_hip = self._pt(keypoints, LEFT_HIP)
        right_hip = self._pt(keypoints, RIGHT_HIP)
        left_knee = self._pt(keypoints, LEFT_KNEE)
        right_knee = self._pt(keypoints, RIGHT_KNEE)
        left_ankle = self._pt(keypoints, LEFT_ANKLE)
        right_ankle = self._pt(keypoints, RIGHT_ANKLE)
        left_shoulder = self._pt(keypoints, LEFT_SHOULDER)
        right_shoulder = self._pt(keypoints, RIGHT_SHOULDER)
        left_wrist = self._pt(keypoints, LEFT_WRIST)
        right_wrist = self._pt(keypoints, RIGHT_WRIST)

        hip_center = self._avg_pt(keypoints, LEFT_HIP, RIGHT_HIP)
        knee_center = self._avg_pt(keypoints, LEFT_KNEE, RIGHT_KNEE)
        ankle_center = self._avg_pt(keypoints, LEFT_ANKLE, RIGHT_ANKLE)
        shoulder_center = self._avg_pt(keypoints, LEFT_SHOULDER, RIGHT_SHOULDER)
        hand_center = self._avg_pt(keypoints, LEFT_WRIST, RIGHT_WRIST)

        # --- angles: hip & knee ---

        # Hip angle: shoulder - hip - knee
        left_hip_angle = angle_3pts(left_shoulder, left_hip, left_knee)
        right_hip_angle = angle_3pts(right_shoulder, right_hip, right_knee)
        # Knee angle: hip - knee - ankle
        left_knee_angle = angle_3pts(left_hip, left_knee, left_ankle)
        right_knee_angle = angle_3pts(right_hip, right_knee, right_ankle)

        if (
            left_hip_angle is None
            or right_hip_angle is None
            or left_knee_angle is None
            or right_knee_angle is None
        ):
            issues.append("Key joints not clearly visible.")
            return {
                "rep_count": self.rep_count,
                "issues": issues,
                "extra": extra,
            }

        hip_angle = (left_hip_angle + right_hip_angle) / 2.0
        knee_angle = (left_knee_angle + right_knee_angle) / 2.0

        self.angle_history.append(hip_angle)

        extra["hip_angle"] = hip_angle
        extra["knee_angle"] = knee_angle

        # --- Rep state machine ---
        # TOP (standing) → BOTTOM (hinged) → TOP
        if self.state == "TOP":
            if hip_angle < self.hip_angle_bottom:
                self.state = "BOTTOM"
        elif self.state == "BOTTOM":
            if hip_angle > self.hip_angle_top:
                self.rep_count += 1
                self.state = "TOP"

        extra["state"] = self.state

        # --- Form checks ---

        # 1) Neutral spine / torso angle
        # Torso: shoulder_center -> hip_center
        torso_vec = (
            hip_center[0] - shoulder_center[0],
            hip_center[1] - shoulder_center[1],
        )
        torso_len = math.sqrt(torso_vec[0] ** 2 + torso_vec[1] ** 2)

        # "Neutral" reference: a straight line from hip to ankle (general body line)
        body_vec = (
            ankle_center[0] - hip_center[0],
            ankle_center[1] - hip_center[1],
        )
        body_len = math.sqrt(body_vec[0] ** 2 + body_vec[1] ** 2)

        if torso_len > 0 and body_len > 0:
            dot = torso_vec[0] * body_vec[0] + torso_vec[1] * body_vec[1]
            cosang = max(min(dot / (torso_len * body_len), 1.0), -1.0)
            spine_angle = math.degrees(math.acos(cosang))
        else:
            spine_angle = 0.0

        extra["spine_angle_deg"] = spine_angle

        if spine_angle > self.max_back_round_deg:
            issues.append("Keep a neutral spine – avoid rounding your back during the lift.")

        # 2) Hip hinge vs squatty pattern
        # Deadlift: more hip hinge, moderate knee bend.
        # If knees are too bent (angle much smaller), cue more hip hinge.
        if knee_angle < self.max_knee_bend_for_deadlift:
            issues.append("Push your hips back more – avoid turning deadlifts into squats.")

        # 3) Bar path close to body
        # Distance between hand_center and ankle_center:
        bar_dx = abs(hand_center[0] - ankle_center[0])
        bar_dy = abs(hand_center[1] - ankle_center[1])
        bar_distance = math.sqrt(bar_dx**2 + bar_dy**2)
        extra["bar_distance"] = bar_distance

        if bar_distance > self.max_bar_distance_normalized:
            issues.append("Keep the bar closer to your body – slide it along your legs/shins.")

        # 4) Knee forward position (2D approximation)
        # If knee is significantly in front of ankle in x-direction, cue:
        knee_forward = abs(knee_center[0] - ankle_center[0])
        extra["knee_forward_offset"] = knee_forward

        if knee_forward > 0.08:  # tweak threshold
            issues.append("Avoid pushing your knees too far forward; focus on hinging at the hips.")

        return {
            "rep_count": self.rep_count,
            "issues": issues,
            "extra": extra,
        }
