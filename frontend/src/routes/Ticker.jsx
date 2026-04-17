import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import Sparkline from "../components/Sparkline";
import CellFlash from "../components/CellFlash";
import { api, fmt } from "../lib/api";
import { DEFAULT_TICKERS } from "../stockTickers";

export default function Ticker() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [data, setData] = React.useState(null);
  const [error, setError] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [range, setRange] = React.useState("180");

  const name = DEFAULT_TICKERS.find((t) => t.symbol === symbol)?.name ?? symbol;

  React.useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .analyze(symbol, Number(range))
      .then((d) => setData(d))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol, range]);

  const price = data?.priceHistory?.[data.priceHistory.length - 1];
  const prev = data?.priceHistory?.[data.priceHistory.length - 2];
  const change = price && prev ? ((price - prev) / prev) * 100 : null;
  const series = data?.priceHistory ?? [];

  return (
    <div className="px-6 py-6">
      <div className="flex items-center justify-between mb-6">
        <button onClick={() => navigate(-1)} className="micro text-stone-500 hover:text-stone-300">
          ← back
        </button>
        <div className="flex items-center gap-2">
          {["30", "90", "180", "365"].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`kbd ${range === r ? "!text-amber-400 !border-amber-500/40" : ""}`}
            >
              {r}d
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-7">
          <div className="flex items-baseline gap-4">
            <span className="num text-brand text-[28px] leading-none">{symbol}</span>
            <span className="text-[14px] text-stone-400">{name}</span>
          </div>
          <div className="mt-4 flex items-baseline gap-5">
            <CellFlash value={price} className="num text-[56px] leading-none text-stone-50">
              <span>{fmt.price(price)}</span>
            </CellFlash>
            <span className={`num text-[18px] ${change >= 0 ? "text-up" : "text-down"}`}>
              {fmt.pct(change)}
            </span>
          </div>

          <div className="mt-6 panel p-4">
            <div className="flex items-center justify-between micro text-stone-500 mb-2">
              <span>price · {range}d</span>
              <span>source: yfinance</span>
            </div>
            {series.length > 0 ? (
              <Sparkline values={series} width={720} height={220} up={change >= 0} />
            ) : (
              <div className="h-[220px] flex items-center justify-center text-stone-600 micro">
                {loading ? "loading…" : error ? `error: ${error}` : "no data"}
              </div>
            )}
            <figcaption className="mt-2 micro text-stone-500">
              Close only · split adjusted · trading days only
            </figcaption>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 space-y-4">
          <div className="panel p-4">
            <div className="micro text-stone-500 mb-3">sentiment · last {range}d</div>
            <div className="grid grid-cols-3 gap-3">
              <StatBlock label="positive" value={data?.sentimentCounts?.positive} tone="up" />
              <StatBlock label="neutral" value={data?.sentimentCounts?.neutral} tone="neutral" />
              <StatBlock label="negative" value={data?.sentimentCounts?.negative} tone="down" />
            </div>
            <div className="divider my-4" />
            <div className="flex items-center justify-between">
              <span className="micro text-stone-500">model</span>
              <span className="num text-[12px] text-stone-300">
                {data?.sentimentModel ?? "finbert-tone-int8"}
              </span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="micro text-stone-500">escalations</span>
              <span className="num text-[12px] text-stone-300">
                {data?.escalations ?? 0} / {data?.total_headlines ?? 0}
              </span>
            </div>
          </div>

          <div className="panel p-4">
            <div className="micro text-stone-500 mb-3">next-day signal</div>
            <div className="flex items-center justify-between">
              <span className="text-[28px] num text-brand">
                {data?.nextDay?.direction ?? "—"}
              </span>
              <div className="text-right">
                <div className="micro text-stone-500">expected return</div>
                <div className="num text-stone-100 text-[14px]">
                  {fmt.pct(data?.nextDay?.expectedReturn)}
                </div>
              </div>
            </div>
            <div className="divider my-4" />
            <Row k="model" v={data?.nextDay?.model ?? "lightgbm · returns target"} />
            <Row k="features" v={data?.nextDay?.features ?? "21 (technicals + sentiment + event flags)"} />
            <Row k="directional acc (walk-forward)" v={fmt.pct(data?.nextDay?.directionalAccuracy)} />
            <Row k="sharpe (net 10bps)" v={data?.nextDay?.sharpe ?? "—"} mono />
            <Row k="trained" v={data?.nextDay?.trainedAt ?? "—"} />
            <p className="micro text-stone-500 mt-3 leading-relaxed">
              Reported accuracy is backtest only and does not guarantee future performance. We don't promise
              better than 55% directional because no honest backtest of liquid US equities does.
            </p>
          </div>
        </div>
      </div>

      <section className="mt-8">
        <div className="flex items-center gap-3 micro text-stone-500 mb-3">
          <span className="text-brand">§03</span>
          <span>recent headlines · classified</span>
        </div>
        <div className="panel divide-y divide-stone-800">
          {(data?.news ?? []).slice(0, 15).map((n, i) => (
            <div key={i} className="flex items-center gap-4 px-4 py-2 hover:bg-stone-800/40">
              <span className={
                "num text-[11px] w-10 shrink-0 " +
                (n.sentiment === "positive" ? "text-up"
                  : n.sentiment === "negative" ? "text-down" : "text-stone-500")
              }>
                {n.sentiment === "positive" ? "POS" : n.sentiment === "negative" ? "NEG" : "NEU"}
              </span>
              <span className="text-[13px] text-stone-200 flex-1 truncate">{n.headline}</span>
              <span className="num text-[11px] text-stone-500 shrink-0">
                {fmt.ago(n.date)}
              </span>
            </div>
          ))}
          {(data?.news ?? []).length === 0 && !loading && (
            <div className="px-4 py-6 text-[13px] text-stone-500">
              no headlines returned · try a longer range
            </div>
          )}
          {loading && <div className="px-4 py-6 text-[13px] text-stone-500">loading headlines…</div>}
        </div>
      </section>
    </div>
  );
}

function Row({ k, v, mono }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="micro text-stone-500">{k}</span>
      <span className={`text-[12px] text-stone-300 ${mono ? "num" : ""}`}>{v}</span>
    </div>
  );
}

function StatBlock({ label, value, tone }) {
  const color = tone === "up" ? "text-up" : tone === "down" ? "text-down" : "text-stone-300";
  return (
    <div className="flex flex-col">
      <span className="micro text-stone-500">{label}</span>
      <span className={`num text-[22px] mt-1 ${color}`}>{value ?? 0}</span>
    </div>
  );
}
