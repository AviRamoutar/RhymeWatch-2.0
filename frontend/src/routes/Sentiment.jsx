import React from "react";
import { useNavigate } from "react-router-dom";
import DataTable from "../components/DataTable";
import { fmt } from "../lib/api";
import { DEFAULT_TICKERS } from "../stockTickers";

export default function Sentiment() {
  const navigate = useNavigate();
  const rows = React.useMemo(() =>
    DEFAULT_TICKERS.slice(0, 30).map((t, i) => ({
      id: t.symbol,
      symbol: t.symbol,
      name: t.name,
      mentions: 50 + ((i * 83) % 2000),
      pos: (i * 11) % 100,
      neg: (i * 7) % 100,
      escalated: (i * 3) % 20,
      avg: ((i * 13) % 200 - 100) / 100,
    })), []);

  const columns = [
    { key: "symbol", label: "Symbol", mono: true, width: 88,
      render: (r) => <span className="text-brand">{r.symbol}</span> },
    { key: "name", label: "Company",
      render: (r) => <span className="text-stone-300 truncate">{r.name}</span> },
    { key: "mentions", label: "Mentions 24h", align: "right", mono: true,
      render: (r) => fmt.num(r.mentions) },
    { key: "pos", label: "+", align: "right", mono: true,
      render: (r) => <span className="text-up">{r.pos}</span> },
    { key: "neg", label: "−", align: "right", mono: true,
      render: (r) => <span className="text-down">{r.neg}</span> },
    { key: "escalated", label: "LLM-esc", align: "right", mono: true,
      render: (r) => <span className="text-stone-400">{r.escalated}</span> },
    { key: "avg", label: "Score", align: "right", mono: true,
      render: (r) => <span className={r.avg >= 0 ? "text-up" : "text-down"}>{r.avg.toFixed(2)}</span> },
  ];

  return (
    <div className="px-6 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 micro text-stone-500">
            <span className="text-brand">§01</span>
            <span>sentiment · retail aggregates</span>
          </div>
          <h1 className="text-[28px] font-medium mt-1 text-stone-100">Three-tier sentiment pipeline</h1>
          <p className="text-[14px] text-stone-400 mt-2 max-w-[560px]">
            Tier 0: regex lexicon for WSB slang and emoji.
            Tier 1: ONNX-int8 <span className="num text-stone-300">finbert-tone</span> (~85MB).
            Tier 2: Gemini Flash-Lite escalation for sarcasm, multi-entity text, and aspect analysis.
          </p>
        </div>
        <span className="micro text-stone-500">cached 1–6h · upstash</span>
      </div>
      <DataTable columns={columns} rows={rows} onRowClick={(r) => navigate(`/ticker/${r.symbol}`)} />
    </div>
  );
}
