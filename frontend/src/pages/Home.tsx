// src/pages/Home.tsx
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="max-w-6xl mx-auto px-6 py-16 lg:py-24">
        {/* Top grid: hero + what it checks */}
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          {/* LEFT: Hero copy */}
          <motion.section
            initial={{ opacity: 0, x: -24 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
              Overview
            </p>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold leading-tight max-w-xl">
              Your AI form coach for{" "}
              <span className="text-emerald-400">smarter</span> workouts.
            </h1>

            <p className="text-sm sm:text-base text-slate-400 max-w-xl">
              Upload a clip or use your webcam. Smart Gym analyzes your form, counts
              reps, and gives friendly posture cues. Then it helps you plan PCOS-friendly
              diets and realistic workout splits.
            </p>

            {/* Primary actions */}
            <div className="flex flex-wrap gap-3 pt-4">
              <Link
                to="/live"
                className="inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-medium bg-emerald-500 text-slate-950 shadow-sm hover:bg-emerald-400 transition"
              >
                Start Live Coaching
              </Link>

              <Link
                to="/upload"
                className="inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-medium border border-slate-600 text-slate-100 hover:border-emerald-500 hover:text-emerald-400 transition"
              >
                Analyze a recorded set
              </Link>
            </div>
          </motion.section>

          {/* RIGHT: What it checks card */}
          <motion.section
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="lg:justify-self-end w-full"
          >
            <div className="rounded-2xl border border-slate-700 bg-slate-900/50 px-6 py-5 shadow-lg backdrop-blur-sm max-w-md mx-auto lg:mx-0">
              <h2 className="text-lg font-semibold mb-4 text-center lg:text-left">
                What it checks
              </h2>

              <ul className="space-y-3 text-sm text-slate-300 leading-relaxed">
                <li className="flex items-start gap-3">
                  <span className="mt-[3px] h-2 w-2 rounded-full bg-emerald-500 flex-shrink-0" />
                  <p>
                    <span className="font-medium">Range of motion &amp; depth</span> for
                    squats, deadlifts, presses.
                  </p>
                </li>

                <li className="flex items-start gap-3">
                  <span className="mt-[3px] h-2 w-2 rounded-full bg-emerald-500 flex-shrink-0" />
                  <p>
                    <span className="font-medium">Spine alignment, bar path,</span> and
                    knee tracking across your reps.
                  </p>
                </li>

                <li className="flex items-start gap-3">
                  <span className="mt-[3px] h-2 w-2 rounded-full bg-emerald-500 flex-shrink-0" />
                  <p>
                    <span className="font-medium">Rep counting &amp; consistency</span>{" "}
                    so you can see how your set actually looked.
                  </p>
                </li>

                <li className="flex items-start gap-3">
                  <span className="mt-[3px] h-2 w-2 rounded-full bg-emerald-500 flex-shrink-0" />
                  <p>
                    <span className="font-medium">Personalized cues &amp; tips</span>{" "}
                    generated with the AI diet and workout planners.
                  </p>
                </li>
              </ul>
            </div>
          </motion.section>
        </div>

        {/* Bottom: 3-step layout */}
        <section className="mt-16 grid gap-10 md:grid-cols-3">
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
              1 · Live feedback
            </p>
            <h3 className="text-sm font-semibold">Live Coaching</h3>
            <p className="text-sm text-slate-400 max-w-xs">
              Use your laptop webcam to get real-time cues while you lift.
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
              2 · Deep dive
            </p>
            <h3 className="text-sm font-semibold">Upload Video</h3>
            <p className="text-sm text-slate-400 max-w-xs">
              Upload a 10–20s set to see detailed frame-by-frame analysis.
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
              3 · Plan
            </p>
            <h3 className="text-sm font-semibold">Diet &amp; Workout Plans</h3>
            <p className="text-sm text-slate-400 max-w-xs">
              Generate PCOS-friendly diet and training templates from one profile.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
