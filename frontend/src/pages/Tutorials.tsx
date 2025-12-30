import { Link } from "react-router-dom";

const guides = [
  {
    title: "How to film your form",
    tag: "Getting Started",
    to: "/tutorials/film-form",
    desc: "Learn the best camera angles so the AI can see your whole body."
  },
  {
    title: "Deadlift mistakes AI flags",
    tag: "Technique",
    to: "/tutorials/deadlift-flags",
    desc: "Bar drifting, rounding back, setup errors — common issues."
  },
  {
    title: "Squat checklist", 
    tag: "Technique",
    to: "/tutorials/squat-checklist",
    desc: "Depth, knee tracking, bracing — quick checklist."
  },
  {
    title: "Beginner Push–Pull–Legs",
    tag: "Workout",
    to: "/tutorials/ppl",
    desc: "A simple 3-day split that works well with AI plans."
  }
];

export default function Tutorials() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-semibold text-text-primary mb-2">
        Guides & Tutorials
      </h1>
      <p className="text-text-secondary mb-8">
        Short, helpful guides to improve your form and planning.
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        {guides.map((g) => (
          <Link
            key={g.to}
            to={g.to}
            className="p-5 rounded-xl bg-bg-secondary border border-slate-700/40 hover:border-accent transition"
          >
            <span className="text-xs uppercase text-accent">{g.tag}</span>
            <h2 className="text-xl font-medium text-text-primary mt-1">
              {g.title}
            </h2>
            <p className="text-text-secondary text-sm mt-2">{g.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
