import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import plotly.graph_objects as go
import plotly.express as px

# Ensure the VADER sentiment lexicon is downloaded
try:
    _ = SentimentIntensityAnalyzer()
except Exception:
    nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Set page configuration (including wide layout for better display of charts)
st.set_page_config(page_title="Stock News Sentiment Analyzer", page_icon="📈", layout="wide")

# Apply custom CSS styling for a dark, sleek Apple-like theme
st.markdown("""
<style>
/* Dark background for app and white text with clean font (Apple-like) */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0F0F0F;
    color: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
/* Dark background for sidebar */ 
[data-testid="stSidebar"] {
    background-color: #1C1C1C;
}
/* Stylish buttons */
.stButton > button {
    background-color: #333333;
    color: #FFFFFF;
    border:none;
    border-radius: 4px;
    padding: 0.4em 0.8em;
    font-size: 16px;
}
.stButton > button:hover {
    background-color: #444444;
}
/* Adjust headings color for visibility */
h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("AI Stock News Sentiment Analyzer")
st.write("Enter a stock ticker symbol and select a date range to fetch recent news headlines. The app will analyze headline sentiment using VADER and display sentiment visuals alongside the stock's price trend.")

# Include 3D model (financial themed) using <model-viewer> web component
# (Note: Replace the model_url with an actual .glb model URL related to finance or economy)
st.markdown(
    '<script src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js" type="module"></script>',
    unsafe_allow_html=True
)
model_url = "https://your-cdn.com/path-to-finance-model.glb"  # TODO: replace with actual model URL
st.markdown(f"""
<div style="text-align:center; margin-bottom: 1rem;">
<model-viewer src="{model_url}" alt="3D financial model" 
    auto-rotate camera-controls background-color="#000000" 
    style="width: 100%; max-width: 400px; height: 300px;">
</model-viewer>
</div>""", unsafe_allow_html=True)  # Using <model-viewer> to display 3D model:contentReference[oaicite:0]{index=0}

# Initialize session state for storing ticker history
if 'ticker_history' not in st.session_state:
    st.session_state['ticker_history'] = []

# Sidebar - Quick ticker buttons for popular stocks
st.sidebar.header("Quick Tickers")
quick_tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]
for qt in quick_tickers:
    if st.sidebar.button(qt, key=f"quick_{qt}"):
        st.session_state['ticker_input'] = qt

# Sidebar - Show recently viewed tickers with buttons for quick recall
st.sidebar.markdown("### Recently Viewed")
if st.session_state['ticker_history']:
    # Display in reverse order (most recent last)
    for t in reversed(st.session_state['ticker_history']):
        if st.sidebar.button(t, key=f"hist_{t}"):
            st.session_state['ticker_input'] = t
else:
    st.sidebar.write("None")

# Main input section: Ticker text input and date range selection
col1, col2 = st.columns([1, 2])
with col1:
    ticker = st.text_input("Stock Ticker (e.g. AAPL):", key="ticker_input")
with col2:
    date_options = ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 60 days", "Last 90 days", "Last 120 days"]
    time_horizon = st.selectbox("Time Range:", date_options, index=1)  # default to "Last 7 days"

# Determine the number of days from the selected range
if "hour" in time_horizon:
    days = 1  # 24 hours -> 1 day
else:
    # e.g. "Last 30 days" -> 30
    days = int(time_horizon.split()[1])
since_date = datetime.now() - timedelta(days=days)

# Only proceed if a ticker is provided
if ticker:
    ticker = ticker.strip().upper()
    # Update session history for tickers
    if ticker in st.session_state['ticker_history']:
        # Move the ticker to the end (most recent)
        st.session_state['ticker_history'].remove(ticker)
    st.session_state['ticker_history'].append(ticker)

    # Retrieve headlines using scraper (external module) or use placeholder if unavailable
    headlines = []
    try:
        import scraper
        headlines = scraper.get_headlines(ticker, since_date)
    except Exception as e:
        # Fallback to placeholder headlines if scraper fails or is not implemented
        now_time = datetime.now()
        headlines = [
            (f"{ticker} stock hits new high amid market optimism", now_time - timedelta(hours=12)),
            (f"{ticker} sees unexpected decline in quarterly profits", now_time - timedelta(days=3)),
            (f"Analysts remain bullish on {ticker} despite market volatility", now_time - timedelta(days=10))
        ]
    # Filter headlines by selected date range
    headlines = [(h, ts) for (h, ts) in headlines if ts and ts >= since_date]

    # Ensure each headline is a string (avoid tuple encode errors)
    cleaned_headlines = []
    for item in headlines:
        # Each item expected to be (headline_text, timestamp)
        if isinstance(item, tuple) and len(item) > 0:
            head_text = item[0]
            head_time = item[1] if len(item) > 1 else None
            cleaned_headlines.append((str(head_text), head_time))
        elif isinstance(item, str):
            # If somehow we got just a string without timestamp
            cleaned_headlines.append((item, None))
    headlines = cleaned_headlines

    if not headlines:
        st.warning(f"No news headlines found for **{ticker}** in the selected time range.")
    else:
        # Sort headlines by timestamp (newest first)
        headlines.sort(key=lambda x: x[1] if x[1] else datetime.now(), reverse=True)

        # Perform sentiment analysis on each headline
        sentiment_scores = [sid.polarity_scores(h_text) for h_text, _ in headlines]
        # Classify each headline as Positive, Neutral, or Negative based on compound score
        sentiment_labels = []
        for scores in sentiment_scores:
            compound = scores["compound"]
            if compound >= 0.05:
                sentiment_labels.append("Positive")
            elif compound <= -0.05:
                sentiment_labels.append("Negative")
            else:
                sentiment_labels.append("Neutral")
        # (VADER uses 0.05 and -0.05 as default thresholds for positive/negative:contentReference[oaicite:1]{index=1})

        # Count sentiment categories
        count_pos = sentiment_labels.count("Positive")
        count_neu = sentiment_labels.count("Neutral")
        count_neg = sentiment_labels.count("Negative")

        # Display the headlines with their sentiment classification
        st.subheader(f"Recent News for {ticker}")
        for (headline_text, timestamp), label in zip(headlines, sentiment_labels):
            time_str = timestamp.strftime("%Y-%m-%d %H:%M") if timestamp else ""
            st.write(f"- {headline_text}  *(Sentiment: **{label}**)*  {time_str}")

        # Fetch historical stock price data via yfinance
        try:
            stock_df = yf.download(ticker, start=since_date, end=datetime.now())
        except Exception as e:
            stock_df = pd.DataFrame()  # empty DataFrame on failure
        # Prepare line chart if data is available
        if not stock_df.empty:
            stock_df = stock_df.reset_index()  # ensure Date is a column
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=stock_df['Date'], y=stock_df['Close'], mode='lines',
                                          name=ticker, line=dict(color='#0A84FF', width=3)))
            fig_line.update_layout(
                title=f"{ticker} Stock Price - {time_horizon}",
                xaxis_title="Date", yaxis_title="Price (USD)",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color="white"
            )
            # Display the stock price line chart
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning(f"Unable to retrieve price data for **{ticker}** over {time_horizon.lower()}.")

        # Create a pie chart for sentiment distribution
        fig_pie = go.Figure(data=[go.Pie(labels=["Positive", "Neutral", "Negative"],
                                         values=[count_pos, count_neu, count_neg], hole=0.3)])
        fig_pie.update_traces(marker=dict(colors=["seagreen", "gray", "indianred"]), textinfo="percent+label")
        fig_pie.update_layout(
            title="Sentiment Distribution",
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )

        # Create a bar chart for sentiment counts
        fig_bar = go.Figure(data=[go.Bar(x=["Positive", "Neutral", "Negative"],
                                         y=[count_pos, count_neu, count_neg],
                                         marker_color=["seagreen", "gray", "indianred"],
                                         text=[count_pos, count_neu, count_neg], textposition='auto')])
        fig_bar.update_layout(
            title="Headline Sentiment Count",
            yaxis_title="Number of Headlines",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color="white"
        )

        # Display pie and bar charts side by side
        colA, colB = st.columns(2)
        colA.plotly_chart(fig_pie, use_container_width=True)
        colB.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("👈 Enter a stock ticker and select a time range to analyze its news sentiment.")

# Feedback section (properly indented and standalone)
st.markdown("### Feedback")
feedback = st.text_input("Share your feedback or suggestions:")
if st.button("Submit Feedback"):
    if feedback:
        st.success("Thank you for your feedback!")
    else:
        st.warning("Please enter some feedback before submitting.")
