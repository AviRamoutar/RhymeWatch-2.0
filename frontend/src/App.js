import React, { useState, useEffect } from 'react';
import './App.css';
import { DEFAULT_TICKERS, loadStockTickers } from './stockTickers';

// Stock Sidebar Component
const StockSidebar = ({ onSelectStock, selectedStock }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [allTickers, setAllTickers] = useState(DEFAULT_TICKERS);
    const [filteredStocks, setFilteredStocks] = useState(DEFAULT_TICKERS);

    // Load tickers on mount
    useEffect(() => {
        loadStockTickers().then(tickers => {
            setAllTickers(tickers);
            setFilteredStocks(tickers);
        });
    }, []);

    // Filter stocks when search term changes
    useEffect(() => {
        const filtered = allTickers.filter(stock =>
            stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
            stock.name.toLowerCase().includes(searchTerm.toLowerCase())
        );
        setFilteredStocks(filtered);
    }, [searchTerm, allTickers]);

    return (
        <div className="stock-sidebar">
            <h3>Stock Universe</h3>
            <input
                type="text"
                className="stock-search-input"
                placeholder="Search stocks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
            />
            <div className="stock-list">
                {filteredStocks.map((stock) => (
                    <div
                        key={stock.symbol}
                        className={`stock-list-item ${selectedStock === stock.symbol ? 'selected' : ''}`}
                        onClick={() => onSelectStock(stock.symbol)}
                    >
                        <div>
                            <div className="stock-symbol">{stock.symbol}</div>
                            <div className="stock-name">{stock.name}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

function App() {
    const [stockSymbol, setStockSymbol] = useState('');
    const [timeRange, setTimeRange] = useState('6 Months');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    const handleStockSelect = (symbol) => {
        setStockSymbol(symbol);
    };

    const analyzeStock = async () => {
        if (!stockSymbol) return;

        setLoading(true);
        setError(null);
        setResults(null);

        try {
            // Convert time range to days
            const daysMap = {
                '1 Week': 7,
                '1 Month': 30,
                '3 Months': 90,
                '6 Months': 180,
                '1 Year': 365
            };
            const days = daysMap[timeRange] || 60;

            // Use your Render backend URL when deployed
            const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/analyze?symbol=${stockSymbol}&days=${days}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Transform the data to match the expected format
            const transformedData = {
                sentiment_summary: {
                    overall_sentiment: data.sentimentCounts.positive > data.sentimentCounts.negative ? 'POSITIVE' :
                        data.sentimentCounts.negative > data.sentimentCounts.positive ? 'NEGATIVE' : 'NEUTRAL',
                    average_score: (data.sentimentCounts.positive - data.sentimentCounts.negative) / data.total_headlines,
                    positive_count: data.sentimentCounts.positive,
                    neutral_count: data.sentimentCounts.neutral,
                    negative_count: data.sentimentCounts.negative
                },
                prediction: {
                    current_price: data.priceHistory[data.priceHistory.length - 1] || 0,
                    predicted_price: data.priceHistory[data.priceHistory.length - 1] * (data.nextDayUp ? 1.02 : 0.98),
                    predicted_change: data.nextDayUp ? 2.0 : -2.0,
                    confidence: data.nextDayUp !== null ? 0.75 : 0.5
                },
                stock_info: {
                    symbol: data.symbol,
                    market_cap: 0, // Your backend doesn't provide this
                    volume: data.volumeHistory[data.volumeHistory.length - 1] || 0,
                    year_high: Math.max(...data.priceHistory),
                    year_low: Math.min(...data.priceHistory)
                },
                news: data.news.map(item => ({
                    title: item.headline,
                    summary: item.headline.substring(0, 150) + '...',
                    sentiment: item.sentiment.toUpperCase(),
                    source: 'News',
                    published_at: item.date
                }))
            };

            setResults(transformedData);
        } catch (err) {
            console.error('Error:', err);
            setError(err.message || 'Failed to analyze stock. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app-container">
            <StockSidebar
                onSelectStock={handleStockSelect}
                selectedStock={stockSymbol}
            />

            <div className="main-content">
                <div className="hero-section">
                    <h1 className="app-title">
                        <span className="gradient-text">Sentiment</span>
                        <br />
                        Before It Moves
                    </h1>
                    <p className="app-subtitle">
                        Advanced AI sentiment analysis meets real-time market intelligence.
                        Make informed investment decisions with machine learning predictions.
                    </p>
                </div>

                <div className="analysis-card">
                    <div className="input-group">
                        <div className="input-section">
                            <label className="input-label">STOCK SYMBOL</label>
                            <input
                                type="text"
                                className="stock-input"
                                placeholder="AAPL, TSLA, MSFT..."
                                value={stockSymbol}
                                onChange={(e) => setStockSymbol(e.target.value.toUpperCase())}
                            />
                        </div>

                        <div className="input-section">
                            <label className="input-label">TIME RANGE</label>
                            <select
                                className="time-select"
                                value={timeRange}
                                onChange={(e) => setTimeRange(e.target.value)}
                            >
                                <option value="1 Week">1 Week</option>
                                <option value="1 Month">1 Month</option>
                                <option value="3 Months">3 Months</option>
                                <option value="6 Months">6 Months</option>
                                <option value="1 Year">1 Year</option>
                            </select>
                        </div>

                        <button
                            className="analyze-button"
                            onClick={analyzeStock}
                            disabled={loading || !stockSymbol}
                        >
                            {loading ? 'Analyzing...' : 'Analyze Sentiment'}
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="error-message">
                        <p>⚠️ {error}</p>
                    </div>
                )}

                {results && (
                    <div className="results-container">
                        <div className="results-grid">
                            <div className="result-card sentiment-card">
                                <h3>Sentiment Analysis</h3>
                                <div className={`sentiment-score ${results.sentiment_summary.overall_sentiment.toLowerCase()}`}>
                                    <span className="sentiment-label">{results.sentiment_summary.overall_sentiment}</span>
                                    <span className="sentiment-value">{(results.sentiment_summary.average_score * 100).toFixed(1)}%</span>
                                </div>
                                <div className="sentiment-breakdown">
                                    <div className="sentiment-item">
                                        <span className="sentiment-type">Positive</span>
                                        <span className="sentiment-count">{results.sentiment_summary.positive_count}</span>
                                    </div>
                                    <div className="sentiment-item">
                                        <span className="sentiment-type">Neutral</span>
                                        <span className="sentiment-count">{results.sentiment_summary.neutral_count}</span>
                                    </div>
                                    <div className="sentiment-item">
                                        <span className="sentiment-type">Negative</span>
                                        <span className="sentiment-count">{results.sentiment_summary.negative_count}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="result-card prediction-card">
                                <h3>Price Prediction</h3>
                                <div className="prediction-content">
                                    <div className="current-price">
                                        <span className="price-label">Current Price</span>
                                        <span className="price-value">${results.prediction.current_price.toFixed(2)}</span>
                                    </div>
                                    <div className="predicted-price">
                                        <span className="price-label">Predicted (30 days)</span>
                                        <span className="price-value">${results.prediction.predicted_price.toFixed(2)}</span>
                                    </div>
                                    <div className={`price-change ${results.prediction.predicted_change >= 0 ? 'positive' : 'negative'}`}>
                                        <span className="change-label">Expected Change</span>
                                        <span className="change-value">
                      {results.prediction.predicted_change >= 0 ? '+' : ''}{results.prediction.predicted_change.toFixed(2)}%
                    </span>
                                    </div>
                                    <div className="confidence">
                                        <span className="confidence-label">Confidence</span>
                                        <span className="confidence-value">{(results.prediction.confidence * 100).toFixed(1)}%</span>
                                    </div>
                                </div>
                            </div>

                            <div className="result-card stock-info-card">
                                <h3>Stock Information</h3>
                                <div className="stock-details">
                                    <div className="info-item">
                                        <span className="info-label">Symbol</span>
                                        <span className="info-value">{results.stock_info.symbol}</span>
                                    </div>
                                    <div className="info-item">
                                        <span className="info-label">Market Cap</span>
                                        <span className="info-value">${(results.stock_info.market_cap / 1e9).toFixed(2)}B</span>
                                    </div>
                                    <div className="info-item">
                                        <span className="info-label">Volume</span>
                                        <span className="info-value">{(results.stock_info.volume / 1e6).toFixed(2)}M</span>
                                    </div>
                                    <div className="info-item">
                                        <span className="info-label">52W Range</span>
                                        <span className="info-value">
                      ${results.stock_info.year_low.toFixed(2)} - ${results.stock_info.year_high.toFixed(2)}
                    </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="news-section">
                            <h3>Recent News & Sentiment</h3>
                            <div className="news-grid">
                                {results.news.map((article, index) => (
                                    <div key={index} className="news-item">
                                        <div className="news-header">
                                            <h4>{article.title}</h4>
                                            <span className={`news-sentiment ${article.sentiment.toLowerCase()}`}>
                        {article.sentiment}
                      </span>
                                        </div>
                                        <p className="news-summary">{article.summary}</p>
                                        <div className="news-meta">
                                            <span className="news-source">{article.source}</span>
                                            <span className="news-date">{new Date(article.published_at).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;