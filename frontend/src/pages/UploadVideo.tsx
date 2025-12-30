// src/pages/UploadVideo.tsx
import { useState } from "react";
import type { ChangeEvent } from "react";

type IssueSummary = {
  issue: string;
  count: number;
};

type ApiResponse = {
  exercise: string;
  total_reps: number;
  timeline: any[];
  issue_summary: IssueSummary[];
  video_output?: string;
};

export default function UploadVideo() {
  const [file, setFile] = useState<File | null>(null);
  const [selectedName, setSelectedName] = useState<string>("none");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setSelectedName(f?.name ?? "none");
    setData(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setData(null);

    const formData = new FormData();
    formData.append("video_file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/process-video", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new Error(`Backend error ${res.status}`);
      }
      const json = (await res.json()) as ApiResponse;
      setData(json);
    } catch (err: any) {
      console.error(err);
      setError(err.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const topIssue = data?.issue_summary?.[0];

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">
      {/* Heading */}
      <header className="text-center mb-2">
        <h1 className="text-3xl sm:text-4xl font-bold">Analyze Recorded Set</h1>
        <p className="mt-3 text-muted">
          Upload a video (10–20 seconds) of a single exercise. The backend will detect
          movement, count reps, and summarize posture issues.
        </p>
      </header>

      {/* Upload card */}
      <section className="rounded-2xl bg-slate-900/80 border border-slate-800 px-6 py-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1 text-left">
          <p className="text-sm font-medium">Video file (mp4 or mov)</p>
          <p className="text-xs text-muted">
            Try to keep the camera steady, with your full body in frame.
          </p>
          <p className="text-xs text-slate-400">
            Selected: <span className="font-mono">{selectedName}</span>
          </p>
        </div>

        <div className="flex gap-3 items-center">
          <label className="relative inline-flex">
            <input
              type="file"
              accept="video/mp4,video/quicktime"
              onChange={handleFileChange}
              className="hidden"
            />
            <span className="cursor-pointer rounded-full border border-slate-700 px-4 py-2 text-sm hover:border-slate-500">
              Choose file
            </span>
          </label>

          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="rounded-full px-5 py-2 text-sm font-semibold bg-emerald-500 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "Analyzing..." : "Upload & Analyze"}
          </button>
        </div>
      </section>

      {/* Error */}
      {error && (
        <p className="mt-2 text-sm text-red-400 bg-red-950/40 border border-red-500/40 rounded-xl px-4 py-2">
          {error}
        </p>
      )}

      {/* Results */}
      {data && (
        <section className="mt-6 rounded-2xl bg-slate-900/80 border border-slate-800 p-6 grid gap-6 lg:grid-cols-[1.4fr,1.6fr]">
          <div className="space-y-4">
            <div>
              <p className="text-xs text-muted uppercase tracking-wide">
                Detected exercise
              </p>
              <p className="text-3xl font-semibold text-accent mt-1">
                {data.exercise}
              </p>
            </div>

            <div className="flex gap-4">
              <div className="rounded-2xl bg-slate-950 border border-slate-800 px-4 py-3 flex-1">
                <p className="text-xs text-muted uppercase tracking-wide">
                  Total reps
                </p>
                <p className="text-3xl font-semibold mt-1">
                  {data.total_reps ?? 0}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-950 border border-slate-800 px-4 py-3 flex-1">
                <p className="text-xs text-muted uppercase tracking-wide">
                  Frames analyzed
                </p>
                <p className="text-3xl font-semibold mt-1">
                  {data.timeline?.length ?? 0}
                </p>
              </div>
            </div>

            <div className="rounded-2xl bg-slate-950 border border-slate-800 px-4 py-3 space-y-2 text-left">
              <p className="text-xs text-muted uppercase tracking-wide">
                Most frequent posture cue
              </p>
              <p className="text-sm">
                {topIssue ? topIssue.issue : "No posture issues detected."}
              </p>
              {data.issue_summary?.length > 1 && (
                <ul className="mt-1 text-xs text-slate-400 space-y-1 list-disc list-inside">
                  {data.issue_summary.slice(1).map((item, idx) => (
                    <li key={idx}>
                      {item.issue}{" "}
                      <span className="text-slate-500">
                        ({item.count} frames)
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <p className="text-xs text-muted text-left">
              Tip: use this page to debug your form for a single lift, then
              switch to <span className="text-accent">Live Coaching</span> for
              real-time feedback.
            </p>
          </div>

          {/* Video preview */}
          <div className="space-y-2">
            <p className="text-xs text-muted uppercase tracking-wide">
              Annotated video
            </p>
            <div className="rounded-2xl bg-black/70 border border-slate-800 overflow-hidden">
              {data.video_output ? (
                <video
                  key={data.video_output}
                  src={`http://127.0.0.1:8000${data.video_output}`}
                  controls
                  className="w-full h-full"
                />
              ) : (
                <div className="h-64 flex items-center justify-center text-sm text-muted">
                  Backend did not return a video path.
                </div>
              )}
            </div>
            <p className="text-[11px] text-muted">
              The video is generated and stored locally by your backend and
              streamed to this player from <code>/processed-video</code>.
            </p>
          </div>
        </section>
      )}
    </div>
  );
}
