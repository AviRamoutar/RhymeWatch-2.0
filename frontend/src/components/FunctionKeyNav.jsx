import React from "react";
import clsx from "clsx";
import { NavLink, useNavigate } from "react-router-dom";
import LiveIndicator from "./LiveIndicator";

const KEYS = [
  { fkey: "F1", label: "Watchlist", path: "/" },
  { fkey: "F2", label: "Movers", path: "/movers" },
  { fkey: "F3", label: "Sentiment", path: "/sentiment" },
  { fkey: "F4", label: "Methodology", path: "/methodology" },
];

export default function FunctionKeyNav({ onOpenCmdK, lastUpdate }) {
  const navigate = useNavigate();
  React.useEffect(() => {
    const onKey = (e) => {
      const map = { F1: "/", F2: "/movers", F3: "/sentiment", F4: "/methodology" };
      if (map[e.key]) {
        e.preventDefault();
        navigate(map[e.key]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navigate]);

  return (
    <header className="sticky top-0 z-40 border-b border-stone-800 bg-stone-950/95 backdrop-blur-none">
      <div className="px-6 h-12 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="num text-brand text-[14px] tracking-widest">RW</span>
            <span className="micro text-stone-500">rhymewatch</span>
          </NavLink>
          <nav className="flex items-center gap-5">
            {KEYS.map((k) => (
              <NavLink
                key={k.fkey}
                to={k.path}
                className={({ isActive }) =>
                  clsx(
                    "group inline-flex items-center gap-2 py-3",
                    "text-[13px] text-stone-400 hover:text-stone-100 transition-colors",
                    isActive && "text-stone-100"
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <span className={clsx("kbd", isActive && "!text-amber-400 !border-amber-500/40")}>{k.fkey}</span>
                    <span>{k.label}</span>
                  </>
                )}
              </NavLink>
            ))}
            <button
              onClick={onOpenCmdK}
              className="inline-flex items-center gap-2 py-3 text-[13px] text-stone-400 hover:text-stone-100 transition-colors"
            >
              <span className="kbd">⌘K</span>
              <span>Search</span>
            </button>
          </nav>
        </div>
        <LiveIndicator updatedAt={lastUpdate} />
      </div>
    </header>
  );
}
