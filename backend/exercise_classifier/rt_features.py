# backend/exercise_classifier/rt_features.py

import numpy as np
from backend.exercise_classifier.features import (
    FEATURE_NAMES,
    extract_angle_features,
    extract_position_features,
)


def extract_rt_features(keypoints):
    ang = extract_angle_features(keypoints)
    pos = extract_position_features(keypoints)

    feats = []
    for name in FEATURE_NAMES:
        if name in ang:
            feats.append(ang[name])
        else:
            feats.append(pos[name])

    return np.array(feats, dtype=np.float32)
