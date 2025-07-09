RhymeWatch
LLM powered stock sentiment analysis and price prediction platform

Overview
RhymeWatch analyzes financial news sentiment using advanced natural language processing to help investors make informed decisions. The platform combines real-time news data with machine learning models to predict short-term stock movements and provide investment recommendations.
Built with React for the frontend and FastAPI for the backend, 
Sentiment Analysis
Real-time analysis of financial news headlines using the FinBERT model specifically trained on financial text data.
Investment Recommendations
Automated buy, hold, or avoid recommendations based on aggregated sentiment scores from multiple news sources.
Price Prediction
Machine learning models predict next-day price movements using historical data and sentiment indicators.
Multi-Source Data
Integrates with NewsAPI, Finnhub, and Google RSS to ensure comprehensive news coverage.
Flexible Time Ranges
Analyze sentiment trends across different periods from one month to five years.
Modern Interface
Clean, intuitive design optimized for both desktop and mobile devices.
Technology Stack

Frontend

React 18 
CSS3 
Responsive design principles

Backend

FastAPI endpoints
Python 3.8+ with  computing libraries
REST architecture

Machine Learning

FinBERT for sentiment classification
Random Forest for price prediction
scikit-learn for model training

Data Sources

yfinance for historical stock data
NewsAPI for current headlines
Finnhub for company specific news
Google RSS as fallback source