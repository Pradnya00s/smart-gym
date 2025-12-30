# backend/pose/pose_detector.py

import mediapipe as mp
import cv2

class PoseDetector:
    def __init__(self):
        self.pose = mp.solutions.pose.Pose(
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

    def detect_keypoints(self, frame):
        """Returns list of 33 MediaPipe keypoints or None."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.pose.process(rgb)

        if not res.pose_landmarks:
            return None

        kps = []
        for lm in res.pose_landmarks.landmark:
            kps.append({
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
                "visibility": lm.visibility
            })
        return kps
