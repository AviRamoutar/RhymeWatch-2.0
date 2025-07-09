from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, timedelta
import yfinance as yf
import numpy as np
import pandas as pd
from typing import Optional

from scraper import get_headlines
from sentiment import load_sentiment_model, classify_headlines
from predictor import train_random_forest, predict_next_day

app = FastAPI(title="RhymeWatch API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sentiment_model = None

def get_sentiment_model():
    global _sentiment_model
    if _sentiment_model is None:
        print("Loading sentiment model...")
        _sentiment_model = load_sentiment_model()
    return _sentiment_model

@app.get("/")
def root():
    return {"message": "RhymeWatch API is running!", "version": "1.0.0"}

@app.get("/analyze")
def analyze(
        symbol: str = Query(..., description="Stock symbol to analyze"),
        days: int = Query(60, description="Number of days to look back", ge=1, le=365)
):
    try:
        symbol = symbol.upper().strip()

        print(f"Fetching headlines for {symbol}...")
        headlines_with_dates = get_headlines(symbol, days=days)

        if not headlines_with_dates:
            raise HTTPException(
                status_code=404,
                detail=f"No news found for {symbol}. Try a different stock symbol."
            )

        headlines = [title for title, _ in headlines_with_dates]
        dates = [dt.isoformat() for _, dt in headlines_with_dates]

        print(f"Analyzing sentiment for {len(headlines)} headlines...")
        nlp = get_sentiment_model()
        sentiments = classify_headlines(nlp, headlines)

        sentiment_counts = {
            "positive": sentiments.count("positive"),
            "neutral": sentiments.count("neutral"),
            "negative": sentiments.count("negative"),
        }

        print(f"Fetching price data for {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d")

            if df.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No price data found for {symbol}. Please check the symbol."
                )

            price_history = df["Close"].tolist()
            volume_history = df["Volume"].tolist()

        except Exception as e:
            print(f"Error fetching price data: {e}")
            price_history = []
            volume_history = []

        next_day_prediction = None
        if price_history and sentiments:
            try:
                sentiment_scores = [
                    {"positive": 1, "neutral": 0, "negative": -1}[sentiment]
                    for sentiment in sentiments
                ]
                avg_sentiment = np.mean(sentiment_scores)

                if len(price_history) > 1:
                    price_changes = [
                        1 if price_history[i] > price_history[i-1] else 0
                        for i in range(1, len(price_history))
                    ]

                    if len(price_changes) >= 10:
                        features = pd.DataFrame({
                            'sentiment': [avg_sentiment] * len(price_changes)
                        })
                        targets = np.array(price_changes)

                        model = train_random_forest(features, targets)
                        next_features = pd.DataFrame({'sentiment': [avg_sentiment]})
                        next_day_prediction = predict_next_day(model, next_features)

            except Exception as e:
                print(f"Error in prediction: {e}")
                next_day_prediction = None

        news_data = []
        for i, headline in enumerate(headlines):
            news_data.append({
                "headline": headline,
                "date": dates[i] if i < len(dates) else "",
                "sentiment": sentiments[i] if i < len(sentiments) else "neutral"
            })

        return {
            "symbol": symbol,
            "days_analyzed": days,
            "news": news_data,
            "sentimentCounts": sentiment_counts,
            "priceHistory": price_history,
            "volumeHistory": volume_history,
            "nextDayUp": next_day_prediction,
            "total_headlines": len(headlines)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "RhymeWatch API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)