import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import FunctionKeyNav from "./components/FunctionKeyNav";
import CommandPalette from "./components/CommandPalette";
import Watchlist from "./routes/Watchlist";
import Ticker from "./routes/Ticker";
import Movers from "./routes/Movers";
import Sentiment from "./routes/Sentiment";
import Methodology from "./routes/Methodology";
import Changelog from "./routes/Changelog";

export default function App() {
  const [cmdkOpen, setCmdkOpen] = React.useState(false);
  const [lastUpdate, setLastUpdate] = React.useState("just now");

  React.useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdkOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  React.useEffect(() => {
    const t = setInterval(() => {
      const s = Math.floor(Math.random() * 30) + 1;
      setLastUpdate(`${s}s ago`);
    }, 3000);
    return () => clearInterval(t);
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen noise relative">
        <FunctionKeyNav onOpenCmdK={() => setCmdkOpen(true)} lastUpdate={lastUpdate} />
        <main className="max-w-[1400px] mx-auto">
          <Routes>
            <Route path="/" element={<Watchlist />} />
            <Route path="/ticker/:symbol" element={<Ticker />} />
            <Route path="/movers" element={<Movers />} />
            <Route path="/sentiment" element={<Sentiment />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/changelog" element={<Changelog />} />
          </Routes>
        </main>
        <footer className="border-t border-stone-800 mt-16">
          <div className="max-w-[1400px] mx-auto px-6 py-6 flex items-center justify-between micro text-stone-500">
            <div className="flex items-center gap-4">
              <span className="num text-brand">RW 2.0</span>
              <span>research software · not investment advice</span>
            </div>
            <div className="flex items-center gap-4">
              <NavLink to="/methodology" className="hover:text-stone-200">methodology</NavLink>
              <NavLink to="/changelog" className="hover:text-stone-200">changelog</NavLink>
              <a
                href="https://github.com/AviRamoutar/RhymeWatch-2.0"
                target="_blank"
                rel="noreferrer"
                className="hover:text-stone-200"
              >
                source
              </a>
            </div>
          </div>
        </footer>
        <CommandPalette open={cmdkOpen} onClose={() => setCmdkOpen(false)} />
      </div>
    </BrowserRouter>
  );
}
