# backend/exercise_classifier/collect_from_videos.py

import os
import sys
import csv
from typing import List

import cv2

from ..pose.mediapipe_pose import MediaPipePoseEstimator
from .features import build_feature_vector, FEATURE_NAMES


def iter_video_files(root_dir: str, exts=(".mp4", ".mov", ".avi", ".mkv")):
    """
    Walks through root_dir and yields (video_path, label),
    where label = name of the immediate parent directory.

    Example folder structure:
      root_dir/
        squat/
          video1.mp4
          video2.mov
        pushup/
          video3.mp4

    Then:
      video1.mp4 -> label 'squat'
      video3.mp4 -> label 'pushup'
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # label: folder name directly under root_dir
        # e.g., /.../root_dir/squat -> label 'squat'
        if dirpath == root_dir:
            # top-level, skip files directly under root
            continue

        label = os.path.basename(dirpath.rstrip(os.sep))

        for fname in filenames:
            if fname.lower().endswith(exts):
                yield os.path.join(dirpath, fname), label


def collect_from_video(
    video_path: str,
    label: str,
    pose_estimator: MediaPipePoseEstimator,
    frame_stride: int = 3,
) -> List[List]:
    """
    Extracts feature vectors from a single video.
    Returns a list of rows: [feature_1, ..., feature_n, label]
    """
    print(f"[COLLECT] Video: {video_path} | Label: {label}")
    rows = []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[WARN] Could not open video: {video_path}")
        return rows

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # only sample every Nth frame
        if frame_idx % frame_stride != 0:
            frame_idx += 1
            continue

        keypoints = pose_estimator.infer(frame)
        if keypoints is None:
            frame_idx += 1
            continue

        feats = build_feature_vector(keypoints)
        row = list(feats.tolist()) + [label]
        rows.append(row)

        frame_idx += 1

    cap.release()
    print(f"[COLLECT] Extracted {len(rows)} samples from {video_path}")
    return rows


def main(root_dir: str, out_csv: str, frame_stride: int = 3):
    """
    root_dir: path containing subfolders per exercise.
    out_csv: path to output CSV file.
    frame_stride: use every Nth frame (to reduce dataset size).
    """
    pose = MediaPipePoseEstimator()
    all_rows: List[List] = []

    for video_path, label in iter_video_files(root_dir):
        rows = collect_from_video(video_path, label, pose, frame_stride=frame_stride)
        all_rows.extend(rows)

    pose.close()

    if not all_rows:
        print("[COLLECT] No data collected.")
        return

    # Write CSV
    header = FEATURE_NAMES + ["label"]
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(all_rows)

    print(f"[COLLECT] Wrote {len(all_rows)} rows to {out_csv}")


if __name__ == "__main__":
    # Usage:
    # python -m backend.exercise_classifier.collect_from_videos data/raw_videos data/exercise_features.csv 3
    if len(sys.argv) < 3:
        print("Usage: python -m backend.exercise_classifier.collect_from_videos <root_dir> <out_csv> [frame_stride]")
        sys.exit(1)

    root_dir = sys.argv[1]
    out_csv = sys.argv[2]
    frame_stride = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    main(root_dir, out_csv, frame_stride)
