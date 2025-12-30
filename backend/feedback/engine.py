# backend/feedback/engine.py
from collections import deque
from typing import Deque, List, Optional, Dict
import time


class FeedbackEngine:
    """
    Tracks frame-wise issues and decides:
      - Which issue is the current "top" issue
      - Whether it's time to speak / highlight it (cooldown)
    """

    def __init__(
        self,
        history_len: int = 15,
        min_persistence_frames: int = 5,
        cooldown_sec: float = 3.0,
        repeat_same_issue_after: float = 10.0,
    ):
        """
        Parameters
        ----------
        history_len : int
            How many recent frames of issues to remember.
        min_persistence_frames : int
            Minimum number of frames where the same issue must appear
            in history to be considered "stable".
        cooldown_sec : float
            Minimum seconds between two "speak" events.
        repeat_same_issue_after : float
            Minimum seconds before repeating the exact same issue again.
        """
        self.issue_history: Deque[List[str]] = deque(maxlen=history_len)
        self.min_persistence_frames = min_persistence_frames
        self.cooldown_sec = cooldown_sec
        self.repeat_same_issue_after = repeat_same_issue_after

        self.last_spoken_issue: Optional[str] = None
        self.last_spoken_time: float = 0.0

    # ---------- history management ----------

    def add_frame(self, issues: List[str]) -> None:
        """
        Add issues for the current frame to the history.
        """
        self.issue_history.append(issues or [])

    def _issue_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for frame_issues in self.issue_history:
            for iss in frame_issues:
                counts[iss] = counts.get(iss, 0) + 1
        return counts

    def get_top_issue(self) -> Optional[str]:
        """
        Returns the most persistent issue in the recent history,
        if it appears at least `min_persistence_frames` times.
        Otherwise returns None.
        """
        counts = self._issue_counts()
        if not counts:
            return None

        # pick the issue that appears in the largest number of frames
        issue, count = max(counts.items(), key=lambda kv: kv[1])
        if count < self.min_persistence_frames:
            return None
        return issue

    # ---------- speaking / highlighting logic ----------

    def should_speak(self, issue: Optional[str], now: Optional[float] = None) -> bool:
        """
        Decide if it's okay to trigger TTS / major highlight for this issue now.
        Applies cooldown & avoids immediately repeating the same issue.
        """
        if not issue:
            return False

        now = now or time.time()

        # Global cooldown between any two speech events
        if now - self.last_spoken_time < self.cooldown_sec:
            return False

        # Avoid repeating the exact same issue too soon
        if (
            self.last_spoken_issue == issue
            and now - self.last_spoken_time < self.repeat_same_issue_after
        ):
            return False

        return True

    def mark_spoken(self, issue: str, now: Optional[float] = None) -> None:
        """
        Mark that we just spoke this issue (for cooldown tracking).
        """
        now = now or time.time()
        self.last_spoken_issue = issue
        self.last_spoken_time = now
