import React from "react";
import { useNavigate } from "react-router-dom";
import TickerCard from "../components/TickerCard";
import DataTable from "../components/DataTable";
import { fmt, api } from "../lib/api";
import { DEFAULT_TICKERS } from "../stockTickers";

const HERO_TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "AMD", "AMZN"];

function fakeSeries(seed = 1, n = 24) {
  let x = seed;
  return Array.from({ length: n }, () => {
    x = (x * 9301 + 49297) % 233280;
    return 100 + (x / 233280) * 20 - 10;
  });
}

export default function Watchlist() {
  const navigate = useNavigate();
  const [quotes, setQuotes] = React.useState(() =>
    HERO_TICKERS.map((s, i) => ({
      symbol: s,
      name: DEFAULT_TICKERS.find((t) => t.symbol === s)?.name ?? s,
      price: 150 + i * 7.23,
      change: (i % 2 === 0 ? 1 : -1) * (0.5 + i * 0.4),
      series: fakeSeries(i + 1),
    }))
  );
  const [watchlist] = React.useState(
    DEFAULT_TICKERS.slice(0, 20).map((t, i) => ({
      id: t.symbol,
      symbol: t.symbol,
      name: t.name,
      price: 50 + i * 3.7,
      change: (i % 3 === 0 ? -1 : 1) * (0.1 + (i % 7) * 0.3),
      sentiment: (i % 4 === 0 ? "pos" : i % 4 === 1 ? "neg" : "neu"),
      mentions: 120 + ((i * 37) % 500),
      signal: (i % 5 === 0 ? "↑" : i % 5 === 1 ? "↓" : "→"),
    }))
  );

  React.useEffect(() => {
    let alive = true;
    const tick = setInterval(() => {
      if (!alive) return;
      setQuotes((q) =>
        q.map((row) => {
          const d = (Math.random() - 0.5) * 0.6;
          return {
            ...row,
            price: +(row.price + d).toFixed(2),
            change: +(row.change + d / 10).toFixed(2),
          };
        })
      );
    }, 2500);
    return () => { alive = false; clearInterval(tick); };
  }, []);

  const columns = [
    { key: "symbol", label: "Symbol", width: 88, mono: true,
      render: (r) => <span className="text-brand">{r.symbol}</span> },
    { key: "name", label: "Company",
      render: (r) => <span className="text-stone-300 truncate">{r.name}</span> },
    { key: "price", label: "Last", align: "right", mono: true,
      render: (r) => fmt.price(r.price) },
    { key: "change", label: "Δ", align: "right", mono: true,
      render: (r) => (
        <span className={r.change >= 0 ? "text-up" : "text-down"}>{fmt.pct(r.change)}</span>
      ) },
    { key: "sentiment", label: "Sent", align: "center",
      render: (r) => (
        <span className={
          r.sentiment === "pos" ? "text-up" :
          r.sentiment === "neg" ? "text-down" : "text-stone-500"
        }>
          {r.sentiment === "pos" ? "+" : r.sentiment === "neg" ? "−" : "·"}
        </span>
      ) },
    { key: "mentions", label: "Mentions 24h", align: "right", mono: true,
      render: (r) => fmt.num(r.mentions) },
    { key: "signal", label: "Signal", align: "center", mono: true,
      render: (r) => <span className={r.signal === "↑" ? "text-up" : r.signal === "↓" ? "text-down" : "text-stone-500"}>{r.signal}</span> },
  ];

  return (
    <div className="px-6 py-6">
      {/* Asymmetric 7/5 hero */}
      <section className="grid grid-cols-12 gap-8 mb-10">
        <div className="col-span-12 lg:col-span-7 flex flex-col justify-between">
          <div className="flex items-center gap-3 micro text-stone-500">
            <span className="text-brand">§01</span>
            <span>watchlist</span>
            <span className="text-stone-700">/</span>
            <span>us equities · intraday</span>
          </div>
          <div className="mt-6">
            <h1 className="text-[40px] leading-[1.05] font-medium text-stone-100 max-w-[640px]">
              Sentiment and technicals for 8,000 US tickers, back-tested with walk-forward validation.
            </h1>
            <p className="mt-5 text-[15px] text-stone-400 max-w-[560px] leading-relaxed">
              Realistic directional accuracy per ticker — disclosed, not promised. Features from{" "}
              <span className="text-stone-200">pandas-ta</span>, sentiment from an ONNX FinBERT with LLM
              escalation for sarcasm and aspects.
            </p>
            <div className="mt-6 flex items-center gap-3">
              <button onClick={() => navigate("/methodology")} className="btn-ghost-amber">
                Read the methodology →
              </button>
              <button onClick={() => navigate("/movers")} className="btn-ghost">
                Top movers
              </button>
              <span className="micro text-stone-500 ml-2">
                backtest: 53.4% directional · 5yr · net 10bps
              </span>
            </div>
          </div>
          <div className="mt-10 flex items-center gap-4 micro text-stone-500">
            <span>Source:</span>
            <span className="text-stone-300">SEC EDGAR</span>
            <span className="text-stone-700">·</span>
            <span className="text-stone-300">Reddit / ApeWisdom</span>
            <span className="text-stone-700">·</span>
            <span className="text-stone-300">StockTwits</span>
            <span className="text-stone-700">·</span>
            <span className="text-stone-300">Finnhub</span>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5">
          <div className="flex items-center justify-between mb-3">
            <span className="micro text-stone-500">top signals · live</span>
            <span className="micro text-stone-500">updated every 2.5s</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {quotes.map((q) => (
              <TickerCard
                key={q.symbol}
                symbol={q.symbol}
                name={q.name}
                price={q.price}
                change={q.change}
                series={q.series}
                onClick={() => navigate(`/ticker/${q.symbol}`)}
              />
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3 micro text-stone-500">
            <span className="text-brand">§02</span>
            <span>watchlist · 20 tickers</span>
          </div>
          <div className="flex items-center gap-2 micro text-stone-500">
            <span className="kbd">↵</span>
            <span>open ticker</span>
          </div>
        </div>
        <DataTable
          columns={columns}
          rows={watchlist}
          onRowClick={(r) => navigate(`/ticker/${r.symbol}`)}
        />
        <figcaption className="mt-2 micro text-stone-500">
          Signal column uses the LightGBM model on log-returns · updated at 22:00 UTC daily
        </figcaption>
      </section>
    </div>
  );
}
