import React from "react";
import { Command } from "cmdk";
import { useNavigate } from "react-router-dom";
import { DEFAULT_TICKERS } from "../stockTickers";

const ROUTES = [
  { label: "Watchlist", path: "/" },
  { label: "Movers", path: "/movers" },
  { label: "Sentiment", path: "/sentiment" },
  { label: "Methodology", path: "/methodology" },
  { label: "Changelog", path: "/changelog" },
];

export default function CommandPalette({ open, onClose }) {
  const navigate = useNavigate();
  const go = (path) => { onClose(); navigate(path); };

  React.useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        open ? onClose() : window.dispatchEvent(new CustomEvent("rw:cmdk"));
      }
      if (e.key === "Escape" && open) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-start justify-center pt-[12vh]" onClick={onClose}>
      <div
        className="w-full max-w-xl mx-4 rounded-md border border-amber-500/30 bg-stone-950 shadow-etched"
        onClick={(e) => e.stopPropagation()}
      >
        <Command label="Global Command Palette" className="w-full">
          <Command.Input
            placeholder="Type a ticker, command, or route…"
            className="num w-full bg-transparent px-4 py-3 text-[15px] text-stone-100 placeholder:text-stone-500 border-b border-stone-800 focus:outline-none"
          />
          <Command.List className="max-h-[320px] overflow-auto p-1">
            <Command.Empty className="px-4 py-6 text-[13px] text-stone-500">
              No results. Try a ticker like AAPL or a route.
            </Command.Empty>
            <Command.Group heading="Routes" className="micro text-stone-500 px-2 pt-2">
              {ROUTES.map((r) => (
                <Command.Item
                  key={r.path}
                  onSelect={() => go(r.path)}
                  className="flex items-center justify-between px-3 py-2 text-[13px] rounded text-stone-300 aria-selected:bg-stone-900 aria-selected:text-stone-100 cursor-pointer"
                >
                  <span>{r.label}</span>
                  <span className="micro text-stone-500">route</span>
                </Command.Item>
              ))}
            </Command.Group>
            <Command.Group heading="Tickers" className="micro text-stone-500 px-2 pt-2">
              {DEFAULT_TICKERS.slice(0, 200).map((t) => (
                <Command.Item
                  key={t.symbol}
                  value={`${t.symbol} ${t.name}`}
                  onSelect={() => go(`/ticker/${t.symbol}`)}
                  className="flex items-center justify-between px-3 py-2 rounded text-stone-300 aria-selected:bg-stone-900 aria-selected:text-stone-100 cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <span className="num text-brand text-[13px] w-14">{t.symbol}</span>
                    <span className="text-[13px] text-stone-400 truncate">{t.name}</span>
                  </div>
                  <span className="micro text-stone-500">ticker</span>
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
          <div className="flex items-center justify-between px-3 py-2 border-t border-stone-800 micro text-stone-500">
            <div className="flex items-center gap-3">
              <span><span className="kbd mr-1">↑↓</span>navigate</span>
              <span><span className="kbd mr-1">↵</span>select</span>
              <span><span className="kbd mr-1">esc</span>close</span>
            </div>
            <span>rhymewatch ⌘K</span>
          </div>
        </Command>
      </div>
    </div>
  );
}
