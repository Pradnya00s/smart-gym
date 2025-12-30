// src/pages/Plans.tsx
import { useState } from "react";

type PlannerMode = "diet" | "workout";

type PlannerResult = {
  diet_plan?: string;
  workout_plan?: string;
};

export default function Plans() {
  const [mode, setMode] = useState<PlannerMode>("diet");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlannerResult | null>(null);

  const [profile, setProfile] = useState({
    name: "",
    age: "",
    gender: "",
    heightCm: "",
    weightKg: "",
    goal: "fat_loss",
    activityLevel: "moderate",
    dietType: "mixed",
    constraints: "",
  });

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setResult(null);

    const payload = {
      name: profile.name || "User",
      age: profile.age ? Number(profile.age) : null,
      gender: profile.gender || null,
      height_cm: profile.heightCm ? Number(profile.heightCm) : null,
      weight_kg: profile.weightKg ? Number(profile.weightKg) : null,
      primary_goal: profile.goal,
      activity_level: profile.activityLevel,
      diet_type: profile.dietType,
      constraints: profile.constraints,
    };

    const endpoint =
      mode === "diet"
        ? "http://127.0.0.1:8000/plan/diet"
        : "http://127.0.0.1:8000/plan/workout";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const activeLabel = mode === "diet" ? "Diet Plan" : "Workout Plan";

  return (
    <div className="max-w-6xl mx-auto px-6 space-y-8">
      <header className="space-y-2">
        <h1 className="text-4xl font-bold">Smart Plans</h1> 
        <p className="mt-3 text-muted">
          Fill your profile once and generate AI-backed <span className="text-accent">diet</span>
          and <span className="text-accent">workout</span> plans that match your goals
          and constraints.
          </p>
      </header>

      {/* Toggle */}
      <div className="inline-flex rounded-full bg-slate-900 border border-slate-800 p-1">
        <button
          type="button"
          onClick={() => {
            setMode("diet");
            setResult(null);
          }}
          className={`px-4 py-1 text-xs font-medium rounded-full ${
            mode === "diet"
              ? "bg-[var(--sg-accent-strong)] text-slate-950 shadow-sm"
              : "text-slate-300 hover:text-slate-100"
          }`}
        >
          Diet Plan
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("workout");
            setResult(null);
          }}
          className={`px-4 py-1 text-xs font-medium rounded-full ${
            mode === "workout"
              ? "bg-[var(--sg-accent-strong)] text-slate-950 shadow-sm"
              : "text-slate-300 hover:text-slate-100"
          }`}
        >
          Workout Plan
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-6 items-start">
        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4"
        >
          <h2 className="text-lg font-medium mb-1">Your Profile</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400">Name</label>
              <input
                name="name"
                value={profile.name}
                onChange={handleChange}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)]"
                placeholder=""
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400">Age</label>
              <input
                name="age"
                type="number"
                value={profile.age}
                onChange={handleChange}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)]"
                placeholder="Your Age"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400">
                Gender
              </label>
              <select
                name="gender"
                value={profile.gender}
                onChange={handleChange}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)]"
              >
                <option value="">Select</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="non_binary">Non-binary</option>
                <option value="prefer_not">Prefer not to say</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400">
                Height 
              </label>
              <input
                name="heightCm"
                type="number"
                value={profile.heightCm}
                onChange={handleChange}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)]"
                placeholder="Height in cm"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400">
                Weight 
              </label>
              <input
                name="weightKg"
                type="number"
                value={profile.weightKg}
                onChange={handleChange}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)]"
                placeholder="Weight in KG"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400">Goal</label>
              <select
                name="goal"
                value={profile.goal}
                onChange={handleChange}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)]"
              >
                <option value="fat_loss">Fat loss</option>
                <option value="muscle_gain">Muscle gain</option>
                <option value="recomposition">Body recomposition</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400">
                Activity level
              </label>
              <select
                name="activityLevel"
                value={profile.activityLevel}
                onChange={handleChange}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)]"
              >
                <option value="sedentary">Sedentary</option>
                <option value="light">Lightly active</option>
                <option value="moderate">Moderately active</option>
                <option value="high">Very active</option>
              </select>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-400">
                Diet type
              </label>
              <select
                name="dietType"
                value={profile.dietType}
                onChange={handleChange}
                className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)]"
              >
                <option value="veg">Vegetarian</option>
                <option value="non_veg">Non-vegetarian</option>
                <option value="egg_veg">Egg + Veg</option>
                <option value="vegan">Vegan</option>
                <option value="mixed">Flexible / mixed</option>
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-400">
              Constraints / preferences
            </label>
            <textarea
              name="constraints"
              value={profile.constraints}
              onChange={handleChange}
              rows={3}
              className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--sg-accent-strong)] resize-none"
              placeholder="E.g. PCOS-friendly, no dairy at night, hostel mess food, budget friendly..."
            />
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950/40 border border-red-500/40 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 inline-flex items-center justify-center px-4 py-2 rounded-lg bg-[var(--sg-accent-strong)] text-slate-950 font-medium text-sm hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed transition shadow-md"
          >
            {loading
              ? `Generating ${activeLabel}...`
              : `Generate ${activeLabel}`}
          </button>
        </form>

        {/* Result */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg h-full flex flex-col">
          <h2 className="text-lg font-medium mb-2">{activeLabel} (AI)</h2>

          {!result && !loading && (
            <p className="text-sm text-muted">
              Fill your details and click{" "}
              <span className="text-accent font-medium">Generate</span> to see a
              tailored plan here.
            </p>
          )}

          {loading && (
            <p className="text-sm text-muted animate-pulse">
              Thinking about macros, recovery, and your schedule...
            </p>
          )}

          {result && (
            <pre className="mt-3 text-sm whitespace-pre-wrap text-slate-100 bg-slate-950/60 border border-slate-800 rounded-xl p-3 overflow-y-auto max-h-[450px]">
              {mode === "diet"
                ? result.diet_plan || JSON.stringify(result, null, 2)
                : result.workout_plan || JSON.stringify(result, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
