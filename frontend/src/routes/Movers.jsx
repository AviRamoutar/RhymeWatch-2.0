import React from "react";
import { useNavigate } from "react-router-dom";
import DataTable from "../components/DataTable";
import { fmt } from "../lib/api";
import { DEFAULT_TICKERS } from "../stockTickers";

export default function Movers() {
  const navigate = useNavigate();
  const rows = React.useMemo(() =>
    DEFAULT_TICKERS.slice(0, 40).map((t, i) => ({
      id: t.symbol,
      symbol: t.symbol,
      name: t.name,
      price: 50 + i * 4.2,
      change: (i % 2 === 0 ? 1 : -1) * (1 + (i % 9) * 0.7),
      volume: 1_200_000 + (i * 317_000),
      rsi: 30 + (i * 2.1) % 40,
    })), []);

  const columns = [
    { key: "symbol", label: "Symbol", mono: true, width: 88,
      render: (r) => <span className="text-brand">{r.symbol}</span> },
    { key: "name", label: "Company",
      render: (r) => <span className="text-stone-300 truncate">{r.name}</span> },
    { key: "price", label: "Last", align: "right", mono: true, render: (r) => fmt.price(r.price) },
    { key: "change", label: "Δ %", align: "right", mono: true,
      render: (r) => <span className={r.change >= 0 ? "text-up" : "text-down"}>{fmt.pct(r.change)}</span> },
    { key: "volume", label: "Volume", align: "right", mono: true, render: (r) => fmt.compact(r.volume) },
    { key: "rsi", label: "RSI-14", align: "right", mono: true,
      render: (r) => {
        const tone = r.rsi > 70 ? "text-down" : r.rsi < 30 ? "text-up" : "text-stone-300";
        return <span className={tone}>{r.rsi.toFixed(1)}</span>;
      } },
  ];

  return (
    <div className="px-6 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 micro text-stone-500">
            <span className="text-brand">§01</span>
            <span>movers · last session</span>
          </div>
          <h1 className="text-[28px] font-medium mt-1 text-stone-100">Largest absolute moves</h1>
        </div>
        <span className="micro text-stone-500">precomputed · cron · 22:00 UTC</span>
      </div>
      <DataTable columns={columns} rows={rows} onRowClick={(r) => navigate(`/ticker/${r.symbol}`)} />
    </div>
  );
}
