from typing import List, Tuple, Dict
from utils.angles import angle_3pts

LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


def get_angle(keypoints, i1, i2, i3):
    p1 = (keypoints[i1]["x"], keypoints[i1]["y"])
    p2 = (keypoints[i2]["x"], keypoints[i2]["y"])
    p3 = (keypoints[i3]["x"], keypoints[i3]["y"])
    return angle_3pts(p1, p2, p3)


# ------------------------------
# IDLE / NO-EXERCISE DETECTION
# ------------------------------

def is_idle_pose(avg_knee: float, avg_hip: float, exercise: str) -> bool:
    """
    Returns True if the user is likely idle (sitting / standing),
    not performing an exercise.
    """

    # Standing upright
    standing_like = avg_knee > 155 and avg_hip > 155

    # Sitting posture
    sitting_like = avg_knee < 120 and avg_hip > 150

    # Plank exception
    if exercise == "plank":
        return False

    return standing_like or sitting_like


# ------------------------------
# MOVEMENT DEPTH + REP LOGIC
# ------------------------------

def analyze_frame(exercise: str, keypoints, rep_count: int) -> Tuple[int, List[str], Dict]:
    """Shared logic for all exercises."""

    issues: List[str] = []
    extra: Dict = {}

    # --- Universal angles ---
    knee_left = get_angle(keypoints, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)
    knee_right = get_angle(keypoints, RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE)
    hip_left = get_angle(keypoints, LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE)
    hip_right = get_angle(keypoints, RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE)

    if None in (knee_left, knee_right, hip_left, hip_right):
        return rep_count, ["Pose not detected clearly."], {"status": "no_pose"}

    avg_knee = (knee_left + knee_right) / 2
    avg_hip = (hip_left + hip_right) / 2

    # --- IDLE CHECK ---
    if is_idle_pose(avg_knee, avg_hip, exercise):
        return rep_count, ["No exercise detected. Start exercising."], {
            "status": "idle",
            "avg_knee": avg_knee,
            "avg_hip": avg_hip,
        }

    # --- REP TRIGGERING ---
    if exercise in ["squat", "deadlift"]:
        if avg_knee < 70:
            extra["phase"] = "down"
        elif avg_knee > 150:
            if extra.get("phase") == "down":
                rep_count += 1
            extra["phase"] = "up"

    elif exercise == "pushup":
        shoulder_y = keypoints[LEFT_SHOULDER]["y"]
        hip_y = keypoints[LEFT_HIP]["y"]

        if shoulder_y - hip_y < 0.07:
            extra["phase"] = "down"
        elif shoulder_y - hip_y > 0.15:
            if extra.get("phase") == "down":
                rep_count += 1
            extra["phase"] = "up"

    elif exercise == "plank":
        extra["phase"] = "hold"

    elif exercise == "lunge":
        if avg_knee < 80:
            extra["phase"] = "down"
        elif avg_knee > 150:
            if extra.get("phase") == "down":
                rep_count += 1
            extra["phase"] = "up"

    # --- BASIC ISSUES ---
    if avg_hip < 130:
        issues.append("Keep your spine neutral — avoid rounding your back.")

    if avg_knee < 50:
        issues.append("Avoid collapsing knees inward — push them outward.")

    if exercise == "squat" and avg_knee > 120:
        issues.append("Go deeper to achieve full squat depth.")

    return rep_count, issues, extra

# ------------------------------
# FINAL SUMMARY
# ------------------------------

def finalize_analysis(predicted_exercise: str, timeline, rep_count):
    issue_counts = {}

    for frame in timeline:
        for issue in frame.get("issues", []):
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    summary = [
        {"issue": issue, "count": count}
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1])
    ]

    return predicted_exercise, summary
