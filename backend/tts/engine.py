# backend/tts/engine.py

import threading
import platform
import subprocess
from typing import Optional

import pyttsx3


class TTSFeedbackSpeaker:
    """
    TTS speaker for real-time feedback.

    - On macOS: prefers the system `say` command (very reliable).
    - Elsewhere: falls back to pyttsx3.
    - Runs speech in a background thread so it doesn't block the main loop.
    """

    def __init__(self, rate: int = 180, volume: float = 1.0, voice_id: Optional[str] = None):
        self.system = platform.system()

        # Decide backend
        if self.system == "Darwin":  # macOS
            self.backend = "say"
            self.engine = None
        else:
            self.backend = "pyttsx3"
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", rate)
            self.engine.setProperty("volume", volume)
            if voice_id is not None:
                self.engine.setProperty("voice", voice_id)

        # Protect pyttsx3 engine with a lock (if used)
        self._lock = threading.Lock()

    def _speak_sync(self, text: str):
        if not text:
            return

        print(f"[TTS] Speaking: {text}", flush=True)

        if self.backend == "say":
            # Use macOS built-in TTS
            try:
                subprocess.call(["say", text])
            except Exception as e:
                print(f"[TTS] Error calling 'say': {e}", flush=True)
        else:
            # pyttsx3 backend
            if self.engine is None:
                return
            with self._lock:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"[TTS] pyttsx3 error: {e}", flush=True)

    def speak(self, text: str):
        """
        Fire-and-forget: speak text in a background thread.
        """
        if not text:
            return

        t = threading.Thread(target=self._speak_sync, args=(text,))
        t.daemon = True
        t.start()
