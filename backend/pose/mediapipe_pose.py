# backend/pose/mediapipe_pose.py

import cv2
import mediapipe as mp

from backend.utils.smoothing import (
    RollingAverageSmoother,
    VisibilityFilter,
    smooth_keypoints,
)


class MediaPipePoseEstimator:
    """
    Wrapper around MediaPipe Pose.

    Usage:
        pose_estimator = MediaPipePoseEstimator()
        keypoints = pose_estimator.infer(frame_bgr)

    - infer(frame_bgr) -> list of 33 keypoints or None
      Each keypoint is a dict: {x, y, z, visibility}
      where x, y are normalized [0,1] in image coordinates.

    Optional smoothing:
      - Rolling average over landmark x,y coordinates
      - VisibilityFilter to avoid using unstable frames
    """

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        enable_segmentation: bool = False,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        enable_smoothing: bool = True,
        smoothing_window: int = 5,
        min_visibility: float = 0.5,
        stable_visibility_frames: int = 2,
    ):
        """
        Parameters
        ----------
        static_image_mode : bool
            False for video stream (recommended).
        model_complexity : int
            0, 1, or 2 – higher = more accurate but slower.
        enable_segmentation : bool
            If True, MediaPipe also returns segmentation mask (we don't use it here).
        min_detection_confidence : float
        min_tracking_confidence : float
        enable_smoothing : bool
            If True, apply coordinate smoothing + visibility gating.
        smoothing_window : int
            Rolling window size for coordinate smoothing.
        min_visibility : float
            Minimum average landmark visibility to accept a frame.
        stable_visibility_frames : int
            Number of consecutive frames above min_visibility before we trust output.
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            enable_segmentation=enable_segmentation,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self.enable_smoothing = enable_smoothing

        if enable_smoothing:
            # One smoother per landmark
            self.smoothers = [
                RollingAverageSmoother(window=smoothing_window) for _ in range(33)
            ]
            # VisibilityFilter operates on aggregated visibility
            self.visibility_filter = VisibilityFilter(
                min_visibility=min_visibility,
                stable_frames=stable_visibility_frames,
            )
        else:
            self.smoothers = None
            self.visibility_filter = None

    def infer(self, frame_bgr):
        """
        Run pose estimation on a BGR frame (as read by OpenCV).

        Returns
        -------
        None
            If no person detected or visibility not yet stable.
        list[dict]
            Otherwise, list of 33 keypoints:
            [
              {"x": float, "y": float, "z": float, "visibility": float},
              ...
            ]
        """
        if frame_bgr is None:
            return None

        # MediaPipe expects RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.pose.process(frame_rgb)

        if not result.pose_landmarks:
            return None

        landmarks = result.pose_landmarks.landmark

        # Build raw keypoints list
        keypoints = []
        vis_values = []
        for lm in landmarks:
            keypoints.append(
                {
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "visibility": lm.visibility,
                }
            )
            vis_values.append(lm.visibility)

        # Optional smoothing + visibility gating
        if self.enable_smoothing and self.smoothers is not None:
            # Use mean visibility as a simple stability metric
            mean_vis = sum(vis_values) / len(vis_values)

            # VisibilityFilter enforces stability over several frames
            if not self.visibility_filter.update(mean_vis):
                # Not yet stable enough – skip this frame
                return None

            # Smooth coordinates
            keypoints = smooth_keypoints(keypoints, self.smoothers)

        return keypoints

    def close(self):
        """Release MediaPipe resources."""
        self.pose.close()
