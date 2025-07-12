RhymeWatch LLM "powered" stock sentiment analysis and price prediction platform. Just this repo for now going live soon!!!

RhymeWatch is a full stack application that analyzes stock sentiment using AI and predicts price movements. The React frontend communicates with a FastAPI backend that ethically scrapes financial news, analyzes sentiment with FinBERT model to make predictions.

ML tools (Pretrained) FinBERT for sentiment classification Random Forest for price prediction scikit-learn for model training

FILE STRUCTURE

FRONTEND (React 18, CSS3 , Responsive design principles)
App.js - Main React component handling user interface, stock input, API calls, and results display

App.css - Styling for the entire application with dark theme, responsive design, and component layouts

index.js - React entry point that mounts the App component to the DOM

index.css - Global CSS styles for body, fonts, and base styling

package.json - Lists React dependencies and build scripts needed for the frontend

package-lock.json - Records exact versions of installed packages for consistent deployments (Honeslty for my own cloning/pulling ease across devices)

BACKEND (FastAPI endpoints, Python 3.8 or up, REST architecture)
app.py - FastAPI server with API endpoints, CORS configuration, and main analysis logic coordination

scraper.py - Fetches financial news headlines from NewsAPI, Finnhub, and Google RSS sources

sentiment.py - Loads FinBERT model and classifies headlines as positive, neutral, or negative

predictor.py - Trains Random Forest model and predicts next-day stock price movement direction

utils.py - Shared utility functions for data processing and helper operations

CONFIG
.env - Stores API keys for NewsAPI and Finnhub services securely

.gitignore - Excludes sensitive files and large dependencies from version control

requirements.txt - Lists Python packages needed for backend functionality

DATA SOURCES (Adding more next Update)
yahoofinance for historical stock data NewsAPI for current headlines Finnhub for company specific news Google RSS as fallback source