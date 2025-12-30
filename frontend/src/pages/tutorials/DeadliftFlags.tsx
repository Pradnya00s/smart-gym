export default function DeadliftFlags() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-10 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Deadlift mistakes the AI often flags</h1>

      <ul className="list-disc list-inside text-slate-400 mt-4 space-y-3">
        <li>Rounding the lower back during the pull.</li>
        <li>Letting the bar drift too far forward.</li>
        <li>Not engaging the lats (bar drifts away).</li>
        <li>Jerking the bar instead of building tension first.</li>
      </ul>
    </div>
  );
}
