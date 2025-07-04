import streamlit as st
from datetime import datetime, date, timedelta

# Importing our modules
from scraper import scrape_yahoo_headlines, scrape_marketwatch_headlines
from sentiment import load_sentiment_model, classify_headlines
from predictor import train_random_forest, predict_next_day
from utils import parse_relative_date

# Set Streamlit page configuration (optional)
st.set_page_config(page_title="AI Stock News Sentiment Analyzer", layout="wide")

st.title("AI Stock News Sentiment Analyzer")

# Sidebar or top inputs for user
ticker = st.text_input("Enter Stock Ticker:", value="AAPL")  # default to AAPL for convenience

# Date range input - default to last 7 days
default_end = date.today()
default_start = default_end - timedelta(days=7)
start_date, end_date = st.date_input("Select Date Range:", [default_start, default_end])

# If only one date is picked, treat it as both start and end
if isinstance(start_date, list) or isinstance(start_date, tuple):
    # Streamlit returns a list/tuple if range provided; unpack if so
    if len(start_date) == 2:
        start_date, end_date = start_date  # unpack tuple of dates
else:
    # If date_input returned a single date (in case of single-date mode), set end_date same as start
    end_date = start_date

# Button to trigger analysis
if st.button("Analyze"):
    # Validate inputs
    ticker = ticker.strip().upper()
    if not ticker:
        st.error("Please enter a stock ticker symbol.")
    else:
        # Inform the user that analysis is in progress
        with st.spinner(f"Scraping news for {ticker} and analyzing sentiment..."):
            # Scrape headlines from Yahoo Finance and MarketWatch
            yahoo_news = scrape_yahoo_headlines(ticker)
            mw_news = scrape_marketwatch_headlines(ticker)
            all_news = yahoo_news + mw_news

            # If no news found, show a warning
            if not all_news:
                st.warning("No news headlines found for the given ticker and date range.")
            else:
                # Parse relative dates to actual dates, filter by selected range
                filtered_news = []
                for head, time_str in all_news:
                    # Convert relative/absolute time string to date object
                    head_date = parse_relative_date(time_str)
                    if head_date is None:
                        continue  # skip if date couldn't be parsed
                    # Filter by selected date range (inclusive)
                    if start_date <= head_date <= end_date:
                        filtered_news.append((head, head_date))
                # If nothing remains after filtering
                if not filtered_news:
                    st.warning("No news headlines in the selected date range.")
                else:
                    # Separate headlines and their dates
                    headlines = [h for (h, d) in filtered_news]
                    dates = [d for (h, d) in filtered_news]

                    # Load or get the cached sentiment analysis model (FinBERT pipeline)
                    nlp_pipeline = load_sentiment_model()
                    # Classify all headlines
                    sentiments = classify_headlines(nlp_pipeline, headlines)

                    # Prepare data for sentiment distribution and daily aggregation
                    pos_count = sum(1 for s in sentiments if s == "positive")
                    neu_count = sum(1 for s in sentiments if s == "neutral")
                    neg_count = sum(1 for s in sentiments if s == "negative")

                    # Compute daily average sentiment score
                    # Map sentiment label to numeric value for averaging
                    label_to_score = {"positive": 1, "neutral": 0, "negative": -1}
                    daily_scores = {}  # dict of date -> list of scores
                    for (h, d), label in zip(filtered_news, sentiments):
                        score = label_to_score.get(label, 0)
                        daily_scores.setdefault(d, []).append(score)
                    # Average score per day
                    daily_avg = []
                    for d, scores in daily_scores.items():
                        avg_score = sum(scores) / len(scores)
                        daily_avg.append((d, avg_score))
                    # Sort by date
                    daily_avg.sort(key=lambda x: x[0])

                    # Fetch historical prices for the date range
                    # Use yfinance to get closing prices
                    import yfinance as yf
                    # Include end_date in data by adding one day to end (yfinance end is exclusive)
                    end_plus_one = end_date + timedelta(days=1)
                    ticker_obj = yf.Ticker(ticker)
                    try:
                        price_df = ticker_obj.history(start=start_date, end=end_plus_one)
                    except Exception as e:
                        price_df = None
                        st.error(f"Error fetching price data: {e}")

                    if price_df is None or price_df.empty:
                        st.warning("No price data available for the selected date range.")

                    # If price data is available, proceed
                    if price_df is not None and not price_df.empty:
                        # Ensure date is a column for merging (reset index)
                        price_df = price_df.reset_index()
                        price_df['Date'] = price_df['Date'].dt.date  # convert to date (without time)
                        price_df = price_df[['Date', 'Close']]

                        # Merge price with sentiment by date (left join on price dates)
                        import pandas as pd
                        sentiment_df = pd.DataFrame(daily_avg, columns=["Date", "AvgSentiment"])
                        merged_df = pd.merge(price_df, sentiment_df, on="Date", how="left")
                        # Fill NaN sentiment (if no news that day) with 0 (neutral)
                        merged_df['AvgSentiment'] = merged_df['AvgSentiment'].fillna(0.0)

                        # Train Random Forest on all but last day, predict last day
                        if len(merged_df) >= 2:  # need at least 2 days to train/predict
                            prediction = None
                            try:
                                model = train_random_forest(merged_df)
                                last_day = merged_df['Date'].max()
                                last_features = merged_df[merged_df['Date'] == last_day][['AvgSentiment']]
                                if not last_features.empty:
                                    pred_class = predict_next_day(model, last_features)
                                    prediction = "Up" if pred_class == 1 else "Down"
                            except Exception as e:
                                st.error(f"Model training/prediction error: {e}")
                                prediction = None
                        else:
                            prediction = None

                        # --- Display results ---
                        st.subheader("Sentiment Analysis Results")

                        col1, col2 = st.columns(2)
                        with col1:
                            # Sentiment distribution pie chart using Plotly
                            import plotly.express as px
                            dist_labels = ['Positive', 'Neutral', 'Negative']
                            dist_values = [pos_count, neu_count, neg_count]
                            fig_pie = px.pie(names=dist_labels, values=dist_values, title="Headline Sentiment Distribution")
                            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig_pie, use_container_width=True)
                        with col2:
                            # Daily average sentiment bar chart
                            if daily_avg:
                                dates_list = [d.strftime("%Y-%m-%d") for d, _ in daily_avg]
                                scores_list = [s for _, s in daily_avg]
                                fig_bar = px.bar(x=dates_list, y=scores_list, labels={"x": "Date", "y": "Average Sentiment"},
                                                 title="Daily Average Sentiment Score")
                                st.plotly_chart(fig_bar, use_container_width=True)
                            else:
                                st.write("No sentiment data to display in the selected range.")

                        # Price trend line chart
                        st.subheader("Stock Closing Price Trend")
                        fig_line = px.line(merged_df, x='Date', y='Close', title=f"{ticker} Closing Prices")
                        st.plotly_chart(fig_line, use_container_width=True)

                        # Display prediction
                        if prediction is not None:
                            st.subheader("Next-Day Movement Prediction")
                            st.markdown(f"Based on the data, the model predicts **{prediction}** for the next trading day after {merged_df['Date'].max()}.")
                        else:
                            st.write("Not enough data to train model for prediction.")
                    # end of price data available check
    # Spinner/with block ends

# End of app.py
