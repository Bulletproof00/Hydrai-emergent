import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SmartMoneyPanel = ({ selectedSymbol }) => {
    const [smartMoneyData, setSmartMoneyData] = useState(null);
    const [activeTab, setActiveTab] = useState('liquidation');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchSmartMoneyData();
        
        // Set up interval for updates every 15 minutes
        const interval = setInterval(fetchSmartMoneyData, 15 * 60 * 1000);
        return () => clearInterval(interval);
    }, [selectedSymbol]);

    const fetchSmartMoneyData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await axios.get(`${BACKEND_URL}/api/smart-money/all?symbols=${selectedSymbol}`);
            
            if (response.data.status === 'success') {
                setSmartMoneyData(response.data.data);
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

    const renderLiquidationHeatmap = () => {
        const symbolData = smartMoneyData?.[selectedSymbol];
        const liquidationData = symbolData?.liquidation_heatmap;
        
        if (!liquidationData || !liquidationData.liquidation_levels) {
            return <div className="no-data">No liquidation data available</div>;
        }

        const levels = liquidationData.liquidation_levels.slice(0, 10); // Show top 10 levels
        const maxLiquidation = Math.max(...levels.map(l => l.total_liquidation));

        return (
            <div className="liquidation-heatmap">
                <div className="heatmap-header">
                    <h3>Liquidation Heatmap</h3>
                    <div className="current-price">
                        Current: ${liquidationData.current_price?.toFixed(2) || 'N/A'}
                    </div>
                </div>
                
                <div className="heatmap-legend">
                    <div className="legend-item long">
                        <span className="color-box long"></span>
                        Long Liquidations
                    </div>
                    <div className="legend-item short">
                        <span className="color-box short"></span>
                        Short Liquidations
                    </div>
                </div>

                <div className="liquidation-levels">
                    {levels.map((level, index) => {
                        const longRatio = level.long_liquidation / maxLiquidation;
                        const shortRatio = level.short_liquidation / maxLiquidation;
                        const isHigh = (longRatio > 0.7 || shortRatio > 0.7);
                        
                        return (
                            <div 
                                key={index} 
                                className={`liquidation-level ${isHigh ? 'high-liquidation' : ''}`}
                            >
                                <div className="level-price">
                                    ${level.price?.toFixed(2)}
                                </div>
                                
                                <div className="liquidation-bars">
                                    <div 
                                        className="long-bar"
                                        style={{ width: `${longRatio * 100}%` }}
                                        title={`Long: $${(level.long_liquidation / 1000000).toFixed(2)}M`}
                                    ></div>
                                    
                                    <div 
                                        className="short-bar"
                                        style={{ width: `${shortRatio * 100}%` }}
                                        title={`Short: $${(level.short_liquidation / 1000000).toFixed(2)}M`}
                                    ></div>
                                </div>
                                
                                <div className="level-amount">
                                    ${((level.total_liquidation || 0) / 1000000).toFixed(1)}M
                                </div>
                            </div>
                        );
                    })}
                </div>
                
                <div className="data-source">
                    Source: {liquidationData.source} | Updated: {new Date(liquidationData.timestamp).toLocaleTimeString()}
                </div>
            </div>
        );
    };

    const renderOpenInterest = () => {
        const symbolData = smartMoneyData?.[selectedSymbol];
        const oiData = symbolData?.open_interest;
        
        if (!oiData || !oiData.exchanges) {
            return <div className="no-data">No open interest data available</div>;
        }

        const exchanges = Object.entries(oiData.exchanges);
        const totalOI = oiData.total_oi || 0;

        return (
            <div className="open-interest">
                <div className="oi-header">
                    <h3>Open Interest</h3>
                    <div className="total-oi">
                        Total: ${(totalOI / 1000000).toFixed(2)}M
                    </div>
                </div>

                <div className="oi-breakdown">
                    {exchanges.map(([exchange, data]) => {
                        if (!data || typeof data.open_interest !== 'number') return null;
                        
                        const percentage = totalOI > 0 ? (data.open_interest / totalOI * 100) : 0;
                        const isSynthetic = data.source === 'synthetic';
                        
                        return (
                            <div key={exchange} className="oi-exchange">
                                <div className="exchange-header">
                                    <span className="exchange-name">
                                        {exchange.charAt(0).toUpperCase() + exchange.slice(1)}
                                        {isSynthetic && <span className="synthetic-badge">SIM</span>}
                                    </span>
                                    <span className="exchange-percentage">
                                        {percentage.toFixed(1)}%
                                    </span>
                                </div>
                                
                                <div className="oi-bar-container">
                                    <div 
                                        className="oi-bar"
                                        style={{ width: `${percentage}%` }}
                                    ></div>
                                </div>
                                
                                <div className="oi-amount">
                                    ${(data.open_interest / 1000000).toFixed(2)}M
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

    const renderFundingRates = () => {
        const symbolData = smartMoneyData?.[selectedSymbol];
        const fundingData = symbolData?.funding_rates;
        
        if (!fundingData || !fundingData.exchanges) {
            return <div className="no-data">No funding rate data available</div>;
        }

        const exchanges = Object.entries(fundingData.exchanges);
        const avgFunding = fundingData.current_funding_rate || 0;

        return (
            <div className="funding-rates">
                <div className="funding-header">
                    <h3>Funding Rates</h3>
                    <div className={`avg-funding ${avgFunding >= 0 ? 'positive' : 'negative'}`}>
                        Avg: {(avgFunding * 100).toFixed(4)}%
                    </div>
                </div>

                <div className="funding-breakdown">
                    {exchanges.map(([exchange, data]) => {
                        if (!data || typeof data.funding_rate !== 'number') return null;
                        
                        const fundingRate = data.funding_rate;
                        const isPositive = fundingRate >= 0;
                        const isSynthetic = data.source === 'synthetic';
                        
                        return (
                            <div key={exchange} className="funding-exchange">
                                <div className="exchange-header">
                                    <span className="exchange-name">
                                        {exchange.charAt(0).toUpperCase() + exchange.slice(1)}
                                        {isSynthetic && <span className="synthetic-badge">SIM</span>}
                                    </span>
                                    <span className={`funding-rate ${isPositive ? 'positive' : 'negative'}`}>
                                        {(fundingRate * 100).toFixed(4)}%
                                    </span>
                                </div>
                                
                                <div className="funding-bar-container">
                                    <div 
                                        className={`funding-bar ${isPositive ? 'positive' : 'negative'}`}
                                        style={{ 
                                            width: `${Math.abs(fundingRate) * 1000}%`, 
                                            maxWidth: '100%' 
                                        }}
                                    ></div>
                                </div>
                                
                                {data.next_funding_time && (
                                    <div className="next-funding">
                                        Next: {new Date(data.next_funding_time).toLocaleTimeString()}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
                
                <div className="funding-info">
                    <div className="info-item">
                        <span className="label">Positive:</span>
                        <span className="value">Shorts pay Longs</span>
                    </div>
                    <div className="info-item">
                        <span className="label">Negative:</span>
                        <span className="value">Longs pay Shorts</span>
                    </div>
                </div>
                
                <div className="data-source">
                    Source: {fundingData.source} | Updated: {new Date(fundingData.timestamp).toLocaleTimeString()}
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="smart-money-panel loading">
                <div className="loading-spinner"></div>
                <div>Loading Smart Money data...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="smart-money-panel error">
                <div className="error-message">⚠️ {error}</div>
                <button onClick={fetchSmartMoneyData} className="retry-btn">
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="smart-money-panel">
            <div className="panel-header">
                <h2>Smart Money Indicators</h2>
                <div className="symbol-focus">
                    Focus: {selectedSymbol}
                </div>
            </div>

            <div className="tab-navigation">
                <button 
                    className={`tab ${activeTab === 'liquidation' ? 'active' : ''}`}
                    onClick={() => setActiveTab('liquidation')}
                >
                    🔥 Liquidation Heatmap
                </button>
                <button 
                    className={`tab ${activeTab === 'openinterest' ? 'active' : ''}`}
                    onClick={() => setActiveTab('openinterest')}
                >
                    📊 Open Interest
                </button>
                <button 
                    className={`tab ${activeTab === 'funding' ? 'active' : ''}`}
                    onClick={() => setActiveTab('funding')}
                >
                    💰 Funding Rates
                </button>
            </div>

            <div className="tab-content">
                {activeTab === 'liquidation' && renderLiquidationHeatmap()}
                {activeTab === 'openinterest' && renderOpenInterest()}
                {activeTab === 'funding' && renderFundingRates()}
            </div>
        </div>
    );
};

export default SmartMoneyPanel;