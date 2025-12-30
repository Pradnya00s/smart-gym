from dotenv import load_dotenv
load_dotenv()

import os
import tempfile
from typing import List

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, WebSocket, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pose.pose_detector import PoseDetector

from exercise_classifier.model import ExerciseClassifier
from exercise_logic.logic import analyze_frame, finalize_analysis
from exercise_classifier.features import build_feature_vector, FEATURE_NAMES
from planner.diet_planner import DietPlanner
from planner.workout_planner import WorkoutPlanner
from exercise_classifier.temporal_smoother import TemporalExerciseSmoother




# ---------------------------------------------------------
# FastAPI + static video mount
# ---------------------------------------------------------
app = FastAPI(title="Smart Gym Backend", version="3.1")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single, consistent processed-video dir
PROCESSED_DIR = os.path.join(tempfile.gettempdir(), "smart_gym_processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Serve processed videos at /processed-video/<filename>
app.mount(
    "/processed-video",
    StaticFiles(directory=PROCESSED_DIR),
    name="processed-video",
)

pose_detector = PoseDetector()
classifier = ExerciseClassifier(
    confidence_threshold=0.6,
    reject_label=None
)

smoother = TemporalExerciseSmoother(
    window_size=7,
    min_agreement=0.6
)

diet_planner = DietPlanner()
workout_planner = WorkoutPlanner()


# ---------------------------------------------------------
# Helper: draw pose, reps, issues on frame
# ---------------------------------------------------------
def draw_annotations(
    frame,
    keypoints,
    rep_count: int,
    issues: List[str],
    predicted_exercise: str,
):
    # keypoints
    for lm in keypoints:
        x = int(lm["x"] * frame.shape[1])
        y = int(lm["y"] * frame.shape[0])
        cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

    # skeleton
    CONNECTIONS = [
        (11, 13), (13, 15),
        (12, 14), (14, 16),
        (11, 12),
        (23, 24),
        (11, 23), (12, 24),
        (23, 25), (25, 27),
        (24, 26), (26, 28),
    ]

    for i1, i2 in CONNECTIONS:
        x1 = int(keypoints[i1]["x"] * frame.shape[1])
        y1 = int(keypoints[i1]["y"] * frame.shape[0])
        x2 = int(keypoints[i2]["x"] * frame.shape[1])
        y2 = int(keypoints[i2]["y"] * frame.shape[0])
        cv2.line(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)

    # reps
    cv2.putText(
        frame,
        f"Reps: {rep_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2,
    )

    # exercise label
    cv2.putText(
        frame,
        predicted_exercise or "",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 200, 0),
        2,
    )

    # issues
    y_offset = 120
    for issue in issues[:3]:
        cv2.putText(
            frame,
            f"- {issue}",
            (20, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (50, 50, 255),
            2,
        )
        y_offset += 30

    return frame


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"status": "Smart Gym Backend v3.1 Running"}


# ---------------------------------------------------------
# Process recorded video
# ---------------------------------------------------------
@app.post("/process-video")
async def process_video(video_file: UploadFile = File(...)):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(await video_file.read())
        input_path = tmp.name

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return {"error": "Could not read video file"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps is None or fps <= 1:
        fps = 24.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    filename = f"processed_{os.path.basename(input_path)}"
    output_path = os.path.join(PROCESSED_DIR, filename)

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    timeline = []
    rep_count = 0
    predicted_exercise = None
    frame_index = 0
    smoother.buffer.clear()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))

        keypoints = pose_detector.detect_keypoints(frame)

        if keypoints is None:
            timeline.append(
                {
                    "frame": frame_index,
                    "rep_count": rep_count,
                    "issues": ["Pose not detected"],
                    "extra": {},
                }
            )
            writer.write(frame)
            frame_index += 1
            continue

        feats = build_feature_vector(keypoints).reshape(1, -1)
        tentative_exercise = classifier.predict(feats)
        stable_exercise = smoother.update(tentative_exercise)

        rep_count, issues, extra = analyze_frame(
            stable_exercise, keypoints, rep_count
            )

        if extra.get("status") == "idle":
            predicted_exercise = None
        else:
            predicted_exercise = stable_exercise

        timeline.append(
            {
                "frame": frame_index,
                "rep_count": rep_count,
                "issues": issues,
                "extra": extra,
            }
        )

        annotated = draw_annotations(
            frame.copy(),
            keypoints,
            rep_count,
            issues,
            predicted_exercise,
        )

        writer.write(annotated)
        frame_index += 1

    cap.release()
    writer.release()

    exercise_name, summary = finalize_analysis(
        predicted_exercise, timeline, rep_count
    )

    return {
        "exercise": exercise_name,
        "total_reps": rep_count,
        "frames_analyzed": len(timeline),
        "issue_summary": summary,
        "video_url": f"/processed-video/{filename}",
    }


# ---------------------------------------------------------
# Live websocket (LiveCoach)
# ---------------------------------------------------------
@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket, exercise: str = "auto"):
    await websocket.accept()
    smoother.buffer.clear()

    try:
        while True:
            data = await websocket.receive_json()

            frame_bytes = np.frombuffer(bytes(data["frame"]), dtype=np.uint8)
            frame = cv2.imdecode(frame_bytes, cv2.IMREAD_COLOR)

            keypoints = pose_detector.detect_keypoints(frame)
            if keypoints is None:
                await websocket.send_json(
                    {
                        "exercise": exercise if exercise != "auto" else None,
                        "reps": 0,
                        "issues": ["Pose not detected"],
                        "extra": {},
                        "keypoints": None,
                    }
                )
                continue

            if exercise == "auto":
                feats = build_feature_vector(keypoints).reshape(1, -1)
                tentative_exercise = classifier.predict(feats)
            else:
                tentative_exercise = exercise
            stable_exercise = smoother.update(tentative_exercise)

            rep_count, issues, extra = analyze_frame(
                stable_exercise, keypoints, 0
            )

            if extra.get("status") == "idle":
                predicted = None
                rep_count = 0
            else:
                predicted = stable_exercise

            await websocket.send_json(
                {
                    "exercise": predicted,
                    "reps": rep_count,
                    "issues": issues,
                    "extra": extra,
                    "keypoints": keypoints,
                }
            )

    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ---------------------------------------------------------
# AI Diet & Workout planners
# ---------------------------------------------------------
@app.post("/plan/diet")
async def generate_diet_plan(user: dict = Body(...)):
    result = await diet_planner.generate_diet(user)
    return {"diet_plan": result}


@app.post("/plan/workout")
async def generate_workout_plan(user: dict = Body(...)):
    result = await workout_planner.generate_workout(user)
    return {"workout_plan": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
