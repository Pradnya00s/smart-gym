# backend/exercises/plank.py
from typing import Dict, List, Any, Optional
import math
import time

from .base import BaseExerciseSession

# MediaPipe indices
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
NOSE = 0  # rough head / neck reference


class PlankSession(BaseExerciseSession):
    """
    Plank exercise logic:
      - No reps; we care about:
          * Time held (seconds)
          * Posture score (0-100)
          * Form issues:
              - Hip too high/low
              - Shoulders not over elbows
              - Neck not neutral
    """

    def __init__(self):
        super().__init__(name="Plank", angle_history_size=5)

        # posture score between 0 and 100
        self.posture_score: float = 100.0

        # Internal: accumulate penalties per frame
        self._total_penalty: float = 0.0
        self._frame_count: int = 0

        # thresholds (tweak later)
        self.hip_high_thresh: float = -0.05  # relative offset vs torso line
        self.hip_low_thresh: float = 0.05

        self.max_neck_angle_deg: float = 20.0
        self.max_shoulder_elbow_offset_x: float = 0.08  # normalized

    # ---------- helpers ----------

    def _pt(self, keypoints: List[Dict[str, float]], idx: int):
        lm = keypoints[idx]
        return (lm["x"], lm["y"])

    def _avg_pt(self, keypoints: List[Dict[str, float]], idx1: int, idx2: int):
        p1 = self._pt(keypoints, idx1)
        p2 = self._pt(keypoints, idx2)
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    def _angle_between(self, v1, v2) -> float:
        """
        Angle between two 2D vectors in degrees.
        """
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

        # Timer: how long they have been in this plank session
        elapsed = self.elapsed_seconds
        extra["elapsed_seconds"] = elapsed

        # --- compute main reference points ---
        shoulders = self._avg_pt(keypoints, LEFT_SHOULDER, RIGHT_SHOULDER)
        hips = self._avg_pt(keypoints, LEFT_HIP, RIGHT_HIP)
        ankles = self._avg_pt(keypoints, LEFT_ANKLE, RIGHT_ANKLE)
        elbows = self._avg_pt(keypoints, LEFT_ELBOW, RIGHT_ELBOW)
        wrists = self._avg_pt(keypoints, LEFT_WRIST, RIGHT_WRIST)
        head = self._pt(keypoints, NOSE)

        # Torso line (shoulder -> hip)
        torso_vec = (hips[0] - shoulders[0], hips[1] - shoulders[1])

        # Body line (shoulder -> ankle)
        body_vec = (ankles[0] - shoulders[0], ankles[1] - shoulders[1])

        # --- HIP HEIGHT: too high / too low ---
        # We measure hip deviation from the straight line between shoulders and ankles.
        # Parametric projection: project hip onto shoulder-ankle segment.
        sx, sy = shoulders
        ax, ay = ankles
        hx, hy = hips

        bax = ax - sx
        bay = ay - sy
        body_len_sq = bax * bax + bay * bay
        hip_offset = 0.0

        if body_len_sq > 0:
            t = ((hx - sx) * bax + (hy - sy) * bay) / body_len_sq
            # projected point on the line
            px = sx + t * bax
            py = sy + t * bay
            # vertical offset of hip from line (in y, normalized coords)
            hip_offset = hy - py  # +ve: hip lower, -ve: hip higher

        extra["hip_offset"] = hip_offset

        penalty = 0.0

        if hip_offset < self.hip_high_thresh:
            issues.append("Your hips are too high – lower them to form a straight line.")
            penalty += 0.8
        elif hip_offset > self.hip_low_thresh:
            issues.append("Your hips are sagging – lift them to keep your body straight.")
            penalty += 0.8

        # --- SHOULDER-ELBOW ALIGNMENT ---
        # Shoulders should be roughly above elbows in x-position.
        shoulder_elbow_dx = abs(shoulders[0] - elbows[0])
        extra["shoulder_elbow_dx"] = shoulder_elbow_dx

        if shoulder_elbow_dx > self.max_shoulder_elbow_offset_x:
            issues.append("Align your shoulders directly above your elbows.")
            penalty += 0.5

        # --- NECK ALIGNMENT ---
        # Compare head direction vs torso direction.
        neck_vec = (head[0] - shoulders[0], head[1] - shoulders[1])
        neck_angle = self._angle_between(neck_vec, torso_vec)
        extra["neck_angle_deg"] = neck_angle

        if neck_angle > self.max_neck_angle_deg:
            issues.append("Keep your neck neutral – look slightly ahead or down.")
            penalty += 0.4

        # --- Update posture score ---
        self._frame_count += 1
        self._total_penalty += penalty

        # Compute score: start από 100, subtract scaled avg penalty
        if self._frame_count > 0:
            avg_penalty = self._total_penalty / self._frame_count
            # scale factor so reasonable penalties lead to scores around 60–95
            self.posture_score = max(40.0, min(100.0, 100.0 - avg_penalty * 15.0))

        extra["posture_score"] = self.posture_score

        # Plank: no reps
        extra["notes"] = "Plank: focus on time & posture, not reps."

        return {
            "rep_count": self.rep_count,  # will stay 0
            "issues": issues,
            "extra": extra,
        }
