# backend/run_squat_webcam.py
import time
from typing import List, Dict

import cv2

from backend.pose.mediapipe_pose import MediaPipePoseEstimator
from backend.exercises.squat import SquatSession
from backend.feedback.engine import FeedbackEngine


def keypoints_visible_enough(
    keypoints: List[Dict[str, float]],
    min_visibility: float = 0.4,
    required_indices=None,
) -> bool:
    """
    Simple visibility filter:
      - returns False if any required landmark has visibility < min_visibility
    """
    if required_indices is None:
        # default: hips + knees + ankles + shoulders
        required_indices = [11, 12, 23, 24, 25, 26, 27, 28]

    for idx in required_indices:
        if idx >= len(keypoints):
            return False
        if keypoints[idx]["visibility"] < min_visibility:
            return False
    return True


def main():
    # --- Init pose estimator & exercise session ---
    pose_estimator = MediaPipePoseEstimator(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    squat_session = SquatSession()

    feedback_engine = FeedbackEngine(
        history_len=15,
        min_persistence_frames=4,
        cooldown_sec=3.0,
        repeat_same_issue_after=10.0,
    )

    # --- Open webcam ---
    # Use AVFoundation backend on macOS
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        print("❌ Could not open webcam.")
        return

    print("✅ Webcam opened. Press 'q' in the video window to quit.")

    # Explicitly create a named window (helps on macOS)
    window_name = "Smart Gym - Squat Debug"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    last_print_time = 0.0
    loop_counter = 0

    try:
        while True:
            loop_counter += 1
            ret, frame = cap.read()
            if not ret or frame is None:
                print("❌ Failed to read frame from webcam.")
                break

            # You can downscale if needed
            # frame = cv2.resize(frame, (640, 360))

            keypoints = pose_estimator.infer(frame)

            issues = []
            extra = {}

            if keypoints is not None and keypoints_visible_enough(keypoints):
                result = squat_session.update(keypoints)
                rep_count = result["rep_count"]
                issues = result["issues"]
                extra = result["extra"]
            else:
                rep_count = squat_session.rep_count
                issues.append("Pose not clearly visible.")

            # Update feedback engine
            feedback_engine.add_frame(issues)
            top_issue = feedback_engine.get_top_issue()

            if top_issue:
                display_issue = top_issue
            elif issues:
                display_issue = issues[0]
            else:
                display_issue = ""

            # --- Overlay text on frame ---
            cv2.putText(
                frame,
                f"Squats: {rep_count}",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                frame,
                f"State: {squat_session.state}",
                (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2,
                cv2.LINE_AA,
            )

            if display_issue:
                cv2.putText(
                    frame,
                    display_issue[:60],
                    (30, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA,
                )

            # Show the frame
            cv2.imshow(window_name, frame)

            # Debug log every ~1 second so we know loop is alive
            now = time.time()
            if now - last_print_time > 1.0:
                print(
                    f"[loop {loop_counter}] Reps: {rep_count} | "
                    f"State: {squat_session.state} | "
                    f"Top issue: {top_issue} | Frame issues: {issues}"
                )
                last_print_time = now

            # Handle key press (must be AFTER imshow)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Detected 'q' key, exiting loop.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        pose_estimator.close()
        print("👋 Webcam session ended.")


if __name__ == "__main__":
    main()
