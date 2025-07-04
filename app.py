import os, datetime
import streamlit as st
import plotly.graph_objs as go
import pandas as pd
import nltk                                 # NEW
from nltk.sentiment import SentimentIntensityAnalyzer  # NEW
import datetime as dt
from scraper import get_headlines
# ...

# Make sure VADER lexicon is available (downloads once)
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

# ----- Page Config & Style -----
st.set_page_config(page_title="AI Stock News Sentiment Analyzer", page_icon="🚀", layout="wide")
# Custom CSS for dark theme and styling
st.markdown("""
    <style>
    /* Set background colors */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #1E262E; }
    /* Style for headings and texts */
    .stApp, .stApp * { font-family: "Segoe UI", sans-serif; }
    /* Style buttons (all Streamlit buttons) */
    div.stButton > button {
        background-color: #E12D39; color: #FFFFFF; border-radius: 0.5rem;
        border: none; padding: 0.5rem 1rem; margin: 0.2rem 0 0.2rem 0;
    }
    /* Make sidebar buttons inline for quick tickers */
    [data-testid="stSidebar"] div.stButton > button {
        display: inline-block; width: auto; margin: 0.2rem 0.3rem 0.2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ----- Sidebar: Quick Tickers & Saved Tickers -----
st.sidebar.title("Quick Tickers 📈")
st.sidebar.subheader("Popular")
popular_tickers = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA", "META", "NFLX", "AMD", "INTC"]
# Display quick access buttons for popular tickers
for i, quick in enumerate(popular_tickers):
    if st.sidebar.button(quick, key=f"quick_{i}"):
        st.session_state["ticker"] = quick

# Section for user's saved tickers
st.sidebar.subheader("My Tickers ⭐")
# Initialize saved tickers list in session or load from file
if "saved_tickers" not in st.session_state:
    saved = []
    # Optionally load saved tickers from file if it exists
    try:
        with open("saved_tickers.txt", "r") as f:
            saved = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        saved = []
    st.session_state["saved_tickers"] = saved

# Button to add current ticker to saved list
current_ticker = st.session_state.get("ticker", "")
if current_ticker and current_ticker not in st.session_state["saved_tickers"]:
    if st.sidebar.button("➕ Add current ticker", key="add_ticker"):
        st.session_state["saved_tickers"].append(current_ticker)
        # Save updated list to file
        try:
            with open("saved_tickers.txt", "w") as f:
                for t in st.session_state["saved_tickers"]:
                    f.write(t + "\n")
        except Exception as e:
            print("Could not save tickers to file:", e)

# Show saved tickers as buttons for quick selection
for j, fav in enumerate(st.session_state["saved_tickers"]):
    if st.sidebar.button(fav, key=f"saved_{j}"):
        st.session_state["ticker"] = fav

# ----- Main Interface -----
# Two-column layout: left for 3D model, right for inputs and output
col1, col2 = st.columns([1, 3])
with col1:
    # Display 3D model (ensure you have the STL model file and streamlit-stl installed)
    try:
        from streamlit_stl import stl_from_file
        # Replace 'assets/model.stl' with the actual path to your 3D model file
        stl_ok = stl_from_file(file_path="assets/model.stl",
                               color="#FF9900", material="material",
                               auto_rotate=True, height=300)
        if not stl_ok:
            st.write("📌 3D model failed to load. Check file path or format.")
    except Exception as e:
        st.write("📌 3D model not available. (Install `streamlit-stl` and check model file)")

with col2:
    st.title("🚀 AI Stock News Sentiment Analyzer")
    # Ticker input and time range selection
    ticker = st.text_input("Enter Stock Ticker:", value=st.session_state.get("ticker", ""), key="ticker_input", placeholder="e.g. AAPL")
    time_options = ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 60 days"]
    time_choice = st.selectbox("Time Window:", options=time_options, index=1)  # default to "Last 7 days"
    # Determine date range from selection
    end_date = dt.datetime.now(dt.timezone.utc)
    if time_choice == "Last 24 hours":
        start_date = end_date - datetime.timedelta(days=1)
    elif time_choice == "Last 7 days":
        start_date = end_date - datetime.timedelta(days=7)
    elif time_choice == "Last 30 days":
        start_date = end_date - datetime.timedelta(days=30)
    elif time_choice == "Last 60 days":
        start_date = end_date - datetime.timedelta(days=60)
    else:
        start_date = end_date - datetime.timedelta(days=7)

    # Analyze button triggers data fetching and analysis
    if st.button("Analyze"):
        ticker = ticker.strip().upper()
        if not ticker:
            st.warning("Please enter a stock ticker to analyze.")
        else:
            # Fetch news headlines for the given ticker and date range
            start_dt = dt.datetime.combine(start_date, dt.time.min, dt.timezone.utc)
            end_dt   = dt.datetime.combine(end_date,   dt.time.max, dt.timezone.utc)

        headlines = get_headlines(ticker, start_dt, end_dt)




        if headlines:
                # Perform sentiment analysis on headlines
                sia = SentimentIntensityAnalyzer()
                sentiments = [sia.polarity_scores(head)["compound"] for head in headlines]
                # Classify each sentiment score
                pos_count = sum(1 for s in sentiments if s > 0.05)
                neg_count = sum(1 for s in sentiments if s < -0.05)
                neu_count = len(sentiments) - pos_count - neg_count

                st.write(f"**Total Headlines:** {len(headlines)}  |  **Positive:** {pos_count}  **Neutral:** {neu_count}  **Negative:** {neg_count}")

                # Chart 1: Sentiment distribution (bar chart)
                dist_fig = go.Figure(data=[
                    go.Bar(x=["Positive", "Neutral", "Negative"], y=[pos_count, neu_count, neg_count], marker_color=["#4caf50","#607d8b","#f44336"])
                ])
                dist_fig.update_layout(title_text="Sentiment Distribution of Headlines", height=400,
                                       xaxis_title="Sentiment", yaxis_title="Number of Headlines")
                st.plotly_chart(dist_fig, use_container_width=True)

                # Chart 2: Stock price vs average sentiment over time (if price data available)
                try:
                    import yfinance as yf
                    # Fetch historical daily prices for the selected period
                    df_price = yf.download(ticker, start=start_date.date(), end=(end_date + datetime.timedelta(days=1)).date(), progress=False)
                except Exception as e:
                    df_price = pd.DataFrame()  # fallback to empty if download fails
                if not df_price.empty:
                    # Prepare daily sentiment DataFrame
                    dates = []  # extract dates from NewsAPI results if available
                    # If get_headlines provided dates internally, we could use them. Otherwise, approximate dates as current date for all.
                    if hasattr(headlines[0], '__iter__') and not isinstance(headlines[0], str):
                        # In case get_headlines returns list of (headline, datetime)
                        dates = [d.date() for (_, d) in headlines]
                        # Convert headlines list to just titles
                        headlines = [t for (t, d) in headlines]
                    else:
                        # If only titles, assume all headlines are within range; assign current date for 24h or respective day for longer range
                        for _ in headlines:
                            dates.append(datetime.datetime.utcnow().date())
                    df_sent = pd.DataFrame({"date": dates, "sentiment": sentiments})
                    daily_sent = df_sent.groupby("date").mean(numeric_only=True)
                    # Align price data (ensure index is date)
                    price_df = df_price.copy()
                    price_df.index = pd.to_datetime(price_df.index).date
                    # Join price and sentiment on date
                    combo_df = pd.DataFrame({"Close": price_df["Close"]}).join(daily_sent, how="outer")
                    # Plot price and sentiment on dual-axis
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=list(combo_df.index), y=combo_df["Close"], name="Close Price", line=dict(color="#1f77b4"), yaxis="y1"))
                    fig.add_trace(go.Bar(x=list(combo_df.index), y=combo_df["sentiment"], name="Avg Sentiment", marker_color="#ff9900", opacity=0.7, yaxis="y2"))
                    fig.update_layout(title=f"{ticker} Price vs Sentiment Over Time", height=500,
                                      xaxis_title="Date",
                                      yaxis=dict(title="Stock Close Price (USD)", titlefont=dict(color="#1f77b4"), tickfont=dict(color="#1f77b4")),
                                      yaxis2=dict(title="Average Sentiment", titlefont=dict(color="#ff9900"), tickfont=dict(color="#ff9900"),
                                                  overlaying="y", side="right"))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Price data unavailable or failed to load for this period.")

                # Display headlines with sentiment scores (optional detail)
                st.subheader("Headlines and Sentiment Scores")
                for head, score in zip(headlines, sentiments):
                    # Use colored icons or text to indicate sentiment
                    if score > 0.05:
                        st.write(f":heavy_plus_sign: **{head}**  _(Positive)_")
                    elif score < -0.05:
                        st.write(f":heavy_minus_sign: **{head}**  _(Negative)_")
                    else:
                        st.write(f":heavy_minus_sign: **{head}**  _(Neutral)_")
        else:
                # No headlines found – provide feedback to user
                st.warning(f"No news headlines found for **{ticker}** in the selected time range.")
                st.info("Please check the ticker symbol or try a different time range.")
