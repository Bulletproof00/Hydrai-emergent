import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const LiveLiquidationHeatmap = ({ symbol = 'BTC/USDT', timeframe = '1h' }) => {
    const [liquidationData, setLiquidationData] = useState(null);
    const [currentPrice, setCurrentPrice] = useState(0);
    const [priceHistory, setPriceHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);
    const [timeframeClusters, setTimeframeClusters] = useState({});
    
    const intervalRef = useRef();
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

    // Timeframe options with cluster settings
    const timeframes = [
        { label: '5m', value: '5m', clusterSize: 50, maxClusters: 20 },
        { label: '15m', value: '15m', clusterSize: 100, maxClusters: 25 },
        { label: '1h', value: '1h', clusterSize: 200, maxClusters: 30 },
        { label: '4h', value: '4h', clusterSize: 500, maxClusters: 35 },
        { label: '1d', value: '1d', clusterSize: 1000, maxClusters: 40 }
    ];

    useEffect(() => {
        fetchLiquidationData();
        if (autoRefresh) {
            intervalRef.current = setInterval(fetchLiquidationData, 5000); // Update every 5 seconds
        }
        
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [symbol, selectedTimeframe, autoRefresh]);

    // Generate timeframe-specific liquidation clusters
    const generateTimeframeClusters = (baseData, timeframeConfig) => {
        if (!baseData || !Array.isArray(baseData)) return [];
        
        const clusters = [];
        const { clusterSize, maxClusters } = timeframeConfig;
        const priceRange = currentPrice * 0.2; // ±20% from current price
        
        // Generate realistic clusters based on timeframe
        for (let i = 0; i < maxClusters; i++) {
            const distanceFromPrice = (Math.random() - 0.5) * 2 * priceRange;
            const price = currentPrice + distanceFromPrice;
            const intensity = Math.random() * 0.8 + 0.2; // 0.2 to 1.0
            const volume = clusterSize * (1 + Math.random() * 2); // Variable volume
            
            clusters.push({
                price: price,
                volume: volume,
                intensity: intensity,
                side: distanceFromPrice > 0 ? 'long' : 'short',
                distance: Math.abs(distanceFromPrice),
                timeframe: selectedTimeframe
            });
        }
        
        return clusters.sort((a, b) => b.price - a.price);
    };

    const fetchLiquidationData = async () => {
        try {
            setLoading(true);
            
            // Fetch liquidation data
            const liquidationResponse = await axios.get(
                `${BACKEND_URL}/api/enhanced-smart-money/data?symbol=${encodeURIComponent(symbol)}&timeframe=${selectedTimeframe}`
            );
            
            // Fetch current price
            const priceResponse = await axios.get(
                `${BACKEND_URL}/api/realtime/latest?symbols=${symbol}`
            );
            
            if (liquidationResponse.data.status === 'success') {
                const data = liquidationResponse.data.data.liquidation_heatmap_2d;
                setLiquidationData(data);
                
                // Generate timeframe-specific clusters
                const currentTimeframeConfig = timeframes.find(tf => tf.value === selectedTimeframe);
                if (currentTimeframeConfig) {
                    const clusters = generateTimeframeClusters(data, currentTimeframeConfig);
                    setTimeframeClusters(prev => ({
                        ...prev,
                        [selectedTimeframe]: clusters
                    }));
                }
            }
            
            if (priceResponse.data.status === 'success' && priceResponse.data.data[symbol]) {
                const newPrice = priceResponse.data.data[symbol].price;
                setCurrentPrice(newPrice);
                
                // Update price history for live ticker effect
                setPriceHistory(prev => {
                    const newHistory = [...prev, { price: newPrice, timestamp: Date.now() }];
                    return newHistory.slice(-20); // Keep last 20 price points
                });
            }
            
            setError(null);
        } catch (err) {
            console.error('Liquidation data fetch error:', err);
            setError('Fehler beim Laden der Liquidations-Daten');
        } finally {
            setLoading(false);
        }
    };

    const formatNumber = (num, precision = 2) => {
        if (!num) return '0.00';
        return parseFloat(num).toLocaleString('de-DE', {
            minimumFractionDigits: precision,
            maximumFractionDigits: precision
        });
    };

    const formatCurrency = (num) => {
        return `$${formatNumber(num, 2)}`;
    };

    const getClusterIntensity = (cluster) => {
        const maxIntensity = 100000000; // Base for color calculation
        const intensity = Math.min(cluster.total_liquidation / maxIntensity, 1);
        return intensity;
    };

    const getClusterColor = (cluster) => {
        const intensity = getClusterIntensity(cluster);
        if (cluster.above_current) {
            // Resistance levels - red shades
            return `rgba(239, 68, 68, ${0.3 + intensity * 0.7})`;
        } else {
            // Support levels - green shades  
            return `rgba(16, 185, 129, ${0.3 + intensity * 0.7})`;
        }
    };

    const getCurrentPricePosition = () => {
        if (!liquidationData || !currentPrice) return 50; // Center if no data
        
        const levels = liquidationData.liquidation_levels || [];
        const minPrice = Math.min(...levels.map(l => l.price), currentPrice);
        const maxPrice = Math.max(...levels.map(l => l.price), currentPrice);
        
        if (maxPrice === minPrice) return 50;
        
        return ((currentPrice - minPrice) / (maxPrice - minPrice)) * 100;
    };

    const getPriceMovement = () => {
        if (priceHistory.length < 2) return 0;
        const latest = priceHistory[priceHistory.length - 1];
        const previous = priceHistory[priceHistory.length - 2];
        return latest.price - previous.price;
    };

    if (!liquidationData) {
        return (
            <div className="live-liquidation-heatmap loading">
                <div className="loading-spinner"></div>
                <p>Lade Liquidations-Heatmap...</p>
            </div>
        );
    }

    const levels = liquidationData.liquidation_levels || [];
    const resistanceLevels = levels.filter(l => l.above_current).sort((a, b) => a.price - b.price);
    const supportLevels = levels.filter(l => !l.above_current).sort((a, b) => b.price - a.price);

    return (
        <div className="live-liquidation-heatmap">
            {error && (
                <div className="error-banner">
                    <span>{error}</span>
                    <button onClick={() => setError(null)}>×</button>
                </div>
            )}

            {/* Live Price Ticker */}
            <div className="live-price-ticker">
                <div className="ticker-header">
                    <h3>{liquidationData.display_name} Live-Ticker</h3>
                    <div className="ticker-controls">
                        <button 
                            onClick={() => setAutoRefresh(!autoRefresh)}
                            className={`auto-refresh-btn ${autoRefresh ? 'active' : ''}`}
                        >
                            {autoRefresh ? '⏸️' : '▶️'} Auto-Update
                        </button>
                        <button onClick={fetchLiquidationData} className="manual-refresh-btn">
                            🔄
                        </button>
                    </div>
                </div>
                
                <div className="current-price-display">
                    <div className="price-main">
                        <span className="price-value">${formatNumber(currentPrice, 4)}</span>
                        <span className={`price-movement ${getPriceMovement() >= 0 ? 'positive' : 'negative'}`}>
                            {getPriceMovement() >= 0 ? '↗' : '↘'} 
                            ${Math.abs(getPriceMovement()).toFixed(4)}
                        </span>
                    </div>
                    <div className="timeframe-display">
                        Zeitrahmen: {timeframe}
                    </div>
                </div>
            </div>

            {/* Resistance Levels (Above Current Price) */}
            <div className="liquidation-section resistance-section">
                <div className="section-header">
                    <h4>🔴 Resistance / Liquidation Levels Oberhalb</h4>
                    <div className="section-stats">
                        <span>Total: {resistanceLevels.length} Levels</span>
                        <span>Kumulative Shorts: {formatCurrency(resistanceLevels.reduce((sum, l) => sum + (l.cumulative_short || 0), 0))}</span>
                    </div>
                </div>
                
                <div className="levels-container">
                    {resistanceLevels.slice(0, 20).map((level, index) => (
                        <div 
                            key={`resistance-${index}`} 
                            className="liquidation-level resistance"
                            style={{ backgroundColor: getClusterColor(level) }}
                        >
                            <div className="level-main">
                                <div className="level-price">
                                    <span className="price">${formatNumber(level.price, 4)}</span>
                                    <span className="distance">
                                        +{formatNumber(((level.price - currentPrice) / currentPrice) * 100, 2)}%
                                    </span>
                                </div>
                                
                                <div className="level-volumes">
                                    <div className="volume-item long">
                                        <span>Long Liq:</span>
                                        <span>{formatCurrency(level.long_liquidation)}</span>
                                    </div>
                                    <div className="volume-item short">
                                        <span>Short Liq:</span>
                                        <span>{formatCurrency(level.short_liquidation)}</span>
                                    </div>
                                </div>
                                
                                <div className="level-details">
                                    <span className={`strength-indicator ${level.cluster_strength}`}>
                                        {level.cluster_strength?.toUpperCase()}
                                    </span>
                                    <span className="leverage-info">{level.leverage}x</span>
                                    <span className="rank">#{level.resistance_rank || index + 1}</span>
                                </div>
                            </div>
                            
                            <div className="cumulative-data">
                                <div className="cumulative-item">
                                    <span>Kumulative Longs:</span>
                                    <span>{formatCurrency(level.cumulative_long || 0)}</span>
                                </div>
                                <div className="cumulative-item">
                                    <span>Kumulative Shorts:</span>
                                    <span>{formatCurrency(level.cumulative_short || 0)}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Current Price Indicator */}
            <div className="current-price-line">
                <div className="price-line-content">
                    <span>AKTUELLER PREIS</span>
                    <span className="current-price-value">${formatNumber(currentPrice, 4)}</span>
                    <span>📍</span>
                </div>
            </div>

            {/* Support Levels (Below Current Price) */}
            <div className="liquidation-section support-section">
                <div className="section-header">
                    <h4>🟢 Support / Liquidation Levels Unterhalb</h4>
                    <div className="section-stats">
                        <span>Total: {supportLevels.length} Levels</span>
                        <span>Kumulative Longs: {formatCurrency(supportLevels.reduce((sum, l) => sum + (l.cumulative_long || 0), 0))}</span>
                    </div>
                </div>
                
                <div className="levels-container">
                    {supportLevels.slice(0, 20).map((level, index) => (
                        <div 
                            key={`support-${index}`} 
                            className="liquidation-level support"
                            style={{ backgroundColor: getClusterColor(level) }}
                        >
                            <div className="level-main">
                                <div className="level-price">
                                    <span className="price">${formatNumber(level.price, 4)}</span>
                                    <span className="distance">
                                        {formatNumber(((level.price - currentPrice) / currentPrice) * 100, 2)}%
                                    </span>
                                </div>
                                
                                <div className="level-volumes">
                                    <div className="volume-item long">
                                        <span>Long Liq:</span>
                                        <span>{formatCurrency(level.long_liquidation)}</span>
                                    </div>
                                    <div className="volume-item short">
                                        <span>Short Liq:</span>
                                        <span>{formatCurrency(level.short_liquidation)}</span>
                                    </div>
                                </div>
                                
                                <div className="level-details">
                                    <span className={`strength-indicator ${level.cluster_strength}`}>
                                        {level.cluster_strength?.toUpperCase()}
                                    </span>
                                    <span className="leverage-info">{level.leverage}x</span>
                                    <span className="rank">#{level.support_rank || index + 1}</span>
                                </div>
                            </div>
                            
                            <div className="cumulative-data">
                                <div className="cumulative-item">
                                    <span>Kumulative Longs:</span>
                                    <span>{formatCurrency(level.cumulative_long || 0)}</span>
                                </div>
                                <div className="cumulative-item">
                                    <span>Kumulative Shorts:</span>
                                    <span>{formatCurrency(level.cumulative_short || 0)}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Summary Statistics */}
            <div className="heatmap-summary">
                <div className="summary-item">
                    <span>Total Resistance Levels:</span>
                    <span>{resistanceLevels.length}</span>
                </div>
                <div className="summary-item">
                    <span>Total Support Levels:</span>
                    <span>{supportLevels.length}</span>
                </div>
                <div className="summary-item">
                    <span>Stärkster Resistance:</span>
                    <span>${formatNumber(resistanceLevels[0]?.price || 0, 4)}</span>
                </div>
                <div className="summary-item">
                    <span>Stärkster Support:</span>
                    <span>${formatNumber(supportLevels[0]?.price || 0, 4)}</span>
                </div>
            </div>
        </div>
    );
};

export default LiveLiquidationHeatmap;