import React from "react";

const ENTRIES = [
  {
    version: "2.0.0",
    date: "2026-04-17",
    tag: "major",
    title: "Bloomberg-meets-Linear redesign + honest ML rewrite",
    body: [
      "Replaced glassmorphism + indigo gradients with warm stone + amber accent. Entire surface reworked.",
      "Added ⌘K command palette and F1–F4 function-key navigation.",
      "Replaced FinBERT (PyTorch, 438 MB) with ONNX-int8 finbert-tone (~85 MB) served from Vercel Blob.",
      "Replaced sklearn RandomForestClassifier + train_test_split with LightGBM on log-returns and walk-forward cross-validation with embargo.",
      "Added 21 features from pandas-ta: lagged returns, RV at 5/21/63d, RSI, MACD, BBands, ATR, OBV, volume z-score, VIX, sector RS, news velocity, earnings/FOMC/OPEX/CPI flags.",
      "Honest metric disclosure: MAE on returns, directional accuracy, Sharpe net of 10 bps — published per ticker.",
      "Three-tier sentiment: regex lexicon → ONNX classifier → Gemini Flash-Lite escalation for sarcasm / multi-entity / aspects.",
      "New /methodology route documents target, features, validation, and realistic accuracy.",
      "Fixed backend bugs: Mangum handler reference order, CORS allow_origins=['*'] with credentials.",
      "requirements.txt trimmed from ~950 MB (with torch) to ~170 MB — fits Vercel's 250 MB Python limit.",
    ],
  },
];

export default function Changelog() {
  return (
    <div className="px-6 py-10 max-w-[760px] mx-auto">
      <div className="flex items-center gap-3 micro text-stone-500">
        <span className="text-brand">§00</span>
        <span>changelog</span>
      </div>
      <h1 className="text-[36px] font-medium text-stone-100 mt-3 leading-tight">What changed.</h1>
      <p className="text-[15px] text-stone-400 mt-3 leading-relaxed">
        Opinionated notes per release. If something broke in your workflow, it's probably mentioned below.
      </p>

      <div className="mt-12 space-y-12">
        {ENTRIES.map((e) => (
          <article key={e.version} className="relative">
            <div className="flex items-baseline justify-between mb-3">
              <div className="flex items-baseline gap-3">
                <span className="num text-brand text-[20px]">{e.version}</span>
                <span className="micro text-stone-500">{e.date}</span>
                <span className="micro text-amber-500 border border-amber-500/30 rounded px-1.5 py-0.5 bg-amber-500/5">
                  {e.tag}
                </span>
              </div>
            </div>
            <h2 className="text-[22px] font-medium text-stone-100">{e.title}</h2>
            <ul className="mt-4 space-y-2 text-[14px] text-stone-300 leading-relaxed">
              {e.body.map((b, i) => (
                <li key={i} className="flex gap-3">
                  <span className="text-brand num select-none">·</span>
                  <span>{b}</span>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </div>
  );
}
