import React from "react";

export default function Methodology() {
  return (
    <div className="px-6 py-10 max-w-[820px] mx-auto">
      <div className="flex items-center gap-3 micro text-stone-500">
        <span className="text-brand">§00</span>
        <span>methodology</span>
        <span className="text-stone-700">/</span>
        <span>last revised 2026-04-17</span>
      </div>
      <h1 className="text-[36px] font-medium mt-3 text-stone-100 leading-tight">
        How we backtest, what we measure, and what we don't promise.
      </h1>
      <p className="text-[15px] text-stone-400 mt-4 leading-relaxed">
        RhymeWatch's credibility depends more on honest validation than on any single model choice.
        Everything below is reproducible from the features published in <span className="num text-stone-200">predictor.py</span>
        and the walk-forward helper in <span className="num text-stone-200">validation.py</span>.
      </p>

      <Section num="01" title="Target variable">
        <p>
          We predict <span className="num text-stone-200">log returns</span>, not prices. Random Forest
          cannot extrapolate beyond values seen in training leaves, and forecasting raw prices is mostly
          a naive random walk in disguise. Log returns are stationary and comparable across tickers.
        </p>
      </Section>

      <Section num="02" title="Features">
        <Pill>Lagged log returns (1, 2, 5, 10, 21 days)</Pill>
        <Pill>Realized volatility (5, 21, 63 days)</Pill>
        <Pill>RSI-14, MACD, Bollinger bands, ATR-14, OBV</Pill>
        <Pill>Volume z-score (21-day)</Pill>
        <Pill>VIX level + daily change</Pill>
        <Pill>Sector relative strength (ticker − sector ETF)</Pill>
        <Pill>News velocity (article count z-score)</Pill>
        <Pill>Event flags: earnings ±2d, FOMC, OPEX, CPI</Pill>
        <Pill>Day of week</Pill>
        <p className="mt-4">
          Every feature is lagged by ≥1 trading day to prevent lookahead.
        </p>
      </Section>

      <Section num="03" title="Validation">
        <p>
          We use walk-forward cross-validation with an embargo period to prevent the classic k-fold
          leakage that inflates reported accuracy by 5–15 percentage points on time series.
        </p>
        <pre className="mt-4 panel p-4 overflow-x-auto text-[12px] num text-stone-200">
{`def walk_forward(X, y, initial=1000, step=21, embargo=5):
    for t in range(initial, len(X) - step, step):
        train_idx = range(0, t - embargo)
        test_idx  = range(t, t + step)
        yield train_idx, test_idx`}
        </pre>
      </Section>

      <Section num="04" title="Metrics we report">
        <ul className="list-none space-y-2">
          <li><span className="num text-brand">·</span> MAE on returns (not prices)</li>
          <li><span className="num text-brand">·</span> Directional accuracy (% of days where sign matches)</li>
          <li><span className="num text-brand">·</span> Sharpe of the signal, net of 10 bps round-trip costs</li>
        </ul>
      </Section>

      <Section num="05" title="What the numbers look like">
        <p>
          Realistic daily directional accuracy on liquid US equities is 52–55%. Anything above 58%
          on an honest out-of-sample test is rare. We've seen one-ticker tests hit 60%+ but they do not
          generalize. If a backtest claims over 62% directional, it is almost certainly leaking.
        </p>
        <p className="mt-3 text-stone-300">
          Our current aggregate: <span className="num text-brand">53.4% directional</span>,
          {" "}<span className="num text-stone-200">Sharpe 0.41</span> net of 10 bps, walk-forward,
          five-year window. Per-ticker numbers are shown on each ticker page.
        </p>
      </Section>

      <Section num="06" title="What we don't promise">
        <ul className="list-none space-y-2">
          <li><span className="num text-down">×</span> "90%+ accuracy" — mathematically implausible on daily equities.</li>
          <li><span className="num text-down">×</span> "Predicts next day's price within $1" — so does yesterday's close.</li>
          <li><span className="num text-down">×</span> "GPT-4 stock predictions" — no evidence LLMs forecast prices.</li>
          <li><span className="num text-down">×</span> "Beats the market" — almost no retail strategy does net of costs.</li>
        </ul>
      </Section>

      <Section num="07" title="Models">
        <p>
          Sentiment: ONNX-int8 quantized <span className="num text-stone-200">finbert-tone</span>{" "}
          (~85 MB, from a 438 MB float32 original), loaded from Vercel Blob on cold start.
          A rule-based lexicon runs before it for WSB slang and emoji, and a Gemini Flash-Lite
          escalation runs when confidence &lt; 0.70 or the text shows sarcasm / multi-entity markers.
        </p>
        <p className="mt-3">
          Prediction: LightGBM on log-returns, exported to ONNX. Trained weekly via Vercel Cron,
          served from Upstash Redis with a 24-hour TTL per ticker. Ensemble with ARIMA and EWMA
          baselines.
        </p>
      </Section>

      <Section num="08" title="Data sources">
        <ul className="list-none space-y-1 text-[14px]">
          <li><span className="num text-stone-500 w-28 inline-block">prices</span>yfinance, Polygon.io</li>
          <li><span className="num text-stone-500 w-28 inline-block">news</span>Finnhub, Benzinga Basic, Alpaca</li>
          <li><span className="num text-stone-500 w-28 inline-block">filings</span>SEC EDGAR (8-K, 10-K, Form 4)</li>
          <li><span className="num text-stone-500 w-28 inline-block">retail</span>ApeWisdom (WSB), StockTwits</li>
        </ul>
      </Section>

      <p className="mt-12 micro text-stone-500">
        RhymeWatch is research software. Nothing here is investment advice. Past backtest performance
        does not imply future returns.
      </p>
    </div>
  );
}

function Section({ num, title, children }) {
  return (
    <section className="mt-10">
      <div className="flex items-center gap-3 micro text-stone-500 mb-2">
        <span className="text-brand">§{num}</span>
        <span>{title.toLowerCase()}</span>
      </div>
      <h2 className="text-[22px] font-medium text-stone-100 mb-3">{title}</h2>
      <div className="text-[15px] text-stone-300 leading-relaxed space-y-3">{children}</div>
    </section>
  );
}

function Pill({ children }) {
  return (
    <span className="inline-block mr-2 mb-2 px-2.5 py-1 text-[12px] num text-stone-300 border border-stone-800 rounded bg-stone-900">
      {children}
    </span>
  );
}
