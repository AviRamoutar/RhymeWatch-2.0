import React from "react";
import clsx from "clsx";
import Sparkline from "./Sparkline";
import { fmt } from "../lib/api";

export default function TickerCard({ symbol, name, price, change, series, onClick }) {
  const up = (change ?? 0) >= 0;
  return (
    <button
      onClick={onClick}
      className="panel text-left w-full h-24 px-4 py-3 flex flex-col justify-between hover:bg-stone-800/60 transition-colors focus-visible:outline-amber-500"
      style={{ width: 320 }}
    >
      <div className="flex items-start justify-between">
        <div className="flex flex-col">
          <span className="num text-[18px] text-brand leading-none">{symbol}</span>
          <span className="text-[11px] text-stone-400 mt-1 truncate max-w-[180px]">{name}</span>
        </div>
        <Sparkline values={series} up={up} />
      </div>
      <div className="flex items-baseline justify-between">
        <span className="num text-[22px] text-stone-50 leading-none">{fmt.price(price)}</span>
        <span className={clsx("num text-[13px] leading-none", up ? "text-up" : "text-down")}>
          {fmt.pct(change)}
        </span>
      </div>
    </button>
  );
}
