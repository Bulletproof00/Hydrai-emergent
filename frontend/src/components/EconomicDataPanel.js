import React, { useState, useEffect } from 'react';
import axios from 'axios';

const EconomicDataPanel = ({ globalTimeframe }) => {
    const [economicData, setEconomicData] = useState(null);
    const [newsData, setNewsData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeSubTab, setActiveSubTab] = useState('calendar');
    const [lastUpdate, setLastUpdate] = useState(null);

    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

    useEffect(() => {
        fetchEconomicData();
        // Auto-refresh every 15 minutes
        const interval = setInterval(fetchEconomicData, 900000);
        return () => clearInterval(interval);
    }, [globalTimeframe]);

    const fetchEconomicData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch economic calendar and news data
            const [calendarResponse, newsResponse] = await Promise.all([
                axios.get(`${BACKEND_URL}/api/economic-calendar`),
                axios.get(`${BACKEND_URL}/api/financial-news`)
            ]);

            if (calendarResponse.status === 200) {
                setEconomicData(calendarResponse.data);
            }

            if (newsResponse.status === 200) {
                setNewsData(newsResponse.data);
            }

            setLastUpdate(new Date());
        } catch (err) {
            console.error('Economic data fetch error:', err);
            setError('Fehler beim Laden der Wirtschaftsdaten');
            
            // Use mock data for demonstration
            setEconomicData({
                today: [
                    {
                        time: '14:30',
                        event: 'US Initial Jobless Claims',
                        forecast: '220K',
                        previous: '215K',
                        actual: '225K',
                        importance: 'medium',
                        currency: 'USD'
                    },
                    {
                        time: '16:00',
                        event: 'US Existing Home Sales',
                        forecast: '4.10M',
                        previous: '4.15M',
                        actual: null,
                        importance: 'low',
                        currency: 'USD'
                    }
                ],
                week: [
                    {
                        date: '2025-10-09',
                        time: '14:30',
                        event: 'US Consumer Price Index',
                        forecast: '0.2%',
                        previous: '0.3%',
                        actual: null,
                        importance: 'high',
                        currency: 'USD'
                    },
                    {
                        date: '2025-10-10',
                        time: '20:30',
                        event: 'Federal Reserve Interest Rate Decision',
                        forecast: '5.25%',
                        previous: '5.00%',
                        actual: null,
                        importance: 'high',
                        currency: 'USD'
                    }
                ]
            });

            setNewsData([
                {
                    title: 'Federal Reserve Signals Potential Rate Cuts as Inflation Shows Signs of Cooling',
                    summary: 'The Federal Reserve indicated it may consider rate cuts in the coming quarters as inflation metrics show continued moderation...',
                    url: '#',
                    source: 'Reuters',
                    publishedAt: new Date(Date.now() - 1800000).toISOString(),
                    sentiment: 'positive',
                    sentimentScore: 0.72,
                    topics: ['Federal Reserve', 'Interest Rates', 'Inflation']
                },
                {
                    title: 'Bitcoin ETF Sees Record Inflows as Institutional Adoption Grows',
                    summary: 'Spot Bitcoin exchange-traded funds recorded their largest single-day inflow this week, signaling growing institutional interest...',
                    url: '#',
                    source: 'Bloomberg',
                    publishedAt: new Date(Date.now() - 3600000).toISOString(),
                    sentiment: 'positive',
                    sentimentScore: 0.85,
                    topics: ['Bitcoin', 'ETF', 'Institutional Investment']
                },
                {
                    title: 'European Central Bank Maintains Hawkish Stance Amid Economic Concerns',
                    summary: 'The European Central Bank reiterated its commitment to fighting inflation despite growing concerns about economic growth...',
                    url: '#',
                    source: 'Financial Times',
                    publishedAt: new Date(Date.now() - 7200000).toISOString(),
                    sentiment: 'neutral',
                    sentimentScore: 0.45,
                    topics: ['ECB', 'European Economy', 'Monetary Policy']
                },
                {
                    title: 'US Dollar Strengthens on Strong Economic Data and Fed Hawkishness',
                    summary: 'The US Dollar Index reached new weekly highs following better-than-expected economic indicators and Federal Reserve commentary...',
                    url: '#',
                    source: 'MarketWatch',
                    publishedAt: new Date(Date.now() - 10800000).toISOString(),
                    sentiment: 'positive',
                    sentimentScore: 0.68,
                    topics: ['US Dollar', 'Economic Data', 'Currency Markets']
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (timeString) => {
        return timeString || 'N/A';
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('de-DE', {
            weekday: 'short',
            day: '2-digit',
            month: '2-digit'
        });
    };

    const formatRelativeTime = (dateString) => {
        const now = new Date();
        const publishedDate = new Date(dateString);
        const diffInHours = (now - publishedDate) / (1000 * 60 * 60);

        if (diffInHours < 1) {
            const diffInMinutes = Math.floor((now - publishedDate) / (1000 * 60));
            return `vor ${diffInMinutes} Min`;
        } else if (diffInHours < 24) {
            return `vor ${Math.floor(diffInHours)} Std`;
        } else {
            return `vor ${Math.floor(diffInHours / 24)} Tag(en)`;
        }
    };

    const getImportanceColor = (importance) => {
        switch (importance) {
            case 'high': return '#ef4444';
            case 'medium': return '#f59e0b';
            case 'low': return '#10b981';
            default: return '#6b7280';
        }
    };

    const getSentimentColor = (sentiment) => {
        switch (sentiment) {
            case 'positive': return '#10b981';
            case 'negative': return '#ef4444';
            case 'neutral': return '#f59e0b';
            default: return '#6b7280';
        }
    };

    const getSentimentIcon = (sentiment) => {
        switch (sentiment) {
            case 'positive': return '📈';
            case 'negative': return '📉';
            case 'neutral': return '➡️';
            default: return '❓';
        }
    };

    if (loading) {
        return (
            <div className="economic-data-panel loading">
                <div className="loading-spinner"></div>
                <p>Lade Wirtschaftsdaten...</p>
            </div>
        );
    }

    return (
        <div className="economic-data-panel">
            <div className="panel-header">
                <div className="title-section">
                    <h3>📊 Wirtschaftsdaten & News</h3>
                    {lastUpdate && (
                        <span className="last-update">
                            Letzte Aktualisierung: {lastUpdate.toLocaleTimeString('de-DE')}
                        </span>
                    )}
                </div>
                
                <button 
                    onClick={fetchEconomicData}
                    className="refresh-btn"
                    disabled={loading}
                >
                    🔄 Aktualisieren
                </button>
            </div>

            {error && (
                <div className="error-banner">
                    <span>{error}</span>
                    <button onClick={() => setError(null)}>×</button>
                </div>
            )}

            {/* Sub-tabs */}
            <div className="sub-tabs">
                <button 
                    className={`sub-tab ${activeSubTab === 'calendar' ? 'active' : ''}`}
                    onClick={() => setActiveSubTab('calendar')}
                >
                    📅 Wirtschaftskalender
                </button>
                <button 
                    className={`sub-tab ${activeSubTab === 'news' ? 'active' : ''}`}
                    onClick={() => setActiveSubTab('news')}
                >
                    📰 News & Sentiment
                </button>
            </div>

            {/* Economic Calendar Tab */}
            {activeSubTab === 'calendar' && (
                <div className="calendar-content">
                    <div className="calendar-section">
                        <h4>🎯 Heute</h4>
                        {economicData?.today?.length > 0 ? (
                            <div className="events-list">
                                {economicData.today.map((event, index) => (
                                    <div key={index} className="event-card">
                                        <div className="event-header">
                                            <div className="event-time">
                                                <span className="time">{formatTime(event.time)}</span>
                                                <span 
                                                    className="importance-indicator"
                                                    style={{ backgroundColor: getImportanceColor(event.importance) }}
                                                >
                                                    {event.importance?.toUpperCase() || 'N/A'}
                                                </span>
                                            </div>
                                            <span className="currency">{event.currency}</span>
                                        </div>
                                        
                                        <div className="event-details">
                                            <h5 className="event-name">{event.event}</h5>
                                            <div className="event-metrics">
                                                <div className="metric">
                                                    <span className="label">Prognose:</span>
                                                    <span className="value">{event.forecast || 'N/A'}</span>
                                                </div>
                                                <div className="metric">
                                                    <span className="label">Vorherig:</span>
                                                    <span className="value">{event.previous || 'N/A'}</span>
                                                </div>
                                                {event.actual && (
                                                    <div className="metric">
                                                        <span className="label">Tatsächlich:</span>
                                                        <span className="value actual">{event.actual}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-data">Keine Ereignisse für heute geplant</p>
                        )}
                    </div>

                    <div className="calendar-section">
                        <h4>📆 Diese Woche</h4>
                        {economicData?.week?.length > 0 ? (
                            <div className="events-list">
                                {economicData.week.map((event, index) => (
                                    <div key={index} className="event-card">
                                        <div className="event-header">
                                            <div className="event-time">
                                                <span className="date">{formatDate(event.date)}</span>
                                                <span className="time">{formatTime(event.time)}</span>
                                                <span 
                                                    className="importance-indicator"
                                                    style={{ backgroundColor: getImportanceColor(event.importance) }}
                                                >
                                                    {event.importance?.toUpperCase() || 'N/A'}
                                                </span>
                                            </div>
                                            <span className="currency">{event.currency}</span>
                                        </div>
                                        
                                        <div className="event-details">
                                            <h5 className="event-name">{event.event}</h5>
                                            <div className="event-metrics">
                                                <div className="metric">
                                                    <span className="label">Prognose:</span>
                                                    <span className="value">{event.forecast || 'N/A'}</span>
                                                </div>
                                                <div className="metric">
                                                    <span className="label">Vorherig:</span>
                                                    <span className="value">{event.previous || 'N/A'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-data">Keine wichtigen Ereignisse diese Woche</p>
                        )}
                    </div>
                </div>
            )}

            {/* News & Sentiment Tab */}
            {activeSubTab === 'news' && (
                <div className="news-content">
                    <div className="news-header">
                        <h4>📰 Aktuelle Finanznachrichten</h4>
                        <div className="sentiment-legend">
                            <span className="legend-item">📈 Positiv</span>
                            <span className="legend-item">📉 Negativ</span>
                            <span className="legend-item">➡️ Neutral</span>
                        </div>
                    </div>

                    {newsData.length > 0 ? (
                        <div className="news-list">
                            {newsData.map((article, index) => (
                                <div key={index} className="news-card">
                                    <div className="news-header-row">
                                        <div className="news-meta">
                                            <span className="news-source">{article.source}</span>
                                            <span className="news-time">
                                                {formatRelativeTime(article.publishedAt)}
                                            </span>
                                        </div>
                                        <div className="sentiment-indicator">
                                            <span className="sentiment-icon">
                                                {getSentimentIcon(article.sentiment)}
                                            </span>
                                            <span 
                                                className="sentiment-score"
                                                style={{ color: getSentimentColor(article.sentiment) }}
                                            >
                                                {(article.sentimentScore * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </div>

                                    <h5 className="news-title">{article.title}</h5>
                                    <p className="news-summary">{article.summary}</p>

                                    {article.topics && (
                                        <div className="news-topics">
                                            {article.topics.map((topic, topicIndex) => (
                                                <span key={topicIndex} className="topic-tag">
                                                    {topic}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="no-data">Keine aktuellen Nachrichten verfügbar</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default EconomicDataPanel;