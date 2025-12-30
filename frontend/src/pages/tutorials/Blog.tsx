// src/pages/Blog.tsx
import { Link } from "react-router-dom";

const cards = [
  {
    tag: "Getting started",
    title: "How to film your form for Smart Gym",
    desc: "Best camera angles and lighting so the pose detector can see your whole body clearly.",
    to: "/tutorials/film-form",
  },
  {
    tag: "Technique",
    title: "Squat checklist: 5 things to watch",
    desc: "Depth, knee tracking, bracing, and bar path – a quick checklist before every set.",
    to: "/tutorials/squat-checklist",
  },
  {
    tag: "Technique",
    title: "Deadlift mistakes the AI often flags",
    desc: "Bar drifting away, rounding your back, and rushing the setup are the most common issues.",
    to: "/tutorials/deadlift-flags",
  },
  {
    tag: "Workout",
    title: "Beginner push–pull–legs template",
    desc: "A simple 3-day split that pairs nicely with the AI workout planner suggestions.",
    to: "/tutorials/ppl-template",
  },
];

export default function Blog() {
  return (
    <div className="max-w-6xl mx-auto px-6 space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          Guides & Tutorials
        </h1>
        <p className="text-sm text-muted max-w-xl">
          Short, practical guides that help you get better results from Smart
          Gym and your training.
        </p>
      </header>

      <div className="grid md:grid-cols-2 gap-4">
        {cards.map((card) => (
          <Link
            key={card.to}
            to={card.to}
            className="rounded-2xl bg-slate-900/80 border border-slate-800 px-5 py-4 hover:border-[var(--sg-accent-strong)] hover:shadow-lg transition flex flex-col gap-2"
          >
            <p className="text-[11px] uppercase tracking-wide text-[var(--sg-accent-strong)]">
              {card.tag}
            </p>
            <p className="font-medium">{card.title}</p>
            <p className="text-sm text-muted">{card.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
