import React from "react";

export default function LiveIndicator({ label = "LIVE", updatedAt }) {
  return (
    <div className="flex items-center gap-2 micro text-stone-400">
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full rounded-full bg-amber-500 opacity-60 animate-pulse-dot" />
        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-amber-500" />
      </span>
      <span className="text-amber-500">{label}</span>
      {updatedAt && <span className="text-stone-500 num">· {updatedAt}</span>}
    </div>
  );
}
