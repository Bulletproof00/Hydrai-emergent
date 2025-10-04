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

    useEffect(() => {
        fetchSupportedSymbols();
    }, []);

    useEffect(() => {
        if (selectedSymbol) {
            fetchEnhancedSmartMoneyData();
        }
    }, [selectedSymbol]);

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
            
            const response = await axios.get(`${BACKEND_URL}/api/enhanced-smart-money/data/${encodeURIComponent(selectedSymbol)}`);
            
            if (response.data.status === 'success') {
                setSmartMoneyData(response.data.data);
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