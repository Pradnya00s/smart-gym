// src/components/Navbar.tsx
import { Link, useLocation } from "react-router-dom";
import { useTheme } from "../theme/useTheme";

export default function Navbar() {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { name: "Home", to: "/" },
    { name: "Live Coaching", to: "/live" },
    { name: "Upload Video", to: "/upload" },
    { name: "Plans", to: "/plans" },
    { name: "Tutorials", to: "/tutorials" },
  ];

  return (
    <div className="w-full border-b border-slate-700/50 bg-slate-950/80 backdrop-blur-md">
      <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 flex items-center justify-center rounded-full bg-accent text-white font-bold">
            SG
          </div>
          <span className="font-semibold text-lg text-slate-100">
            Smart Gym
          </span>
        </Link>

        {/* Nav links + theme toggle */}
        <div className="flex items-center gap-6">
          {navItems.map((item) => {
            const active = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`text-sm font-medium transition ${
                  active
                    ? "text-accent-strong border-b-2 border-accent-strong pb-1"
                    : "text-slate-300 hover:text-slate-50"
                }`}
              >
                {item.name}
              </Link>
            );
          })}

          {/* Theme toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="ml-2 inline-flex items-center gap-1 rounded-full border border-slate-600 px-3 py-1 text-xs font-medium text-slate-200 hover:bg-slate-800"
          >
            <span>{theme === "dark" ? "🌙" : "☀️"}</span>
            <span>{theme === "dark" ? "Dark" : "Light"}</span>
          </button>
        </div>
      </nav>
    </div>
  );
}
