// src/App.tsx
import "./App.css";

import { Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import LiveCoach from "./pages/LiveCoach";
import UploadVideo from "./pages/UploadVideo";
import Plans from "./pages/Plans";

// Tutorials
import Blog from "./pages/tutorials/Blog";
import FilmForm from "./pages/tutorials/FilmForm";
import DeadliftFlags from "./pages/tutorials/DeadliftFlags";
import SquatChecklist from "./pages/tutorials/SquatChecklist";
import PPLTemplate from "./pages/tutorials/PPLTemplate";

function App() {
  return (
    <div className="bg-slate-950 min-h-screen text-slate-100">
      <Navbar />
      <main className="max-w-6xl mx-auto px-6 py-10">
        <Routes>
          {/* Core pages */}
          <Route path="/" element={<Home />} />
          <Route path="/live" element={<LiveCoach />} />
          <Route path="/upload" element={<UploadVideo />} />
          <Route path="/plans" element={<Plans />} />

          {/* Tutorials hub + individual guides */}
          <Route path="/tutorials" element={<Blog />} />
          <Route path="/tutorials/film-form" element={<FilmForm />} />
          <Route path="/tutorials/deadlift-flags" element={<DeadliftFlags />} />
          <Route path="/tutorials/squat-checklist" element={<SquatChecklist />} />
          <Route path="/tutorials/ppl-template" element={<PPLTemplate />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
