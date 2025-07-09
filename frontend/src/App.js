import React, { useState } from 'react';
import './App.css';

function App() {
    const [ticker, setTicker] = useState('');
    const [selectedRange, setSelectedRange] = useState('6M');
    const [analysisData, setAnalysisData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const convertRangeToDays = (range) => {
        const rangeMap = {
            '1M': 30,
            '3M': 90,
            '6M': 180,
            '1Y': 365,
            '5Y': 1825
        };
        return rangeMap[range] || 180;
    };

    const fetchAnalysisFromBackend = async (stockSymbol, range) => {
        setLoading(true);
        setError('');
        setAnalysisData(null);

        try {
            const days = convertRangeToDays(range);
            const response = await fetch(`http://localhost:8000/analyze?symbol=${stockSymbol}&days=${days}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            setAnalysisData(data);
        } catch (err) {
            console.error('Analysis request failed:', err);
            setError(err.message || 'Failed to fetch analysis');
        } finally {
            setLoading(false);
        }
    };

    const handleAnalyzeClick = () => {
        if (ticker.trim()) {
            fetchAnalysisFromBackend(ticker.trim().toUpperCase(), selectedRange);
        }
    };

    const handleRangeSelection = (newRange) => {
        setSelectedRange(newRange);
        if (analysisData && ticker.trim()) {
            fetchAnalysisFromBackend(ticker.trim().toUpperCase(), newRange);
        }
    };

    const calculateRecommendation = () => {
        if (!analysisData?.sentimentCounts) return null;

        const { positive = 0, negative = 0, neutral = 0 } = analysisData.sentimentCounts;
        const total = positive + negative + neutral;

        if (total === 0) return null;

        if (positive > negative) {
            return { text: 'Buy', color: '#22c55e' };
        } else if (negative > positive) {
            return { text: 'Avoid', color: '#ef4444' };
        } else {
            return { text: 'Hold', color: '#6b7280' };
        }
    };

    const recommendation = calculateRecommendation();

    return (
        <div className="App">
            <header className="app-header">
                <h1>🎵 RhymeWatch</h1>
                <p>AI-Powered Stock Sentiment Analysis</p>
            </header>

            <div className="controls">
                <div className="input-group">
                    <label htmlFor="ticker-input">Stock Symbol:</label>
                    <input
                        id="ticker-input"
                        type="text"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        placeholder="Enter stock symbol (e.g., AAPL)"
                        onKeyPress={(e) => e.key === 'Enter' && handleAnalyzeClick()}
                    />
                    <button onClick={handleAnalyzeClick} disabled={loading || !ticker.trim()}>
                        {loading ? 'Analyzing...' : 'Analyze'}
                    </button>
                </div>
            </div>

            {error && (
                <div className="error-message">
                    <p>❌ Error: {error}</p>
                </div>
            )}

            {analysisData && (
                <div className="results">
                    <h2>Analysis Results for {ticker}</h2>

                    <div className="sentiment-summary">
                        <h3>Sentiment Distribution</h3>
                        <div className="sentiment-counts">
                            <div className="sentiment-item positive">
                                <span className="label">Positive:</span>
                                <span className="count">{analysisData.sentimentCounts.positive}</span>
                            </div>
                            <div className="sentiment-item neutral">
                                <span className="label">Neutral:</span>
                                <span className="count">{analysisData.sentimentCounts.neutral}</span>
                            </div>
                            <div className="sentiment-item negative">
                                <span className="label">Negative:</span>
                                <span className="count">{analysisData.sentimentCounts.negative}</span>
                            </div>
                        </div>
                    </div>

                    {recommendation && (
                        <div className="recommendation">
                            <h3>Investment Recommendation</h3>
                            <div className="recommendation-badge" style={{ color: recommendation.color }}>
                                {recommendation.text}
                            </div>
                        </div>
                    )}

                    {analysisData.nextDayUp !== null && (
                        <div className="prediction">
                            <h3>Next Day Prediction</h3>
                            <div className={`prediction-badge ${analysisData.nextDayUp ? 'up' : 'down'}`}>
                                {analysisData.nextDayUp ? '📈 Up' : '📉 Down'}
                            </div>
                        </div>
                    )}

                    <div className="range-selector">
                        <label>Time Range: </label>
                        <select value={selectedRange} onChange={(e) => handleRangeSelection(e.target.value)}>
                            <option value="1M">1 Month</option>
                            <option value="3M">3 Months</option>
                            <option value="6M">6 Months</option>
                            <option value="1Y">1 Year</option>
                            <option value="5Y">5 Years</option>
                        </select>
                    </div>

                    {analysisData.news && analysisData.news.length > 0 && (
                        <div className="news-section">
                            <h3>Recent News Headlines ({analysisData.news.length})</h3>
                            <div className="news-list">
                                {analysisData.news.slice(0, 10).map((item, index) => (
                                    <div key={index} className={`news-item ${item.sentiment}`}>
                                        <div className="news-headline">{item.headline}</div>
                                        <div className="news-meta">
                                            <span className="news-date">{item.date}</span>
                                            <span className={`news-sentiment ${item.sentiment}`}>
                                                {item.sentiment}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default App;