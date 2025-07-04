import streamlit as st
from datetime import date, timedelta
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import yfinance as yf

from scraper import get_headlines
from sentiment import load_sentiment_model, classify_headlines
from predictor import train_random_forest, predict_next_day
from utils import parse_relative_date

# ---------- constants ----------
MAX_LOOKBACK_DAYS = 90
DATE_FMT = "MM/DD/YYYY"
POPULAR = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL",
           "TSLA", "META", "NFLX", "AMD", "INTC"]

# ---------- global CSS ----------
st.markdown(
    """
    <style>
      body {font-family: Inter, sans-serif;}
      .stButton>button {border-radius:8px; background:#e11d48; color:white;}
      .stButton>button:hover {background:#be123c;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- sidebar ----------
st.sidebar.title("📈 Quick Tickers")

# 3-D model (spinnable spaceship)
import streamlit.components.v1 as components

components.html(
    """
    <!-- 3-D model (CORS-friendly ISS from NASA) -->
    <script type="module"
            src="https://cdn.jsdelivr.net/npm/@google/model-viewer@1.12.1/dist/model-viewer.min.js">
    </script>

    <model-viewer src="https://cdn.jsdelivr.net/gh/nasa/NASA-3D-Resources@main/3D%20Models/ISS.glb"
                  alt="International Space Station"
                  style="width: 220px; height: 220px;"
                  camera-controls
                  auto-rotate>
    </model-viewer>
    """,
    height=235,
)


st.sidebar.subheader("Popular")
for t in POPULAR:
    if st.sidebar.button(t, key=f"pop_{t}"):
        st.session_state["ticker"] = t

st.sidebar.subheader("My Tickers")
if "my_tickers" not in st.session_state:
    st.session_state.my_tickers = []
for t in st.session_state.my_tickers:
    if st.sidebar.button(t, key=f"my_{t}"):
        st.session_state["ticker"] = t

# ---------- main header ----------
st.title("AI Stock News Sentiment Analyzer 🚀")

# ---------- inputs ----------
today = date.today()
default_start = today - timedelta(days=7)

ticker = st.text_input("Enter Stock Ticker:", value=st.session_state.get("ticker", "MSFT")).upper()

# ---------- quick-range selector ----------
RANGE_OPTIONS = {
    "Last 24 hours": 1,
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 60 days": 60,
    "Last 90 days": 90,
}

range_label = st.selectbox(
    "Time Window",
    list(RANGE_OPTIONS.keys()),
    index=1  # pre-select “Last 7 days”
)

days_back = RANGE_OPTIONS[range_label]
end = today
start = today - timedelta(days=days_back)


# ---------- run ----------
if st.button("Analyze"):
    st.session_state["ticker"] = ticker  # remember last used

    if not ticker:
        st.error("Please enter a valid ticker symbol.")
        st.stop()

    raw = get_headlines(ticker)
    if not raw:
        st.info("No headlines returned by the API for this ticker.")
        st.stop()

    # filter by date
    heads, dts = [], []
    for title, ts in raw:
        d = parse_relative_date(ts)
        if d and start <= d <= end:
            heads.append(title)
            dts.append(d)

    if not heads:
        st.warning(f"No news between {start.strftime(DATE_FMT)} and {end.strftime(DATE_FMT)}.")
        st.stop()

    # sentiment
    nlp = load_sentiment_model()
    labels = classify_headlines(nlp, heads)
    score_map = {"positive": 1, "neutral": 0, "negative": -1}
    scores = [score_map[l] for l in labels]
    df = pd.DataFrame({"headline": heads, "date": dts, "label": labels, "score": scores})
    daily = df.groupby("date")["score"].mean().reset_index(name="avg_score")

    # price
    yf_end = end + timedelta(days=1)   # include end day
    price = yf.Ticker(ticker).history(start=start, end=yf_end)["Close"].reset_index()
    price["Date"] = price["Date"].dt.date
    merged = pd.merge(price, daily, left_on="Date", right_on="date", how="left").fillna(0)

    # ML
    model = train_random_forest(merged)
    pred = predict_next_day(model, merged.tail(1)["avg_score"].values.reshape(-1, 1))
    st.metric("Next-day prediction", "⬆ Up" if pred else "⬇ Down")

    # charts
    col1, col2 = st.columns(2)
    with col1:
        pie = df["label"].value_counts().rename_axis("sent").reset_index(name="cnt")
        st.plotly_chart(px.pie(pie, values="cnt", names="sent", title="Sentiment mix"),
                        use_container_width=True)
    with col2:
        st.plotly_chart(px.bar(daily, x="date", y="avg_score",
                               title="Daily avg sentiment"), use_container_width=True)

    st.plotly_chart(px.line(merged, x="Date", y="Close",
                            title=f"{ticker} close price"),
                    use_container_width=True)

    # 3-D scatter
    merged["idx"] = np.arange(len(merged))
    fig3d = go.Figure(data=go.Scatter3d(
        x=merged["idx"], y=merged["Close"], z=merged["avg_score"],
        mode="markers",
        marker=dict(size=5, color=merged["avg_score"], colorscale="RdYlGn")
    ))
    fig3d.update_layout(title="3-D: day × price × sentiment",
                        scene=dict(xaxis_title="#", yaxis_title="Price", zaxis_title="Sentiment"))
    st.plotly_chart(fig3d, use_container_width=True)

    # save ticker
    if ticker not in st.session_state.my_tickers:
        if st.button("⭐ Add to My Tickers"):
            st.session_state.my_tickers.append(ticker)
            st.experimental_rerun()
