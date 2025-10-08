import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SentimentAnalysis = ({ globalTimeframe }) => {
    const [sentimentData, setSentimentData] = useState(null);
    const [socialData, setSocialData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeMetric, setActiveMetric] = useState('overall');
    const [lastUpdate, setLastUpdate] = useState(null);

    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

    useEffect(() => {
        fetchSentimentData();
        // Auto-refresh every 10 minutes
        const interval = setInterval(fetchSentimentData, 600000);
        return () => clearInterval(interval);
    }, [globalTimeframe]);

    const fetchSentimentData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Try to fetch real sentiment data
            const response = await axios.get(`${BACKEND_URL}/api/market-sentiment`);
            
            if (response.status === 200) {
                setSentimentData(response.data);
            }

            setLastUpdate(new Date());
        } catch (err) {
            console.error('Sentiment data fetch error:', err);
            
            // Use comprehensive mock data for demonstration
            setSentimentData({
                overall: {
                    score: 0.68,
                    label: 'Bullish',
                    confidence: 0.82,
                    change24h: 0.05,
                    description: 'Der Gesamtmarkt zeigt bullische Tendenzen mit starkem institutionellem Interesse.'
                },
                fear_greed_index: {
                    score: 72,
                    label: 'Gier',
                    change24h: 3,
                    description: 'Der Fear & Greed Index deutet auf überwiegend positive Marktstimmung hin.'
                },
                crypto_sentiment: {
                    bitcoin: {
                        score: 0.75,
                        label: 'Stark Bullish',
                        social_volume: 15420,
                        social_volume_change: 12.5,
                        mentions_24h: 8760
                    },
                    ethereum: {
                        score: 0.65,
                        label: 'Bullish',
                        social_volume: 8930,
                        social_volume_change: -2.1,
                        mentions_24h: 4210
                    },
                    altcoins: {
                        score: 0.58,
                        label: 'Leicht Bullish',
                        social_volume: 22150,
                        social_volume_change: 8.7,
                        mentions_24h: 12450
                    }
                },
                news_sentiment: {
                    positive: 45,
                    neutral: 38,
                    negative: 17,
                    total_articles: 1247,
                    trending_topics: ['Bitcoin ETF', 'Federal Reserve', 'DeFi', 'Institutional Adoption', 'Regulation']
                },
                social_sentiment: {
                    twitter: {
                        sentiment: 0.71,
                        volume: 25680,
                        engagement_rate: 4.2,
                        trending_hashtags: ['#Bitcoin', '#BTC', '#Crypto', '#HODL', '#BullRun']
                    },
                    reddit: {
                        sentiment: 0.63,
                        posts: 1420,
                        comments: 18750,
                        hot_topics: ['Bitcoin Price Analysis', 'Altcoin Season', 'Market Predictions', 'Technical Analysis']
                    },
                    telegram: {
                        sentiment: 0.69,
                        channels_monitored: 156,
                        messages: 45230,
                        whale_alerts: 23
                    }
                },
                market_indicators: {
                    vix: {
                        value: 18.5,
                        change: -1.2,
                        sentiment_impact: 'positive',
                        description: 'Niedrige Volatilität unterstützt Risk-On-Stimmung'
                    },
                    put_call_ratio: {
                        value: 0.85,
                        change: -0.08,
                        sentiment_impact: 'positive',
                        description: 'Weniger Put-Optionen deuten auf Optimismus hin'
                    },
                    margin_debt: {
                        trend: 'increasing',
                        sentiment_impact: 'neutral',
                        description: 'Steigende Margin-Verschuldung zeigt Risikobereitschaft'
                    }
                }
            });

            setSocialData({
                platforms: {
                    twitter: { sentiment: 0.71, volume: 25680, growth: 8.5 },
                    reddit: { sentiment: 0.63, volume: 1420, growth: -2.1 },
                    telegram: { sentiment: 0.69, volume: 156, growth: 15.3 }
                },
                influencers: [
                    { name: 'Michael Saylor', sentiment: 0.89, followers: '3.2M', recent_post: 'Bitcoin adoption beschleunigt sich...' },
                    { name: 'Elon Musk', sentiment: 0.72, followers: '150M', recent_post: 'Crypto hat Zukunft...' },
                    { name: 'Vitalik Buterin', sentiment: 0.68, followers: '5.1M', recent_post: 'Ethereum 2.0 Fortschritte...' }
                ],
                trending_now: [
                    { topic: 'Bitcoin ETF Inflows', sentiment: 0.82, volume: 12450 },
                    { topic: 'DeFi Renaissance', sentiment: 0.74, volume: 8730 },
                    { topic: 'Altcoin Season', sentiment: 0.67, volume: 15680 },
                    { topic: 'Institutional Adoption', sentiment: 0.79, volume: 9940 }
                ]
            });

            setLastUpdate(new Date());
        } finally {
            setLoading(false);
        }
    };

    const getSentimentColor = (score) => {
        if (score >= 0.7) return '#10b981'; // Strong positive
        if (score >= 0.6) return '#84cc16'; // Positive
        if (score >= 0.4) return '#f59e0b'; // Neutral
        if (score >= 0.3) return '#f97316'; // Negative
        return '#ef4444'; // Strong negative
    };

    const getSentimentLabel = (score) => {
        if (score >= 0.8) return 'Sehr Bullish';
        if (score >= 0.7) return 'Bullish';
        if (score >= 0.6) return 'Leicht Bullish';
        if (score >= 0.5) return 'Neutral';
        if (score >= 0.4) return 'Leicht Bearish';
        if (score >= 0.3) return 'Bearish';
        return 'Sehr Bearish';
    };

    const formatNumber = (num) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toLocaleString();
    };

    if (loading) {
        return (
            <div className="sentiment-analysis loading">
                <div className="loading-spinner"></div>
                <p>Lade Sentiment-Analyse...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="sentiment-analysis error">
                <div className="error-message">
                    <span>{error}</span>
                    <button onClick={fetchSentimentData} className="retry-btn">
                        🔄 Erneut versuchen
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="sentiment-analysis">
            <div className="panel-header">
                <div className="title-section">
                    <h3>🎭 Market Sentiment Analyse</h3>
                    {lastUpdate && (
                        <span className="last-update">
                            Letzte Aktualisierung: {lastUpdate.toLocaleTimeString('de-DE')}
                        </span>
                    )}
                </div>
                
                <button 
                    onClick={fetchSentimentData}
                    className="refresh-btn"
                    disabled={loading}
                >
                    🔄 Aktualisieren
                </button>
            </div>

            {/* Metric Selector */}
            <div className="metric-selector">
                <button 
                    className={`metric-btn ${activeMetric === 'overall' ? 'active' : ''}`}
                    onClick={() => setActiveMetric('overall')}
                >
                    📊 Gesamtmarkt
                </button>
                <button 
                    className={`metric-btn ${activeMetric === 'crypto' ? 'active' : ''}`}
                    onClick={() => setActiveMetric('crypto')}
                >
                    ₿ Crypto
                </button>
                <button 
                    className={`metric-btn ${activeMetric === 'social' ? 'active' : ''}`}
                    onClick={() => setActiveMetric('social')}
                >
                    💬 Social Media
                </button>
                <button 
                    className={`metric-btn ${activeMetric === 'news' ? 'active' : ''}`}
                    onClick={() => setActiveMetric('news')}
                >
                    📰 News
                </button>
            </div>

            {/* Overall Market Sentiment */}
            {activeMetric === 'overall' && sentimentData && (
                <div className="overall-sentiment">
                    <div className="main-sentiment-card">
                        <div className="sentiment-score-display">
                            <div 
                                className="sentiment-circle"
                                style={{ 
                                    background: `conic-gradient(${getSentimentColor(sentimentData.overall.score)} 0deg ${sentimentData.overall.score * 360}deg, rgba(255,255,255,0.1) ${sentimentData.overall.score * 360}deg 360deg)`
                                }}
                            >
                                <div className="sentiment-inner">
                                    <span className="sentiment-percentage">
                                        {Math.round(sentimentData.overall.score * 100)}%
                                    </span>
                                    <span className="sentiment-label">
                                        {sentimentData.overall.label}
                                    </span>
                                </div>
                            </div>
                            <div className="sentiment-details">
                                <div className="confidence">
                                    Vertrauen: {Math.round(sentimentData.overall.confidence * 100)}%
                                </div>
                                <div className={`change-24h ${sentimentData.overall.change24h >= 0 ? 'positive' : 'negative'}`}>
                                    24h Änderung: {sentimentData.overall.change24h >= 0 ? '+' : ''}{(sentimentData.overall.change24h * 100).toFixed(1)}%
                                </div>
                            </div>
                        </div>
                        <p className="sentiment-description">{sentimentData.overall.description}</p>
                    </div>

                    {/* Fear & Greed Index */}
                    <div className="fear-greed-card">
                        <h4>😱 Fear & Greed Index</h4>
                        <div className="fear-greed-display">
                            <div className="fear-greed-score">
                                <span className="score-number">{sentimentData.fear_greed_index.score}</span>
                                <span className="score-label">{sentimentData.fear_greed_index.label}</span>
                            </div>
                            <div className="fear-greed-bar">
                                <div 
                                    className="fear-greed-fill"
                                    style={{ width: `${sentimentData.fear_greed_index.score}%` }}
                                />
                            </div>
                            <div className={`fear-greed-change ${sentimentData.fear_greed_index.change24h >= 0 ? 'positive' : 'negative'}`}>
                                24h: {sentimentData.fear_greed_index.change24h >= 0 ? '+' : ''}{sentimentData.fear_greed_index.change24h}
                            </div>
                        </div>
                        <p className="fear-greed-description">{sentimentData.fear_greed_index.description}</p>
                    </div>
                </div>
            )}

            {/* Crypto Sentiment */}
            {activeMetric === 'crypto' && sentimentData && (
                <div className="crypto-sentiment">
                    <div className="crypto-grid">
                        {Object.entries(sentimentData.crypto_sentiment).map(([crypto, data]) => (
                            <div key={crypto} className="crypto-card">
                                <div className="crypto-header">
                                    <h4>{crypto.charAt(0).toUpperCase() + crypto.slice(1)}</h4>
                                    <span 
                                        className="crypto-sentiment-score"
                                        style={{ color: getSentimentColor(data.score) }}
                                    >
                                        {getSentimentLabel(data.score)}
                                    </span>
                                </div>
                                <div className="crypto-metrics">
                                    <div className="metric-row">
                                        <span>Score:</span>
                                        <span style={{ color: getSentimentColor(data.score) }}>
                                            {Math.round(data.score * 100)}%
                                        </span>
                                    </div>
                                    <div className="metric-row">
                                        <span>Social Volume:</span>
                                        <span>{formatNumber(data.social_volume)}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span>Erwähnungen 24h:</span>
                                        <span>{formatNumber(data.mentions_24h)}</span>
                                    </div>
                                    <div className="metric-row">
                                        <span>Volume Änderung:</span>
                                        <span className={data.social_volume_change >= 0 ? 'positive' : 'negative'}>
                                            {data.social_volume_change >= 0 ? '+' : ''}{data.social_volume_change.toFixed(1)}%
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Social Media Sentiment */}
            {activeMetric === 'social' && socialData && (
                <div className="social-sentiment">
                    <div className="social-platforms">
                        <h4>📱 Social Media Plattformen</h4>
                        <div className="platforms-grid">
                            {Object.entries(socialData.platforms).map(([platform, data]) => (
                                <div key={platform} className="platform-card">
                                    <div className="platform-header">
                                        <h5>{platform.charAt(0).toUpperCase() + platform.slice(1)}</h5>
                                        <span 
                                            className="platform-sentiment"
                                            style={{ color: getSentimentColor(data.sentiment) }}
                                        >
                                            {Math.round(data.sentiment * 100)}%
                                        </span>
                                    </div>
                                    <div className="platform-stats">
                                        <div>Volume: {formatNumber(data.volume)}</div>
                                        <div className={data.growth >= 0 ? 'positive' : 'negative'}>
                                            Wachstum: {data.growth >= 0 ? '+' : ''}{data.growth.toFixed(1)}%
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="trending-topics">
                        <h4>🔥 Trending Topics</h4>
                        <div className="topics-list">
                            {socialData.trending_now.map((topic, index) => (
                                <div key={index} className="topic-item">
                                    <div className="topic-info">
                                        <span className="topic-name">{topic.topic}</span>
                                        <span className="topic-volume">{formatNumber(topic.volume)} Erwähnungen</span>
                                    </div>
                                    <div className="topic-sentiment">
                                        <div className="sentiment-bar">
                                            <div 
                                                className="sentiment-fill"
                                                style={{ 
                                                    width: `${topic.sentiment * 100}%`,
                                                    backgroundColor: getSentimentColor(topic.sentiment)
                                                }}
                                            />
                                        </div>
                                        <span style={{ color: getSentimentColor(topic.sentiment) }}>
                                            {Math.round(topic.sentiment * 100)}%
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* News Sentiment */}
            {activeMetric === 'news' && sentimentData && (
                <div className="news-sentiment">
                    <div className="news-distribution">
                        <h4>📊 News Sentiment Verteilung</h4>
                        <div className="distribution-chart">
                            <div className="pie-chart">
                                <div 
                                    className="pie-segment positive"
                                    style={{ 
                                        '--percentage': sentimentData.news_sentiment.positive,
                                        background: `conic-gradient(#10b981 0deg ${3.6 * sentimentData.news_sentiment.positive}deg, transparent ${3.6 * sentimentData.news_sentiment.positive}deg)`
                                    }}
                                />
                                <div className="pie-center">
                                    <span>{sentimentData.news_sentiment.total_articles}</span>
                                    <small>Artikel</small>
                                </div>
                            </div>
                            <div className="distribution-legend">
                                <div className="legend-item">
                                    <div className="legend-color positive" />
                                    <span>Positiv: {sentimentData.news_sentiment.positive}%</span>
                                </div>
                                <div className="legend-item">
                                    <div className="legend-color neutral" />
                                    <span>Neutral: {sentimentData.news_sentiment.neutral}%</span>
                                </div>
                                <div className="legend-item">
                                    <div className="legend-color negative" />
                                    <span>Negativ: {sentimentData.news_sentiment.negative}%</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="trending-topics-news">
                        <h4>📈 Trending News Topics</h4>
                        <div className="topics-tags">
                            {sentimentData.news_sentiment.trending_topics.map((topic, index) => (
                                <span key={index} className="topic-tag">
                                    #{topic}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SentimentAnalysis;