# backend/exercise_classifier/features.py

from typing import Dict, List
import math
import numpy as np

from backend.utils.angles import angle_3pts

# MediaPipe indices
NOSE = 0
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


def _pt(kps: List[Dict[str, float]], idx: int):
    lm = kps[idx]
    return lm["x"], lm["y"]


def _avg_pt(kps: List[Dict[str, float]], i1: int, i2: int):
    x1, y1 = _pt(kps, i1)
    x2, y2 = _pt(kps, i2)
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def _dist(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def extract_angle_features(keypoints: List[Dict[str, float]]) -> Dict[str, float]:
    """Key joint angles used for classification."""

    ls = _pt(keypoints, LEFT_SHOULDER)
    rs = _pt(keypoints, RIGHT_SHOULDER)
    le = _pt(keypoints, LEFT_ELBOW)
    re = _pt(keypoints, RIGHT_ELBOW)
    lw = _pt(keypoints, LEFT_WRIST)
    rw = _pt(keypoints, RIGHT_WRIST)
    lh = _pt(keypoints, LEFT_HIP)
    rh = _pt(keypoints, RIGHT_HIP)
    lk = _pt(keypoints, LEFT_KNEE)
    rk = _pt(keypoints, RIGHT_KNEE)
    la = _pt(keypoints, LEFT_ANKLE)
    ra = _pt(keypoints, RIGHT_ANKLE)

    # Elbows
    left_elbow = angle_3pts(ls, le, lw)
    right_elbow = angle_3pts(rs, re, rw)

    # Knees
    left_knee = angle_3pts(lh, lk, la)
    right_knee = angle_3pts(rh, rk, ra)

    # Hips: shoulder-hip-knee
    left_hip = angle_3pts(ls, lh, lk)
    right_hip = angle_3pts(rs, rh, rk)

    # Shoulders: elbow-shoulder-hip
    left_shoulder_angle = angle_3pts(le, ls, lh)
    right_shoulder_angle = angle_3pts(re, rs, rh)

    # Basic safety for None
    def nz(x):
        return 0.0 if x is None else x

    return {
        "elbow_left": nz(left_elbow),
        "elbow_right": nz(right_elbow),
        "knee_left": nz(left_knee),
        "knee_right": nz(right_knee),
        "hip_left": nz(left_hip),
        "hip_right": nz(right_hip),
        "shoulder_left": nz(left_shoulder_angle),
        "shoulder_right": nz(right_shoulder_angle),
    }


def extract_position_features(keypoints: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Relative vertical/horizontal relationships of key joints,
    normalized by body height.
    """

    nose = _pt(keypoints, NOSE)
    shoulder_center = _avg_pt(keypoints, LEFT_SHOULDER, RIGHT_SHOULDER)
    hip_center = _avg_pt(keypoints, LEFT_HIP, RIGHT_HIP)
    knee_center = _avg_pt(keypoints, LEFT_KNEE, RIGHT_KNEE)
    ankle_center = _avg_pt(keypoints, LEFT_ANKLE, RIGHT_ANKLE)
    wrist_center = _avg_pt(keypoints, LEFT_WRIST, RIGHT_WRIST)

    # Approximate body height (nose to ankles)
    body_height = _dist(nose, ankle_center) + 1e-6

    def norm_y(p):
        # vertical position normalized: 0 at nose, 1 at ankle
        return (p[1] - nose[1]) / body_height

    def norm_x(p):
        # horizontal relative to hip center
        return (p[0] - hip_center[0])

    return {
        "y_shoulder": norm_y(shoulder_center),
        "y_hip": norm_y(hip_center),
        "y_knee": norm_y(knee_center),
        "y_ankle": norm_y(ankle_center),
        "y_wrist": norm_y(wrist_center),
        "x_wrist_rel_hip": norm_x(wrist_center),
        "x_shoulder_rel_hip": norm_x(shoulder_center),
    }


FEATURE_NAMES = [
    # angles
    "elbow_left",
    "elbow_right",
    "knee_left",
    "knee_right",
    "hip_left",
    "hip_right",
    "shoulder_left",
    "shoulder_right",
    # positions
    "y_shoulder",
    "y_hip",
    "y_knee",
    "y_ankle",
    "y_wrist",
    "x_wrist_rel_hip",
    "x_shoulder_rel_hip",
]


def build_feature_vector(keypoints: List[Dict[str, float]]) -> np.ndarray:
    """
    Build a fixed-length numeric feature vector from MediaPipe keypoints.
    """
    ang = extract_angle_features(keypoints)
    pos = extract_position_features(keypoints)

    feats = []
    for name in FEATURE_NAMES:
        if name in ang:
            feats.append(ang[name])
        else:
            feats.append(pos[name])

    return np.array(feats, dtype=np.float32)
