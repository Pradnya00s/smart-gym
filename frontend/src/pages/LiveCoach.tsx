// src/pages/LiveCoach.tsx
import { useEffect, useRef, useState } from "react";

const WS_BASE_URL = "ws://127.0.0.1:8000/ws/live";

type Issue = string;

interface LiveState {
  exercise: string | null;
  reps: number;
  issues: Issue[];
}

type DetectMode = "auto" | "manual";

const EXERCISES = [
  "squat",
  "pushup",
  "deadlift",
  "bench_press",
  "bicep_curl",
  "lunge",
  "plank",
  "lat_pulldown",
];

export default function LiveCoach() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<number | null>(null);

  const [status, setStatus] = useState<"idle" | "starting" | "running" | "error">(
    "idle"
  );

  const [live, setLive] = useState<LiveState>({
    exercise: null,
    reps: 0,
    issues: [],
  });

  const [detectMode, setDetectMode] = useState<DetectMode>("auto");
  const [manualExercise, setManualExercise] = useState<string>("squat");

  useEffect(() => {
    return () => {
      stopStreaming();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopStreaming = () => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const video = videoRef.current;
    if (video && video.srcObject) {
      (video.srcObject as MediaStream)
        .getTracks()
        .forEach((track) => track.stop());
      video.srcObject = null;
    }

    setStatus("idle");
    setLive({
      exercise: null,
      reps: 0,
      issues: [],
    });
  };

  const startStreaming = async () => {
    try {
      setStatus("starting");

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      });

      const video = videoRef.current;
      if (!video) throw new Error("Video element missing");

      video.srcObject = stream;
      await video.play();

      // build websocket URL with exercise param
      const exerciseParam =
        detectMode === "auto" ? "auto" : manualExercise || "squat";
      const wsUrl = `${WS_BASE_URL}?exercise=${encodeURIComponent(
        exerciseParam
      )}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("running");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLive({
            exercise: data.exercise ?? null,
            reps: data.reps ?? 0,
            issues: data.issues ?? [],
          });
        } catch {
          // ignore malformed packets
        }
      };

      ws.onerror = () => {
        setStatus("error");
      };

      ws.onclose = () => {
        if (status !== "idle") setStatus("idle");
      };

      const sendFrame = async () => {
        if (!videoRef.current || !canvasRef.current) return;
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)
          return;

        const videoEl = videoRef.current;
        const canvasEl = canvasRef.current;
        const ctx = canvasEl.getContext("2d");
        if (!ctx) return;

        canvasEl.width = videoEl.videoWidth || 640;
        canvasEl.height = videoEl.videoHeight || 480;

        ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

        await new Promise<void>((resolve) =>
          canvasEl.toBlob(
            async (blob) => {
              if (!blob) {
                resolve();
                return;
              }
              const buffer = await blob.arrayBuffer();
              const bytes = Array.from(new Uint8Array(buffer));
              wsRef.current?.send(JSON.stringify({ frame: bytes }));
              resolve();
            },
            "image/jpeg",
            0.7
          )
        );
      };

      intervalRef.current = window.setInterval(sendFrame, 160);
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  const topIssue = live.issues[0] ?? "No issues detected yet.";

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Header + webcam controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-slate-50">
            Live Form Coaching
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Stream your webcam to the backend and get real-time exercise
            detection, rep counts and posture cues.
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          {/* Auto / manual toggle */}
          <div className="inline-flex rounded-full bg-slate-900/80 border border-slate-700 p-1 text-xs">
            <button
              type="button"
              onClick={() => setDetectMode("auto")}
              className={`px-3 py-1 rounded-full ${
                detectMode === "auto"
                  ? "bg-teal-400 text-slate-950 font-semibold shadow"
                  : "text-slate-300 hover:text-slate-50"
              }`}
            >
              Auto detect
            </button>
            <button
              type="button"
              onClick={() => setDetectMode("manual")}
              className={`px-3 py-1 rounded-full ${
                detectMode === "manual"
                  ? "bg-teal-400 text-slate-950 font-semibold shadow"
                  : "text-slate-300 hover:text-slate-50"
              }`}
            >
              Choose exercise
            </button>
          </div>

          {/* Manual exercise select */}
          {detectMode === "manual" && (
            <select
              value={manualExercise}
              onChange={(e) => setManualExercise(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-teal-400"
            >
              {EXERCISES.map((ex) => (
                <option key={ex} value={ex}>
                  {ex.replace("_", " ")}
                </option>
              ))}
            </select>
          )}

          {/* Start / Stop button */}
          <div className="flex gap-2">
            {status !== "running" ? (
              <button
                onClick={startStreaming}
                className="rounded-xl bg-teal-400 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-300 disabled:opacity-60"
                disabled={status === "starting"}
              >
                {status === "starting" ? "Starting..." : "Start webcam"}
              </button>
            ) : (
              <button
                onClick={stopStreaming}
                className="rounded-xl bg-rose-500/90 px-4 py-2 text-sm font-semibold text-slate-50 hover:bg-rose-500"
              >
                Stop
              </button>
            )}
          </div>
        </div>
      </div>

      {status === "error" && (
        <p className="text-sm text-red-400">
          Something went wrong. Check that the backend is running on{" "}
          <code>127.0.0.1:8000</code> and that webcam permission is allowed.
        </p>
      )}

      <div className="grid gap-6 md:grid-cols-[3fr,2fr] items-start">
        {/* Video */}
        <div className="space-y-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
            <video
              ref={videoRef}
              className="w-full h-full bg-black object-cover"
              autoPlay
              playsInline
              muted
            />
          </div>
          {/* Hidden canvas for encoding frames */}
          <canvas ref={canvasRef} className="hidden" />
        </div>

        {/* Live stats */}
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wide">
              Detected Exercise
            </p>
            <p className="mt-1 text-xl font-semibold text-slate-50 min-h-[1.5rem]">
              {live.exercise ?? "Detecting..."}
            </p>

            <div className="mt-4 flex items-center gap-4">
              <div className="rounded-xl bg-slate-950 border border-slate-800 px-4 py-2">
                <p className="text-xs text-slate-400 uppercase tracking-wide">
                  Reps
                </p>
                <p className="text-2xl font-semibold text-teal-300">
                  {live.reps}
                </p>
              </div>
              <p className="text-xs text-slate-500">
                Tip: keep your whole body in frame for better tracking.
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">
              Top cue
            </p>
            <p className="text-sm text-slate-100">{topIssue}</p>

            {live.issues.length > 1 && (
              <ul className="mt-3 space-y-1 text-xs text-slate-400 list-disc list-inside">
                {live.issues.slice(1, 4).map((issue, idx) => (
                  <li key={idx}>{issue}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
