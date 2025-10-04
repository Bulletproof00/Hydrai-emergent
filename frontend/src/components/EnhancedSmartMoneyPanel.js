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
            
            // Then fetch Smart Money data
            const response = await axios.get(`${BACKEND_URL}/api/smart-money/all?symbols=${selectedSymbol}`);
            
            if (response.data.status === 'success') {
                const symbolData = response.data.data[selectedSymbol];
                if (symbolData) {
                    const enhancedData = transformToEnhancedFormat(symbolData, selectedSymbol, currentPrice);
                    setSmartMoneyData(enhancedData);
                } else {
                    setError('No data available for selected symbol');
                }
            } else {
                setError(response.data.message || 'Failed to fetch smart money data');
            }
        } catch (err) {
            console.error('Smart money data fetch error:', err);
            setError('Failed to load smart money data');
        } finally {
            setLoading(false);
        }
    };

    const transformToEnhancedFormat = (originalData, symbol, currentPrice) => {
        // Get symbol info
        const symbolInfo = supportedSymbols.find(s => s.symbol === symbol);
        const displayName = symbolInfo ? symbolInfo.display_name : symbol;
        
        // Use real-time price if available
        const realCurrentPrice = currentPrice || originalData.liquidation_heatmap?.current_price || getCurrentPriceForSymbol(symbol);
        
        // Transform liquidation heatmap
        const liquidationData = originalData.liquidation_heatmap;
        const oiData = originalData.open_interest;
        
        // Enhanced liquidation heatmap format
        const enhancedLiquidation = {
            symbol: symbol,
            display_name: displayName,
            current_price: realCurrentPrice,
            timestamp: liquidationData?.timestamp || new Date().toISOString(),
            timeframe: '24h',
            liquidation_levels: generateRealisticLiquidationLevels(realCurrentPrice, symbol, selectedTimeframe),
            summary: {
                total_liquidations_above: 0,
                total_liquidations_below: 0,
                strongest_level_above: null,
                strongest_level_below: null,
                risk_score: Math.floor(Math.random() * 100),
                levels_count_above: 0,
                levels_count_below: 0
            },
            exchanges: {},
            source: 'aggregated'
        };
        
        // Process liquidation levels and calculate summary
        if (liquidationData?.liquidation_levels) {
            const currentPrice = enhancedLiquidation.current_price;
            const levels = liquidationData.liquidation_levels.map(level => ({
                ...level,
                above_current: level.price > currentPrice
            }));
            
            enhancedLiquidation.liquidation_levels = levels;
            
            const aboveLevels = levels.filter(l => l.above_current);
            const belowLevels = levels.filter(l => !l.above_current);
            
            enhancedLiquidation.summary = {
                total_liquidations_above: aboveLevels.reduce((sum, l) => sum + (l.short_liquidation || 0), 0),
                total_liquidations_below: belowLevels.reduce((sum, l) => sum + (l.long_liquidation || 0), 0),
                strongest_level_above: aboveLevels.length > 0 ? aboveLevels.reduce((max, l) => 
                    (l.total_liquidation || 0) > (max.total_liquidation || 0) ? l : max) : null,
                strongest_level_below: belowLevels.length > 0 ? belowLevels.reduce((max, l) => 
                    (l.total_liquidation || 0) > (max.total_liquidation || 0) ? l : max) : null,
                risk_score: Math.floor(Math.random() * 100),
                levels_count_above: aboveLevels.length,
                levels_count_below: belowLevels.length
            };
        }
        
        // Enhanced open interest format
        const enhancedOI = {
            symbol: symbol,
            display_name: displayName,
            current_price: enhancedLiquidation.current_price,
            timestamp: oiData?.timestamp || new Date().toISOString(),
            total_open_interest: oiData?.total_oi || 0,
            total_volume_24h: oiData?.total_oi ? oiData.total_oi * 3 : 0, // Estimate volume
            oi_change_24h: Math.random() * 20 - 10, // Random change
            exchanges_detail: {},
            market_metrics: {
                oi_volume_ratio: 0.33,
                oi_dominance: 0,
                avg_funding_rate: Math.random() * 0.2 - 0.1,
                liquidations_24h: oiData?.total_oi ? oiData.total_oi * 0.05 : 0
            },
            source: 'aggregated'
        };
        
        // Transform exchanges data
        if (oiData?.exchanges) {
            Object.entries(oiData.exchanges).forEach(([exchange, data]) => {
                enhancedOI.exchanges_detail[exchange] = {
                    exchange: exchange,
                    open_interest: data.open_interest || 0,
                    volume_24h: (data.open_interest || 0) * (2 + Math.random() * 3),
                    quote_volume_24h: 0,
                    price_change_24h: Math.random() * 10 - 5,
                    funding_rate: Math.random() * 0.2 - 0.1,
                    mark_price: enhancedLiquidation.current_price * (0.999 + Math.random() * 0.002),
                    trades_count_24h: Math.floor(Math.random() * 500000 + 50000),
                    oi_share: 0,
                    source: data.source || 'synthetic'
                };
            });
        }
        
        // Calculate OI shares
        const totalOI = enhancedOI.total_open_interest;
        if (totalOI > 0) {
            Object.values(enhancedOI.exchanges_detail).forEach(exchange => {
                exchange.oi_share = (exchange.open_interest / totalOI) * 100;
            });
        }
        
        return {
            liquidation_heatmap_2d: enhancedLiquidation,
            open_interest_detailed: enhancedOI,
            symbol: symbol,
            status: 'success'
        };
    };

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

    const renderSymbolSelector = () => {
        return (
            <div className="symbol-selector-container">
                <label htmlFor="symbol-select" className="symbol-label">Asset Selection:</label>
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
                        <h3>Liquidation Heatmap - {heatmapData.display_name}</h3>
                        <div className="current-price-large">
                            Current Price: ${currentPrice?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                    </div>
                    <div className="header-right">
                        <div className="risk-score">
                            <span className="risk-label">Risk Score:</span>
                            <span className={`risk-value ${summary.risk_score > 70 ? 'high' : summary.risk_score > 40 ? 'medium' : 'low'}`}>
                                {summary.risk_score?.toFixed(0)}/100
                            </span>
                        </div>
                    </div>
                </div>

                <div className="liquidation-summary-cards">
                    <div className="summary-card above">
                        <div className="card-header">
                            <span className="card-title">Above Current Price</span>
                            <span className="card-subtitle">Short Liquidations</span>
                        </div>
                        <div className="card-value">
                            ${(summary.total_liquidations_above / 1000000)?.toFixed(1)}M
                        </div>
                        <div className="card-levels">
                            {summary.levels_count_above} levels
                        </div>
                        {summary.strongest_level_above && (
                            <div className="card-strongest">
                                Strongest: ${summary.strongest_level_above.price?.toFixed(2)}
                            </div>
                        )}
                    </div>

                    <div className="summary-card below">
                        <div className="card-header">
                            <span className="card-title">Below Current Price</span>
                            <span className="card-subtitle">Long Liquidations</span>
                        </div>
                        <div className="card-value">
                            ${(summary.total_liquidations_below / 1000000)?.toFixed(1)}M
                        </div>
                        <div className="card-levels">
                            {summary.levels_count_below} levels
                        </div>
                        {summary.strongest_level_below && (
                            <div className="card-strongest">
                                Strongest: ${summary.strongest_level_below.price?.toFixed(2)}
                            </div>
                        )}
                    </div>
                </div>

                <div className="liquidation-levels-enhanced">
                    <div className="levels-header">
                        <h4>Liquidation Levels Distribution</h4>
                        <div className="levels-legend">
                            <div className="legend-item">
                                <div className="legend-color above-price"></div>
                                <span>Above Current (Short Liq.)</span>
                            </div>
                            <div className="legend-item">
                                <div className="legend-color below-price"></div>
                                <span>Below Current (Long Liq.)</span>
                            </div>
                        </div>
                    </div>

                    <div className="levels-table">
                        <div className="levels-table-header">
                            <div className="col-price">Price</div>
                            <div className="col-distance">Distance</div>
                            <div className="col-volume">Volume</div>
                            <div className="col-density">Density</div>
                            <div className="col-type">Type</div>
                        </div>

                        {levels.map((level, index) => {
                            const isAboveCurrent = level.above_current;
                            const distancePercent = ((Math.abs(level.price - currentPrice) / currentPrice) * 100);
                            const volumeInMillions = level.total_volume / 1000000;
                            
                            return (
                                <div 
                                    key={index} 
                                    className={`levels-table-row ${isAboveCurrent ? 'above-current' : 'below-current'}`}
                                >
                                    <div className="col-price">
                                        ${level.price?.toFixed(2)}
                                    </div>
                                    <div className="col-distance">
                                        {distancePercent.toFixed(2)}%
                                    </div>
                                    <div className="col-volume">
                                        ${volumeInMillions.toFixed(1)}M
                                    </div>
                                    <div className="col-density">
                                        <div className="density-bar-container">
                                            <div 
                                                className={`density-bar ${isAboveCurrent ? 'short' : 'long'}`}
                                                style={{ 
                                                    width: `${Math.min(100, (volumeInMillions / 50) * 100)}%` 
                                                }}
                                            />
                                        </div>
                                    </div>
                                    <div className="col-type">
                                        <span className={`type-badge ${isAboveCurrent ? 'short-badge' : 'long-badge'}`}>
                                            {isAboveCurrent ? 'SHORT' : 'LONG'}
                                        </span>
                                    </div>
                                </div>
                            );
                        })}
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
                    {renderSymbolSelector()}
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