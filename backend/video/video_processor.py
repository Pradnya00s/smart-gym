# backend/video/video_processor.py

import cv2
import os
import tempfile
import uuid
from typing import Any, Dict, List

from pose.mediapipe_pose import MediaPipePoseEstimator
from feedback.engine import FeedbackEngine

from exercises.squat import SquatSession
from exercises.pushup import PushupSession
from exercises.bicep_curl import BicepCurlSession
from exercises.deadlift import DeadliftSession
from exercises.plank import PlankSession
from exercises.lunge import LungeSession
from exercises.bench_press import BenchPressSession
from exercises.lat_pulldown import LatPulldownSession


def create_exercise_session(name: str):
    """
    Local copy of the exercise factory to avoid circular imports.
    """
    name = (name or "").lower()

    if name == "plank":
        return PlankSession()
    if name in ("pushup", "push-up", "push_up"):
        return PushupSession()
    if name in ("bicep_curl", "bicep-curl", "curl", "bicep", "hammer_curl"):
        return BicepCurlSession()
    if name in ("deadlift", "deadlifts"):
        return DeadliftSession()
    if name in ("lunge", "lunges"):
        return LungeSession()
    if name in ("bench", "bench_press", "benchpress", "bench-press"):
        return BenchPressSession()
    if name in ("lat", "lat_pulldown", "lat-pulldown", "pulldown"):
        return LatPulldownSession()

    # default
    return SquatSession()


def _draw_skeleton(frame, keypoints: List[Dict[str, float]]):
    """
    Very lightweight skeleton drawing using key MediaPipe joints.
    Assumes normalized coordinates [0,1].
    """
    h, w = frame.shape[:2]

    def to_px(idx: int):
        kp = keypoints[idx]
        return int(kp["x"] * w), int(kp["y"] * h)

    # Minimal set of connections (indices from MediaPipe Pose)
    # shoulders, arms, hips, legs
    pairs = [
        (11, 12),  # shoulders
        (11, 13), (13, 15),  # left arm
        (12, 14), (14, 16),  # right arm
        (11, 23), (12, 24),  # torso
        (23, 24),            # hips
        (23, 25), (25, 27),  # left leg
        (24, 26), (26, 28),  # right leg
    ]

    # draw joints
    for i, kp in enumerate(keypoints):
        x_px = int(kp["x"] * w)
        y_px = int(kp["y"] * h)
        cv2.circle(frame, (x_px, y_px), 3, (0, 255, 0), -1)

    # draw bones
    for i1, i2 in pairs:
        try:
            p1 = to_px(i1)
            p2 = to_px(i2)
            cv2.line(frame, p1, p2, (255, 255, 255), 2)
        except Exception:
            # in case of invalid indices
            continue


class VideoProcessor:
    """
    Process an uploaded video:

    - Runs pose estimation frame by frame
    - Updates the appropriate exercise session (rep counting + form logic)
    - Feeds issues into FeedbackEngine
    - Builds a detailed timeline
    - Writes an overlay video with:
        * Skeleton
        * Exercise name
        * Rep count
        * Top issue text
    """

    def __init__(self, exercise_name: str):
        self.exercise_name = exercise_name

    def process(self, video_path: str) -> Dict[str, Any]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": "Could not open video file."}

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 1e-3:
            fps = 25.0  # sensible default

        pose_estimator = MediaPipePoseEstimator()
        session = create_exercise_session(self.exercise_name)
        feedback_engine = FeedbackEngine()

        # where to save the processed (overlay) video
        tmp_dir = os.path.join(tempfile.gettempdir(), "smart_gym_processed")
        os.makedirs(tmp_dir, exist_ok=True)
        out_path = os.path.join(
            tmp_dir,
            f"{self.exercise_name}_{uuid.uuid4().hex}.mp4"
        )

        writer = None
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        timeline: List[Dict[str, Any]] = []
        issue_counts: Dict[str, int] = {}

        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            # lazily init writer once we know frame size
            if writer is None:
                h, w = frame.shape[:2]
                writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

            keypoints = pose_estimator.infer(frame)

            if keypoints is not None:
                result = session.update(keypoints)
                rep_count = result.get("rep_count", session.rep_count)
                issues = result.get("issues", [])
                extra = result.get("extra", {})
            else:
                rep_count = session.rep_count
                issues = ["Pose not detected"]
                extra = {}

            # feedback engine for top issue
            feedback_engine.add_frame(issues)
            top_issue = feedback_engine.get_top_issue()

            # --- build timeline entry ---
            timeline.append(
                {
                    "frame": frame_idx,
                    "rep_count": rep_count,
                    "issues": issues,
                    "extra": extra,
                }
            )

            # aggregate issues for summary
            for iss in issues:
                if not iss:
                    continue
                issue_counts[iss] = issue_counts.get(iss, 0) + 1

            # --- overlay drawing ---
            overlay = frame.copy()

            if keypoints is not None:
                _draw_skeleton(overlay, keypoints)

            # exercise + reps
            header_text = f"{session.name} | Reps: {rep_count}"
            cv2.putText(
                overlay,
                header_text,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            # top issue (if any and not "Pose not detected")
            if top_issue and top_issue != "Pose not detected":
                cv2.putText(
                    overlay,
                    top_issue[:60],
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA,
                )

            writer.write(overlay)

            frame_idx += 1

        cap.release()
        pose_estimator.close()
        if writer is not None:
            writer.release()

        # build issue summary
        issue_summary = [
            {"issue": k, "count": v}
            for k, v in sorted(issue_counts.items(), key=lambda kv: -kv[1])
        ]

        return {
            "exercise": self.exercise_name,
            "total_reps": session.rep_count,
            "issue_summary": issue_summary,
            "timeline": timeline,
            "video_output": out_path,
        }
