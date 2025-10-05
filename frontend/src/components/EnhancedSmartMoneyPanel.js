import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const EnhancedSmartMoneyPanel = () => {
    const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
    const [supportedSymbols, setSupportedSymbols] = useState([]);
    const [smartMoneyData, setSmartMoneyData] = useState(null);
    const [activeTab, setActiveTab] = useState('liquidation_heatmap');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedTimeframe, setSelectedTimeframe] = useState('1day');

    useEffect(() => {
        fetchSupportedSymbols();
    }, []);

    useEffect(() => {
        if (selectedSymbol) {
            fetchEnhancedSmartMoneyData();
        }
    }, [selectedSymbol, selectedTimeframe]);

    const fetchSupportedSymbols = async () => {
        try {
            const response = await axios.get(`${BACKEND_URL}/api/enhanced-smart-money/supported-symbols`);
            
            if (response.data.status === 'success') {
                setSupportedSymbols(response.data.symbols);
                if (response.data.symbols.length > 0) {
                    setSelectedSymbol(response.data.symbols[0].symbol);
                }
            } else {
                setError(response.data.message || 'Failed to fetch supported symbols');
            }
        } catch (err) {
            console.error('Supported symbols fetch error:', err);
            setError('Failed to load supported symbols');
        }
    };

    const fetchEnhancedSmartMoneyData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // Fetch real-time price first to ensure current data
            const priceResponse = await axios.get(`${BACKEND_URL}/api/realtime/latest?symbols=${selectedSymbol}`);
            let currentPrice = null;
            
            if (priceResponse.data.status === 'success' && priceResponse.data.data[selectedSymbol]) {
                currentPrice = priceResponse.data.data[selectedSymbol].price;
            }
            
            // Then fetch Enhanced Smart Money data with timeframe
            const response = await axios.get(`${BACKEND_URL}/api/enhanced-smart-money/data?symbol=${encodeURIComponent(selectedSymbol)}&timeframe=${selectedTimeframe}`);
            
            if (response.data.status === 'success') {
                const enhancedData = response.data.data;
                if (enhancedData) {
                    // Update current price if we have real-time data
                    if (currentPrice && enhancedData.liquidation_heatmap_2d) {
                        enhancedData.liquidation_heatmap_2d.current_price = currentPrice;
                    }
                    if (currentPrice && enhancedData.open_interest_detailed) {
                        enhancedData.open_interest_detailed.current_price = currentPrice;
                    }
                    
                    setSmartMoneyData(enhancedData);
                } else {
                    setError('No enhanced data available for selected symbol');
                }
            } else {
                setError(response.data.message || 'Failed to fetch enhanced smart money data');
            }
        } catch (err) {
            console.error('Enhanced smart money data fetch error:', err);
            setError('Failed to load enhanced smart money data');
        } finally {
            setLoading(false);
        }
    };

    // Note: transformToEnhancedFormat function removed as we now use Enhanced Smart Money APIs directly

    const getCurrentPriceForSymbol = (symbol) => {
        // Realistic current prices for different assets
        const currentPrices = {
            'BTC/USDT': 62000,
            'ETH/USDT': 2450, 
            'SOL/USDT': 141,
            'XRP/USDT': 0.53,
            'BNB/USDT': 585,
            'ADA/USDT': 0.36
        };
        return currentPrices[symbol] || 100;
    };

    const generateRealisticLiquidationLevels = (currentPrice, symbol, timeframe = '1day') => {
        // Generate realistic liquidation levels based on timeframe and focus on near-price clusters
        const levels = [];
        const leverageLevels = [5, 10, 20, 50, 100];
        
        // Timeframe multipliers for volume and range
        const timeframeConfig = {
            '12h': { multiplier: 0.5, maxDistance: 0.15, clusterCount: 15 },
            '1day': { multiplier: 1, maxDistance: 0.20, clusterCount: 20 },
            '3day': { multiplier: 1.8, maxDistance: 0.25, clusterCount: 25 },
            '1week': { multiplier: 3, maxDistance: 0.30, clusterCount: 30 },
            '2week': { multiplier: 5, maxDistance: 0.35, clusterCount: 35 },
            'monthly': { multiplier: 8, maxDistance: 0.40, clusterCount: 40 }
        };
        
        const config = timeframeConfig[timeframe] || timeframeConfig['1day'];
        const baseVolume = currentPrice * 50000 * config.multiplier;
        
        // Generate focused liquidation clusters near current price
        for (let leverage of leverageLevels) {
            const liquidationThreshold = (1 / leverage) * 0.9;
            
            // Long liquidations (below current price) - more likely in bull markets
            const longLiqPrice = currentPrice * (1 - liquidationThreshold);
            const longVolume = baseVolume * (Math.random() * 2 + 0.8); // Higher volume for long liquidations
            
            // Short liquidations (above current price) - resistance levels
            const shortLiqPrice = currentPrice * (1 + liquidationThreshold);
            const shortVolume = baseVolume * (Math.random() * 1.5 + 0.4); // Moderate short volume
            
            if ((currentPrice - longLiqPrice) / currentPrice <= config.maxDistance) {
                levels.push({
                    price: longLiqPrice,
                    long_liquidation: longVolume,
                    short_liquidation: longVolume * 0.2,
                    total_liquidation: longVolume * 1.2,
                    above_current: false,
                    leverage: leverage,
                    distance_percent: ((currentPrice - longLiqPrice) / currentPrice) * 100,
                    cluster_strength: 'high',
                    timeframe_impact: timeframe
                });
            }
            
            if ((shortLiqPrice - currentPrice) / currentPrice <= config.maxDistance) {
                levels.push({
                    price: shortLiqPrice,
                    long_liquidation: shortVolume * 0.3,
                    short_liquidation: shortVolume,
                    total_liquidation: shortVolume * 1.3,
                    above_current: true,
                    leverage: leverage,
                    distance_percent: ((shortLiqPrice - currentPrice) / currentPrice) * 100,
                    cluster_strength: 'high',
                    timeframe_impact: timeframe
                });
            }
        }
        
        // Add focused cluster levels near current price (±1% to maxDistance)
        for (let i = 0; i < config.clusterCount; i++) {
            const distancePercent = Math.random() * config.maxDistance + 0.01; // 1% to maxDistance
            const isAbove = Math.random() > 0.45; // Slight bias toward above (resistance)
            
            const price = isAbove ? 
                currentPrice * (1 + distancePercent) : 
                currentPrice * (1 - distancePercent);
            
            // Cluster strength based on distance (closer = stronger)
            const proximityFactor = 1 - (distancePercent / config.maxDistance);
            const clusterStrength = proximityFactor > 0.7 ? 'very_high' : proximityFactor > 0.4 ? 'high' : 'medium';
            
            const volume = baseVolume * proximityFactor * (Math.random() * 2 + 0.5);
            
            levels.push({
                price: price,
                long_liquidation: isAbove ? volume * 0.25 : volume,
                short_liquidation: isAbove ? volume : volume * 0.25,
                total_liquidation: volume * 1.25,
                above_current: isAbove,
                leverage: 'cluster',
                distance_percent: distancePercent * 100,
                cluster_strength: clusterStrength,
                timeframe_impact: timeframe
            });
        }
        
        // Sort by price and filter to most relevant levels
        const sortedLevels = levels.sort((a, b) => a.price - b.price);
        
        // Focus on levels within reasonable distance of current price
        const filteredLevels = sortedLevels.filter(level => {
            const distance = Math.abs(level.price - currentPrice) / currentPrice;
            return distance <= config.maxDistance;
        });
        
        return filteredLevels.slice(0, config.clusterCount);
    };

    const calculateDirectionalBias = (levels, currentPrice) => {
        // Calculate bias based on liquidation clusters above vs below current price
        const aboveLevels = levels.filter(l => l.above_current);
        const belowLevels = levels.filter(l => !l.above_current);
        
        const totalAboveVolume = aboveLevels.reduce((sum, l) => sum + (l.total_liquidation || 0), 0);
        const totalBelowVolume = belowLevels.reduce((sum, l) => sum + (l.total_liquidation || 0), 0);
        
        const totalVolume = totalAboveVolume + totalBelowVolume;
        const aboveRatio = totalVolume > 0 ? totalAboveVolume / totalVolume : 0.5;
        
        // Calculate strongest clusters near current price
        const nearLevels = levels.filter(l => 
            Math.abs(l.price - currentPrice) / currentPrice <= 0.05 // Within 5%
        );
        
        const nearAbove = nearLevels.filter(l => l.above_current);
        const nearBelow = nearLevels.filter(l => !l.above_current);
        
        // Determine bias
        let bias = 'neutral';
        let biasStrength = 0;
        
        if (aboveRatio > 0.65) {
            bias = 'bearish'; // More liquidations above = resistance = bearish
            biasStrength = (aboveRatio - 0.5) * 2; // 0.3 to 1.0
        } else if (aboveRatio < 0.35) {
            bias = 'bullish'; // More liquidations below = support = bullish
            biasStrength = (0.5 - aboveRatio) * 2; // 0.3 to 1.0
        } else {
            bias = 'neutral';
            biasStrength = 1 - Math.abs(aboveRatio - 0.5) * 2; // 0 to 1.0
        }
        
        return {
            bias: bias,
            strength: Math.min(1, Math.max(0, biasStrength)),
            above_ratio: aboveRatio,
            below_ratio: 1 - aboveRatio,
            total_above_volume: totalAboveVolume,
            total_below_volume: totalBelowVolume,
            near_clusters_above: nearAbove.length,
            near_clusters_below: nearBelow.length,
            recommendation: getBiasRecommendation(bias, biasStrength, nearAbove.length, nearBelow.length)
        };
    };

    const getBiasRecommendation = (bias, strength, nearAbove, nearBelow) => {
        const strengthText = strength > 0.7 ? 'Strong' : strength > 0.4 ? 'Moderate' : 'Weak';
        
        if (bias === 'bullish') {
            return `${strengthText} Bullish Bias - More liquidations below current price. Expect upward pressure.`;
        } else if (bias === 'bearish') {
            return `${strengthText} Bearish Bias - Heavy resistance above. Expect downward pressure.`;
        } else {
            return `Neutral - Balanced liquidations. Watch for breakout direction.`;
        }
    };

    const handleSymbolChange = (event) => {
        setSelectedSymbol(event.target.value);
    };

    const renderTimeframeSelector = () => {
        const timeframes = [
            { value: '5m', label: '5 Min' },
            { value: '15m', label: '15 Min' },
            { value: '1h', label: '1 Stunde' },
            { value: '4h', label: '4 Stunden' },
            { value: '8h', label: '8 Stunden' },
            { value: '12h', label: '12 Stunden' },
            { value: '1day', label: '1 Tag' },
            { value: '3day', label: '3 Tage' },
            { value: '1week', label: '1 Woche' },
            { value: '2week', label: '2 Wochen' },
            { value: 'monthly', label: '1 Monat' }
        ];

        return (
            <div className="timeframe-selector-container">
                <select 
                    id="timeframe-select"
                    value={selectedTimeframe} 
                    onChange={(e) => setSelectedTimeframe(e.target.value)}
                    className="timeframe-select"
                    title="Zeitrahmen auswählen"
                >
                    {timeframes.map((tf) => (
                        <option key={tf.value} value={tf.value}>
                            {tf.label}
                        </option>
                    ))}
                </select>
            </div>
        );
    };

    const renderSymbolSelector = () => {
        return (
            <div className="symbol-selector-container">
                <label htmlFor="symbol-select" className="symbol-label">Asset:</label>
                <select 
                    id="symbol-select"
                    value={selectedSymbol} 
                    onChange={handleSymbolChange}
                    className="symbol-select"
                >
                    {supportedSymbols.map((symbolInfo) => (
                        <option key={symbolInfo.symbol} value={symbolInfo.symbol}>
                            {symbolInfo.display_name} ({symbolInfo.symbol})
                        </option>
                    ))}
                </select>
            </div>
        );
    };

    const renderLiquidationHeatmap2D = () => {
        const heatmapData = smartMoneyData?.liquidation_heatmap_2d;
        
        if (!heatmapData || !heatmapData.liquidation_levels) {
            return <div className="no-data">No 2D liquidation heatmap data available</div>;
        }

        const summary = heatmapData.summary || {};
        const levels = heatmapData.liquidation_levels.slice(0, 20); // Top 20 levels
        const currentPrice = heatmapData.current_price;

        return (
            <div className="liquidation-heatmap-2d">
                <div className="heatmap-header-enhanced">
                    <div className="header-left">
                        <h3>Liquidation Clusters - {heatmapData.display_name}</h3>
                        <div className="current-price-large">
                            Current Price: ${currentPrice?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                        <div className="timeframe-display">
                            Timeframe: {summary.timeframe || selectedTimeframe}
                        </div>
                    </div>
                    <div className="header-right">
                        {summary.directional_bias && (
                            <div className="directional-bias">
                                <div className={`bias-indicator ${summary.directional_bias.bias}`}>
                                    <span className="bias-label">Market Bias:</span>
                                    <span className="bias-value">
                                        {summary.directional_bias.bias.toUpperCase()}
                                    </span>
                                    <div className="bias-strength">
                                        Strength: {(summary.directional_bias.strength * 100).toFixed(0)}%
                                    </div>
                                </div>
                            </div>
                        )}
                        <div className="risk-score">
                            <span className="risk-label">Risk:</span>
                            <span className={`risk-value ${summary.risk_score > 70 ? 'high' : summary.risk_score > 40 ? 'medium' : 'low'}`}>
                                {summary.risk_score?.toFixed(0)}/100
                            </span>
                        </div>
                    </div>
                </div>

                {summary.directional_bias && (
                    <div className="directional-analysis-card">
                        <div className="analysis-header">
                            <h4>📊 Directional Analysis</h4>
                        </div>
                        <div className="bias-breakdown">
                            <div className={`bias-main ${summary.directional_bias.bias}`}>
                                <div className="bias-text">
                                    {summary.directional_bias.bias.toUpperCase()} BIAS
                                </div>
                                <div className="bias-percentage">
                                    {(summary.directional_bias.strength * 100).toFixed(0)}% Confidence
                                </div>
                            </div>
                            <div className="bias-ratios">
                                <div className="ratio-item above">
                                    <span className="ratio-label">Above:</span>
                                    <span className="ratio-value">{(summary.directional_bias.above_ratio * 100).toFixed(1)}%</span>
                                </div>
                                <div className="ratio-item below">
                                    <span className="ratio-label">Below:</span>
                                    <span className="ratio-value">{(summary.directional_bias.below_ratio * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        </div>
                        <div className="bias-recommendation">
                            {summary.directional_bias.recommendation}
                        </div>
                    </div>
                )}

                <div className="liquidation-summary-cards">
                    <div className="summary-card above">
                        <div className="card-header">
                            <span className="card-title">Above Current Price</span>
                            <span className="card-subtitle">Resistance Clusters</span>
                        </div>
                        <div className="card-value">
                            ${(summary.total_liquidations_above / 1000000)?.toFixed(1)}M
                        </div>
                        <div className="card-levels">
                            {summary.levels_count_above} clusters
                        </div>
                        {summary.strongest_level_above && (
                            <div className="card-strongest">
                                Key Level: ${summary.strongest_level_above.price?.toFixed(2)}
                            </div>
                        )}
                        {summary.directional_bias && (
                            <div className="card-near-clusters">
                                Near Price: {summary.directional_bias.near_clusters_above} clusters
                            </div>
                        )}
                    </div>

                    <div className="summary-card below">
                        <div className="card-header">
                            <span className="card-title">Below Current Price</span>
                            <span className="card-subtitle">Support Clusters</span>
                        </div>
                        <div className="card-value">
                            ${(summary.total_liquidations_below / 1000000)?.toFixed(1)}M
                        </div>
                        <div className="card-levels">
                            {summary.levels_count_below} clusters
                        </div>
                        {summary.strongest_level_below && (
                            <div className="card-strongest">
                                Key Level: ${summary.strongest_level_below.price?.toFixed(2)}
                            </div>
                        )}
                        {summary.directional_bias && (
                            <div className="card-near-clusters">
                                Near Price: {summary.directional_bias.near_clusters_below} clusters
                            </div>
                        )}
                    </div>
                </div>

                <div className="liquidation-levels-enhanced">
                    <div className="levels-header">
                        <h4>Near-Price Liquidation Clusters ({selectedTimeframe})</h4>
                        <div className="levels-legend">
                            <div className="legend-item">
                                <div className="legend-color resistance"></div>
                                <span>Resistance (Above Price)</span>
                            </div>
                            <div className="legend-item">
                                <div className="legend-color support"></div>
                                <span>Support (Below Price)</span>
                            </div>
                            <div className="legend-item cluster-strength">
                                <span>🔥 High Impact Clusters</span>
                            </div>
                        </div>
                    </div>

                    <div className="levels-table">
                        <div className="levels-table-header">
                            <div className="col-price">Price Level</div>
                            <div className="col-distance">Distance</div>
                            <div className="col-volume">Volume</div>
                            <div className="col-strength">Impact</div>
                            <div className="col-direction">Direction</div>
                        </div>

                        {levels.slice(0, 15).map((level, index) => {
                            const isAboveCurrent = level.above_current;
                            const distancePercent = level.distance_percent || ((Math.abs(level.price - currentPrice) / currentPrice) * 100);
                            const volumeInMillions = level.total_liquidation / 1000000;
                            const clusterStrength = level.cluster_strength || 'medium';
                            const isNearPrice = distancePercent <= 5; // Within 5%
                            
                            return (
                                <div 
                                    key={index} 
                                    className={`levels-table-row ${isAboveCurrent ? 'above-current' : 'below-current'} ${isNearPrice ? 'near-price' : ''} cluster-${clusterStrength}`}
                                >
                                    <div className="col-price">
                                        <div className="price-value">
                                            ${level.price?.toFixed(2)}
                                        </div>
                                        {isNearPrice && <div className="near-indicator">🎯 NEAR</div>}
                                    </div>
                                    <div className="col-distance">
                                        <div className="distance-value">
                                            {distancePercent.toFixed(1)}%
                                        </div>
                                        <div className="distance-label">
                                            {isAboveCurrent ? 'Above' : 'Below'}
                                        </div>
                                    </div>
                                    <div className="col-volume">
                                        <div className="volume-value">
                                            ${volumeInMillions.toFixed(1)}M
                                        </div>
                                        {level.leverage && (
                                            <div className="leverage-info">
                                                {level.leverage}x
                                            </div>
                                        )}
                                    </div>
                                    <div className="col-strength">
                                        <div className="strength-indicator">
                                            <div className={`strength-bar strength-${clusterStrength}`}></div>
                                            <span className="strength-text">
                                                {clusterStrength === 'very_high' ? 'VERY HIGH' : 
                                                 clusterStrength === 'high' ? 'HIGH' : 
                                                 clusterStrength === 'medium' ? 'MED' : 'LOW'}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="col-direction">
                                        <div className={`direction-indicator ${isAboveCurrent ? 'resistance' : 'support'}`}>
                                            <span className="direction-text">
                                                {isAboveCurrent ? '🔴 RESIST' : '🟢 SUPPORT'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                    
                    <div className="cluster-summary">
                        <div className="summary-text">
                            Showing closest {Math.min(15, levels.length)} liquidation clusters to current price
                        </div>
                    </div>
                </div>

                <div className="exchanges-breakdown">
                    <h4>Exchange Sources</h4>
                    <div className="exchanges-grid">
                        {heatmapData.exchanges && Object.entries(heatmapData.exchanges).map(([exchange, data]) => (
                            <div key={exchange} className="exchange-item">
                                <div className="exchange-name">
                                    {exchange.charAt(0).toUpperCase() + exchange.slice(1)}
                                </div>
                                <div className="exchange-data">
                                    {data.liquidation_levels ? `${data.liquidation_levels.length} levels` : 'N/A'}
                                </div>
                                <div className={`exchange-source ${data.source === 'synthetic' ? 'synthetic' : 'real'}`}>
                                    {data.source === 'synthetic' ? 'SIM' : 'LIVE'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                
                <div className="data-source">
                    Source: {heatmapData.source} | Updated: {new Date(heatmapData.timestamp).toLocaleTimeString()}
                    | Timeframe: {heatmapData.timeframe}
                </div>
            </div>
        );
    };

    const renderOpenInterestDetailed = () => {
        const oiData = smartMoneyData?.open_interest_detailed;
        
        if (!oiData || !oiData.exchanges_detail) {
            return <div className="no-data">No detailed open interest data available</div>;
        }

        const exchanges = Object.entries(oiData.exchanges_detail);
        const totalOI = oiData.total_open_interest || 0;
        const totalVolume = oiData.total_volume_24h || 0;
        const metrics = oiData.market_metrics || {};

        return (
            <div className="open-interest-detailed">
                <div className="oi-header-enhanced">
                    <div className="header-left">
                        <h3>Open Interest - {oiData.display_name}</h3>
                        <div className="current-price-large">
                            Current Price: ${oiData.current_price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                    </div>
                    <div className="header-right">
                        <div className="oi-change">
                            <span className="change-label">24h Change:</span>
                            <span className={`change-value ${oiData.oi_change_24h >= 0 ? 'positive' : 'negative'}`}>
                                {oiData.oi_change_24h?.toFixed(2)}%
                            </span>
                        </div>
                    </div>
                </div>

                <div className="oi-summary-cards">
                    <div className="summary-card total-oi">
                        <div className="card-title">Total Open Interest</div>
                        <div className="card-value">
                            ${(totalOI / 1000000)?.toFixed(2)}M
                        </div>
                        <div className="card-subtitle">Across {exchanges.length} Exchanges</div>
                    </div>

                    <div className="summary-card total-volume">
                        <div className="card-title">24h Volume</div>
                        <div className="card-value">
                            ${(totalVolume / 1000000)?.toFixed(2)}M
                        </div>
                        <div className="card-subtitle">
                            OI/Vol: {(metrics.oi_volume_ratio * 100)?.toFixed(1)}%
                        </div>
                    </div>

                    <div className="summary-card avg-funding">
                        <div className="card-title">Avg Funding Rate</div>
                        <div className={`card-value ${metrics.avg_funding_rate >= 0 ? 'positive' : 'negative'}`}>
                            {(metrics.avg_funding_rate * 100)?.toFixed(4)}%
                        </div>
                        <div className="card-subtitle">Weighted Average</div>
                    </div>

                    <div className="summary-card liquidations">
                        <div className="card-title">24h Liquidations</div>
                        <div className="card-value">
                            ${(metrics.liquidations_24h / 1000000)?.toFixed(1)}M
                        </div>
                        <div className="card-subtitle">Est. Volume</div>
                    </div>
                </div>

                <div className="exchanges-table">
                    <div className="table-header">
                        <h4>Exchange Breakdown</h4>
                    </div>

                    <div className="table-headers">
                        <div className="col-exchange">Exchange</div>
                        <div className="col-oi">Open Interest</div>
                        <div className="col-share">OI Share</div>
                        <div className="col-volume">24h Volume</div>
                        <div className="col-funding">Funding Rate</div>
                        <div className="col-trades">Trades</div>
                        <div className="col-source">Source</div>
                    </div>

                    {exchanges.map(([exchange, data]) => {
                        if (!data || typeof data.open_interest !== 'number') return null;
                        
                        const oiShare = data.oi_share || 0;
                        const isSynthetic = data.source === 'synthetic';
                        
                        return (
                            <div key={exchange} className="table-row">
                                <div className="col-exchange">
                                    <div className="exchange-info">
                                        <span className="exchange-name">
                                            {exchange.charAt(0).toUpperCase() + exchange.slice(1)}
                                        </span>
                                        {isSynthetic && <span className="synthetic-badge">SIM</span>}
                                    </div>
                                </div>

                                <div className="col-oi">
                                    <div className="oi-amount">
                                        ${(data.open_interest / 1000000).toFixed(2)}M
                                    </div>
                                </div>

                                <div className="col-share">
                                    <div className="share-container">
                                        <div className="share-percentage">
                                            {oiShare.toFixed(1)}%
                                        </div>
                                        <div className="share-bar-container">
                                            <div 
                                                className="share-bar"
                                                style={{ width: `${oiShare}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="col-volume">
                                    <div className="volume-amount">
                                        ${(data.volume_24h / 1000000).toFixed(2)}M
                                    </div>
                                </div>

                                <div className="col-funding">
                                    <span className={`funding-rate ${data.funding_rate >= 0 ? 'positive' : 'negative'}`}>
                                        {(data.funding_rate * 100).toFixed(4)}%
                                    </span>
                                </div>

                                <div className="col-trades">
                                    <div className="trades-count">
                                        {data.trades_count_24h?.toLocaleString()}
                                    </div>
                                </div>

                                <div className="col-source">
                                    <span className={`source-badge ${data.source === 'synthetic' ? 'synthetic' : 'live'}`}>
                                        {data.source === 'synthetic' ? 'SIM' : 'API'}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
                
                <div className="data-source">
                    Source: {oiData.source} | Updated: {new Date(oiData.timestamp).toLocaleTimeString()}
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="enhanced-smart-money-panel loading">
                <div className="loading-spinner"></div>
                <div>Loading Enhanced Smart Money data...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="enhanced-smart-money-panel error">
                <div className="error-message">⚠️ {error}</div>
                <button onClick={fetchEnhancedSmartMoneyData} className="retry-btn">
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="enhanced-smart-money-panel">
            <div className="panel-header-enhanced">
                <div className="header-left">
                    <h2>🔥 Smart Money Analytics</h2>
                    <div className="header-subtitle">
                        Coinglass-style liquidation heatmaps and open interest analysis
                    </div>
                </div>
                <div className="header-right">
                    <div className="controls-container">
                        {renderTimeframeSelector()}
                        {renderSymbolSelector()}
                    </div>
                </div>
            </div>

            <div className="tab-navigation-enhanced">
                <button 
                    className={`tab-enhanced ${activeTab === 'liquidation_heatmap' ? 'active' : ''}`}
                    onClick={() => setActiveTab('liquidation_heatmap')}
                >
                    🔥 2D Liquidation Heatmap
                </button>
                <button 
                    className={`tab-enhanced ${activeTab === 'open_interest_detailed' ? 'active' : ''}`}
                    onClick={() => setActiveTab('open_interest_detailed')}
                >
                    📊 Open Interest Details
                </button>
            </div>

            <div className="tab-content-enhanced">
                {activeTab === 'liquidation_heatmap' && renderLiquidationHeatmap2D()}
                {activeTab === 'open_interest_detailed' && renderOpenInterestDetailed()}
            </div>
        </div>
    );
};

export default EnhancedSmartMoneyPanel;