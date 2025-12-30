# backend/exercises/factory.py

from .squat import SquatSession
from .plank import PlankSession
from .pushup import PushupSession
from .bicep_curl import BicepCurlSession
from .deadlift import DeadliftSession
from .lunge import LungeSession
from .bench_press import BenchPressSession
from .lat_pulldown import LatPulldownSession


def create_exercise_session(name: str):
    """
    Factory for exercise sessions based on a string name.
    """
    name = (name or "").lower()

    if name == "plank":
        return PlankSession()
    if name in ("pushup", "push-up", "push_up"):
        return PushupSession()
    if name in ("bicep_curl", "bicep-curl", "curl", "bicep"):
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
