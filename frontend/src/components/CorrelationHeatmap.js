import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CorrelationHeatmap = ({ globalTimeframe }) => {
    const [correlationData, setCorrelationData] = useState({});
    const [macroData, setMacroData] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

    useEffect(() => {
        fetchCorrelationData();
        // Auto-refresh every 5 minutes
        const interval = setInterval(fetchCorrelationData, 300000);
        return () => clearInterval(interval);
    }, [globalTimeframe]);

    const fetchCorrelationData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch correlation data and macro data simultaneously
            const [correlationResponse, macroResponse] = await Promise.all([
                axios.get(`${BACKEND_URL}/api/correlations`),
                axios.get(`${BACKEND_URL}/api/macro-data`)
            ]);

            if (correlationResponse.status === 200) {
                setCorrelationData(correlationResponse.data);
            }

            if (macroResponse.status === 200) {
                setMacroData(macroResponse.data);
            }

            setLastUpdate(new Date());
        } catch (err) {
            console.error('Correlation data fetch error:', err);
            setError('Fehler beim Laden der Korrelationsdaten');
        } finally {
            setLoading(false);
        }
    };

    const formatCorrelationValue = (value) => {
        if (typeof value !== 'number') return '0.0%';
        return `${(value * 100).toFixed(1)}%`;
    };

    const getCorrelationColor = (value) => {
        if (typeof value !== 'number') return '#374151';
        
        // Strong positive correlation (70-100%): Dark green
        if (value >= 0.7) return '#065f46';
        // Moderate positive correlation (30-70%): Green
        if (value >= 0.3) return '#16a34a';
        // Weak positive correlation (0-30%): Light green
        if (value >= 0) return '#84cc16';
        // Weak negative correlation (0 to -30%): Light red
        if (value >= -0.3) return '#f87171';
        // Moderate negative correlation (-30% to -70%): Red
        if (value >= -0.7) return '#dc2626';
        // Strong negative correlation (-70% to -100%): Dark red
        return '#991b1b';
    };

    const getCorrelationIntensity = (value) => {
        if (typeof value !== 'number') return 0.3;
        return Math.min(0.3 + Math.abs(value) * 0.7, 1);
    };

    const getCorrelationStrength = (value) => {
        if (typeof value !== 'number') return 'Keine Daten';
        const absValue = Math.abs(value);
        if (absValue >= 0.8) return 'Sehr stark';
        if (absValue >= 0.6) return 'Stark';
        if (absValue >= 0.4) return 'Mäßig';
        if (absValue >= 0.2) return 'Schwach';
        return 'Sehr schwach';
    };

    const preparePairData = () => {
        const pairs = [];
        
        // Process correlation data
        Object.entries(correlationData).forEach(([pairName, value]) => {
            // Parse pair names like "BTC_vs_ETH", "BTC_vs_SPX"
            const parts = pairName.split('_vs_');
            if (parts.length === 2) {
                pairs.push({
                    asset1: parts[0],
                    asset2: parts[1],
                    correlation: value,
                    pairName: pairName
                });
            }
        });

        return pairs.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
    };

    const formatMacroPrice = (price) => {
        if (!price) return 'N/A';
        if (price >= 1000000) return `${(price / 1000000).toFixed(2)}M`;
        if (price >= 1000) return `${(price / 1000).toFixed(2)}k`;
        return price.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };

    if (loading) {
        return (
            <div className="correlation-heatmap loading">
                <div className="loading-spinner"></div>
                <p>Lade Korrelationsdaten...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="correlation-heatmap error">
                <div className="error-message">
                    <span>{error}</span>
                    <button onClick={fetchCorrelationData} className="retry-btn">
                        🔄 Erneut versuchen
                    </button>
                </div>
            </div>
        );
    }

    const pairData = preparePairData();

    return (
        <div className="correlation-heatmap">
            <div className="heatmap-header">
                <div className="title-section">
                    <h3>🔗 Asset Korrelations-Matrix</h3>
                    <div className="timeframe-indicator">
                        <span className="timeframe-badge">{globalTimeframe || '1d'}</span>
                        {lastUpdate && (
                            <span className="last-update">
                                Letzte Aktualisierung: {lastUpdate.toLocaleTimeString('de-DE')}
                            </span>
                        )}
                    </div>
                </div>
                
                <button 
                    onClick={fetchCorrelationData}
                    className="refresh-btn"
                    disabled={loading}
                >
                    🔄 Aktualisieren
                </button>
            </div>

            <div className="correlation-grid">
                {pairData.length > 0 ? (
                    pairData.map((pair, index) => (
                        <div 
                            key={pair.pairName}
                            className="correlation-pair"
                            style={{
                                backgroundColor: getCorrelationColor(pair.correlation),
                                opacity: getCorrelationIntensity(pair.correlation)
                            }}
                        >
                            <div className="pair-header">
                                <span className="asset-pair">
                                    {pair.asset1} ↔ {pair.asset2}
                                </span>
                                <span className="correlation-strength">
                                    {getCorrelationStrength(pair.correlation)}
                                </span>
                            </div>
                            
                            <div className="correlation-value">
                                <span className="percentage">
                                    {formatCorrelationValue(pair.correlation)}
                                </span>
                                <div className="correlation-bar">
                                    <div 
                                        className="bar-fill"
                                        style={{
                                            width: `${Math.abs(pair.correlation * 100)}%`,
                                            backgroundColor: pair.correlation >= 0 ? '#22c55e' : '#ef4444'
                                        }}
                                    />
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="no-data">
                        <p>Keine Korrelationsdaten verfügbar</p>
                    </div>
                )}
            </div>

            {/* Macro Market Summary */}
            {Object.keys(macroData).length > 0 && (
                <div className="macro-summary">
                    <h4>📊 Makro-Markt Übersicht</h4>
                    <div className="macro-grid">
                        {Object.entries(macroData).slice(0, 6).map(([asset, data]) => (
                            <div key={asset} className="macro-item">
                                <span className="asset-name">{asset}</span>
                                <span className="asset-price">${formatMacroPrice(data.price)}</span>
                                <span className={`asset-change ${data.change_24h >= 0 ? 'positive' : 'negative'}`}>
                                    {data.change_24h >= 0 ? '+' : ''}{data.change_24h?.toFixed(2)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Correlation Legend */}
            <div className="correlation-legend">
                <h4>🎯 Korrelations-Legende</h4>
                <div className="legend-items">
                    <div className="legend-item">
                        <div className="legend-color" style={{backgroundColor: '#065f46'}}></div>
                        <span>Sehr starke positive Korrelation (70-100%)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-color" style={{backgroundColor: '#16a34a'}}></div>
                        <span>Starke positive Korrelation (30-70%)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-color" style={{backgroundColor: '#84cc16'}}></div>
                        <span>Schwache positive Korrelation (0-30%)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-color" style={{backgroundColor: '#f87171'}}></div>
                        <span>Schwache negative Korrelation (0 bis -30%)</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-color" style={{backgroundColor: '#dc2626'}}></div>
                        <span>Starke negative Korrelation (-30% bis -70%)</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CorrelationHeatmap;