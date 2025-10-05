import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TradingInterface = () => {
    const [account, setAccount] = useState(null);
    const [positions, setPositions] = useState([]);
    const [tradeHistory, setTradeHistory] = useState([]);
    const [symbols, setSymbols] = useState([]);
    const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    // Order form state
    const [orderForm, setOrderForm] = useState({
        side: 'buy',
        orderType: 'market',
        quantity: '',
        price: '',
        leverage: 1,
        stopLoss: '',
        takeProfit: ''
    });
    
    // AI Analysis state
    const [aiAnalysis, setAiAnalysis] = useState(null);
    const [analysisLoading, setAnalysisLoading] = useState(false);
    const [showAiPanel, setShowAiPanel] = useState(false);
    
    // Current prices (from real-time data)
    const [currentPrices, setCurrentPrices] = useState({});

    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

    useEffect(() => {
        fetchTradingData();
        fetchSymbols();
        // Set up real-time price updates
        const priceInterval = setInterval(fetchCurrentPrices, 2000);
        return () => clearInterval(priceInterval);
    }, []);

    const fetchTradingData = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };
            
            // Fetch account, positions, and history in parallel
            const [accountResponse, positionsResponse, historyResponse] = await Promise.all([
                axios.get(`${BACKEND_URL}/api/trading/account`, { headers }),
                axios.get(`${BACKEND_URL}/api/trading/positions`, { headers }),
                axios.get(`${BACKEND_URL}/api/trading/history?limit=20`, { headers })
            ]);
            
            if (accountResponse.data.status === 'success') {
                setAccount(accountResponse.data.account);
            }
            
            if (positionsResponse.data.status === 'success') {
                setPositions(positionsResponse.data.positions);
            }
            
            if (historyResponse.data.status === 'success') {
                setTradeHistory(historyResponse.data.history);
            }
            
        } catch (err) {
            console.error('Trading data fetch error:', err);
            setError('Failed to load trading data');
        } finally {
            setLoading(false);
        }
    };

    const fetchSymbols = async () => {
        try {
            const response = await axios.get(`${BACKEND_URL}/api/trading/symbols`);
            if (response.data.status === 'success') {
                setSymbols(response.data.symbols);
            }
        } catch (err) {
            console.error('Symbols fetch error:', err);
        }
    };

    const fetchCurrentPrices = async () => {
        try {
            // Get prices for all Top 30 symbols from real-time API
            const symbolList = symbols.map(s => s.symbol).join(',');
            if (symbolList) {
                const response = await axios.get(`${BACKEND_URL}/api/realtime/latest?symbols=${symbolList}`);
                if (response.data.status === 'success') {
                    setCurrentPrices(response.data.data);
                    
                    // Update positions with current prices for real-time PnL
                    setPositions(prevPositions => 
                        prevPositions.map(position => ({
                            ...position,
                            current_price: response.data.data[position.symbol]?.price || position.mark_price
                        }))
                    );
                }
            }
        } catch (err) {
            console.error('Price fetch error:', err);
        }
    };

    const placeOrder = async () => {
        try {
            if (!orderForm.quantity || parseFloat(orderForm.quantity) <= 0) {
                setError('Please enter a valid quantity');
                return;
            }

            setLoading(true);
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const orderData = {
                symbol: selectedSymbol,
                side: orderForm.side,
                order_type: orderForm.orderType,
                quantity: parseFloat(orderForm.quantity),
                price: orderForm.price ? parseFloat(orderForm.price) : null,
                leverage: parseInt(orderForm.leverage),
                stop_loss: orderForm.stopLoss ? parseFloat(orderForm.stopLoss) : null,
                take_profit: orderForm.takeProfit ? parseFloat(orderForm.takeProfit) : null
            };

            const response = await axios.post(`${BACKEND_URL}/api/trading/order`, orderData, { headers });
            
            if (response.data.status === 'success' && response.data.result.success) {
                // Reset form
                setOrderForm({
                    ...orderForm,
                    quantity: '',
                    price: '',
                    stopLoss: '',
                    takeProfit: ''
                });
                
                // Refresh data
                await fetchTradingData();
                setError(null);
                
            } else {
                setError(response.data.result?.error || 'Order failed');
            }
            
        } catch (err) {
            console.error('Order placement error:', err);
            setError(err.response?.data?.message || 'Failed to place order');
        } finally {
            setLoading(false);
        }
    };

    const getAiAnalysis = async (symbol, context = "") => {
        try {
            setAnalysisLoading(true);
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const response = await axios.post(`${BACKEND_URL}/api/ai-trading/analyze`, {
                symbol: symbol,
                context: context
            }, { headers });

            if (response.data.status === 'success') {
                setAiAnalysis(response.data.recommendation);
                setShowAiPanel(true);
                
                // Auto-fill order form with AI suggestions
                if (response.data.recommendation.entry_price) {
                    setOrderForm(prev => ({
                        ...prev,
                        side: response.data.recommendation.action === 'buy' ? 'buy' : 'sell',
                        quantity: (response.data.recommendation.position_size / 100).toString(),
                        leverage: response.data.recommendation.leverage,
                        price: response.data.recommendation.entry_price?.toString() || '',
                        stopLoss: response.data.recommendation.stop_loss?.toString() || '',
                        takeProfit: response.data.recommendation.take_profit?.toString() || ''
                    }));
                }
                
                setError(null);
            } else {
                setError('AI Analysis failed');
            }
        } catch (err) {
            console.error('AI Analysis error:', err);
            setError('Failed to get AI analysis');
        } finally {
            setAnalysisLoading(false);
        }
    };

    const closePosition = async (positionId, percentage = 100) => {
        try {
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const response = await axios.post(`${BACKEND_URL}/api/trading/position/close`, {
                position_id: positionId,
                close_percentage: percentage
            }, { headers });

            if (response.data.status === 'success' && response.data.result.success) {
                await fetchTradingData();
                setError(null);
                
                // Show success message
                const result = response.data.result;
                const pnlText = result.net_pnl >= 0 ? `Gewinn: $${result.net_pnl.toFixed(2)}` : `Verlust: $${Math.abs(result.net_pnl).toFixed(2)}`;
                alert(`Position ${percentage}% geschlossen\n${pnlText}`);
            } else {
                setError(response.data.result?.error || 'Position schließen fehlgeschlagen');
            }
            
        } catch (err) {
            console.error('Close position error:', err);
            setError(err.response?.data?.message || 'Fehler beim Schließen der Position');
        }
    };

    const modifyPositionMargin = async (positionId, action, amount) => {
        try {
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const response = await axios.post(`${BACKEND_URL}/api/trading/position/margin`, {
                position_id: positionId,
                action: action,
                amount: parseFloat(amount)
            }, { headers });

            if (response.data.status === 'success' && response.data.result.success) {
                await fetchTradingData();
                setError(null);
            } else {
                setError(response.data.result?.error || 'Margin modification failed');
            }
            
        } catch (err) {
            console.error('Margin modification error:', err);
            setError(err.response?.data?.message || 'Failed to modify margin');
        }
    };

    const formatNumber = (num, precision = 2) => {
        return parseFloat(num).toLocaleString('de-DE', {
            minimumFractionDigits: precision,
            maximumFractionDigits: precision
        });
    };

    const formatCurrency = (num) => {
        return `$${formatNumber(num, 2)}`;
    };

    const getCurrentPrice = (symbol) => {
        // Try real-time price first, then fallback to position mark price
        const realTimePrice = currentPrices[symbol]?.price;
        if (realTimePrice && realTimePrice > 0) {
            return realTimePrice;
        }
        
        // Fallback to mark price from positions if available
        const position = positions.find(p => p.symbol === symbol);
        if (position && position.mark_price && position.mark_price > 0) {
            return position.mark_price;
        }
        
        return 0;
    };

    const calculatePositionValue = (position) => {
        const currentPrice = getCurrentPrice(position.symbol);
        return Math.abs(position.size) * currentPrice;
    };

    const calculateUnrealizedPnL = (position) => {
        const currentPrice = getCurrentPrice(position.symbol);
        if (!currentPrice) return 0;
        
        if (position.side === 'long') {
            return (currentPrice - position.entry_price) * Math.abs(position.size);
        } else {
            return (position.entry_price - currentPrice) * Math.abs(position.size);
        }
    };

    if (loading && !account) {
        return (
            <div className="trading-interface loading">
                <div className="loading-spinner"></div>
                <p>Trading Interface laden...</p>
            </div>
        );
    }

    return (
        <div className="trading-interface">
            {error && (
                <div className="error-banner">
                    <span className="error-text">{error}</span>
                    <button onClick={() => setError(null)} className="error-close">×</button>
                </div>
            )}

            {/* Account Overview */}
            <div className="account-overview">
                <div className="account-header">
                    <h2>Paper Trading Account</h2>
                    <div className="account-stats">
                        <div className="stat-item">
                            <span className="stat-label">Balance</span>
                            <span className="stat-value balance">{formatCurrency(account?.balance || 0)}</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Equity</span>
                            <span className="stat-value equity">{formatCurrency(account?.equity || 0)}</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Unrealized PnL</span>
                            <span className={`stat-value pnl ${(account?.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                                {formatCurrency(account?.unrealized_pnl || 0)}
                            </span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Free Margin</span>
                            <span className="stat-value margin">{formatCurrency(account?.free_margin || 0)}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Trading Layout */}
            <div className="trading-layout">
                
                {/* Order Panel */}
                <div className="order-panel">
                    <div className="panel-header">
                        <h3>Order platzieren</h3>
                    </div>
                    
                    <div className="symbol-selector">
                        <label>Symbol</label>
                        <select 
                            value={selectedSymbol} 
                            onChange={(e) => setSelectedSymbol(e.target.value)}
                            className="symbol-select"
                        >
                            {symbols.map(symbol => (
                                <option key={symbol.symbol} value={symbol.symbol}>
                                    {symbol.display_name} ({symbol.symbol})
                                </option>
                            ))}
                        </select>
                        <div className="current-price">
                            Preis: ${formatNumber(getCurrentPrice(selectedSymbol), 4)}
                        </div>
                        <button 
                            onClick={() => getAiAnalysis(selectedSymbol)}
                            disabled={analysisLoading}
                            className="ai-analysis-btn"
                        >
                            {analysisLoading ? 'Analysiere...' : '🤖 KI Analyse'}
                        </button>
                    </div>

                    <div className="order-form">
                        <div className="side-selector">
                            <button 
                                className={`side-btn buy ${orderForm.side === 'buy' ? 'active' : ''}`}
                                onClick={() => setOrderForm({...orderForm, side: 'buy'})}
                            >
                                Long / Buy
                            </button>
                            <button 
                                className={`side-btn sell ${orderForm.side === 'sell' ? 'active' : ''}`}
                                onClick={() => setOrderForm({...orderForm, side: 'sell'})}
                            >
                                Short / Sell
                            </button>
                        </div>

                        <div className="order-type-selector">
                            <select 
                                value={orderForm.orderType} 
                                onChange={(e) => setOrderForm({...orderForm, orderType: e.target.value})}
                                className="order-type-select"
                            >
                                <option value="market">Market Order</option>
                                <option value="limit">Limit Order</option>
                            </select>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>Quantity</label>
                                <input 
                                    type="number"
                                    value={orderForm.quantity}
                                    onChange={(e) => setOrderForm({...orderForm, quantity: e.target.value})}
                                    placeholder="0.00"
                                    className="quantity-input"
                                />
                            </div>
                            <div className="form-group">
                                <label>Leverage</label>
                                <select 
                                    value={orderForm.leverage} 
                                    onChange={(e) => setOrderForm({...orderForm, leverage: e.target.value})}
                                    className="leverage-select"
                                >
                                    {[1, 2, 3, 5, 10, 20, 25, 50, 75, 100].map(lev => (
                                        <option key={lev} value={lev}>{lev}x</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {orderForm.orderType === 'limit' && (
                            <div className="form-group">
                                <label>Limit Price</label>
                                <input 
                                    type="number"
                                    value={orderForm.price}
                                    onChange={(e) => setOrderForm({...orderForm, price: e.target.value})}
                                    placeholder="0.00"
                                    className="price-input"
                                />
                            </div>
                        )}

                        <div className="form-row">
                            <div className="form-group">
                                <label>Stop Loss</label>
                                <input 
                                    type="number"
                                    value={orderForm.stopLoss}
                                    onChange={(e) => setOrderForm({...orderForm, stopLoss: e.target.value})}
                                    placeholder="Optional"
                                    className="stop-loss-input"
                                />
                            </div>
                            <div className="form-group">
                                <label>Take Profit</label>
                                <input 
                                    type="number"
                                    value={orderForm.takeProfit}
                                    onChange={(e) => setOrderForm({...orderForm, takeProfit: e.target.value})}
                                    placeholder="Optional"
                                    className="take-profit-input"
                                />
                            </div>
                        </div>

                        <button 
                            onClick={placeOrder}
                            disabled={loading}
                            className={`place-order-btn ${orderForm.side}`}
                        >
                            {loading ? 'Placing...' : `${orderForm.side === 'buy' ? 'Long' : 'Short'} ${selectedSymbol}`}
                        </button>
                    </div>
                    {/* AI Analysis Panel */}
                    {showAiPanel && aiAnalysis && (
                        <div className="ai-analysis-panel">
                            <div className="ai-panel-header">
                                <h4>🤖 KI Analyse: {selectedSymbol}</h4>
                                <button onClick={() => setShowAiPanel(false)} className="close-btn">×</button>
                            </div>
                            
                            <div className="ai-recommendation">
                                <div className="recommendation-main">
                                    <span className={`action-badge ${aiAnalysis.action}`}>
                                        {aiAnalysis.action.toUpperCase()}
                                    </span>
                                    <span className="confidence-score">
                                        Konfidenz: {(aiAnalysis.confidence * 100).toFixed(1)}%
                                    </span>
                                </div>
                                
                                <div className="trade-details">
                                    <div className="detail-item">
                                        <span>Trade Typ:</span>
                                        <span>{aiAnalysis.trade_type}</span>
                                    </div>
                                    <div className="detail-item">
                                        <span>Position Size:</span>
                                        <span>{aiAnalysis.position_size}%</span>
                                    </div>
                                    <div className="detail-item">
                                        <span>Leverage:</span>
                                        <span>{aiAnalysis.leverage}x</span>
                                    </div>
                                    {aiAnalysis.entry_price && (
                                        <div className="detail-item">
                                            <span>Entry:</span>
                                            <span>${formatNumber(aiAnalysis.entry_price, 4)}</span>
                                        </div>
                                    )}
                                    {aiAnalysis.stop_loss && (
                                        <div className="detail-item">
                                            <span>Stop Loss:</span>
                                            <span>${formatNumber(aiAnalysis.stop_loss, 4)}</span>
                                        </div>
                                    )}
                                    {aiAnalysis.take_profit && (
                                        <div className="detail-item">
                                            <span>Take Profit:</span>
                                            <span>${formatNumber(aiAnalysis.take_profit, 4)}</span>
                                        </div>
                                    )}
                                    {aiAnalysis.risk_reward_ratio && (
                                        <div className="detail-item">
                                            <span>R/R Ratio:</span>
                                            <span>{aiAnalysis.risk_reward_ratio.toFixed(2)}</span>
                                        </div>
                                    )}
                                </div>
                                
                                <div className="ai-reasoning">
                                    <h5>Analyse:</h5>
                                    <p>{aiAnalysis.reasoning}</p>
                                </div>
                                
                                <div className="market-conditions">
                                    <h5>Marktbedingungen:</h5>
                                    <p>{aiAnalysis.market_conditions}</p>
                                </div>
                                
                                <div className="risk-assessment">
                                    <h5>Risikobewertung:</h5>
                                    <p>{aiAnalysis.risk_assessment}</p>
                                </div>
                                
                                {aiAnalysis.probability_analysis && (
                                    <div className="probability-analysis">
                                        <h5>Wahrscheinlichkeitsanalyse:</h5>
                                        <div className="prob-details">
                                            <div className="prob-item">
                                                <span>Gewinnwahrscheinlichkeit:</span>
                                                <span>{(aiAnalysis.probability_analysis.win_probability * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="prob-item">
                                                <span>Erwarteter Return:</span>
                                                <span>{aiAnalysis.probability_analysis.expected_return?.toFixed(2)}%</span>
                                            </div>
                                            <div className="prob-item">
                                                <span>Max Drawdown:</span>
                                                <span>{aiAnalysis.probability_analysis.max_drawdown_risk?.toFixed(2)}%</span>
                                            </div>
                                            <div className="prob-item">
                                                <span>Zeithorizont:</span>
                                                <span>{aiAnalysis.probability_analysis.time_horizon}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                                
                                <div className="ai-actions">
                                    <button 
                                        onClick={() => {
                                            // Auto-apply AI recommendations to order form
                                            setOrderForm(prev => ({
                                                ...prev,
                                                side: aiAnalysis.action === 'buy' ? 'buy' : 'sell',
                                                quantity: (aiAnalysis.position_size / 100).toString(),
                                                leverage: aiAnalysis.leverage,
                                                stopLoss: aiAnalysis.stop_loss?.toString() || '',
                                                takeProfit: aiAnalysis.take_profit?.toString() || ''
                                            }));
                                            setShowAiPanel(false);
                                        }}
                                        className="apply-ai-btn"
                                    >
                                        KI Empfehlung anwenden
                                    </button>
                                    <button 
                                        onClick={() => getAiAnalysis(selectedSymbol, "Provide updated analysis")}
                                        disabled={analysisLoading}
                                        className="refresh-analysis-btn"
                                    >
                                        Analyse aktualisieren
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Positions Panel */}
                <div className="positions-panel">
                    <div className="panel-header">
                        <h3>Offene Positionen ({positions.length})</h3>
                        <button onClick={fetchTradingData} className="refresh-btn">
                            ↻
                        </button>
                    </div>

                    {positions.length === 0 ? (
                        <div className="no-positions">
                            <p>Keine offenen Positionen</p>
                        </div>
                    ) : (
                        <div className="positions-list">
                            {positions.map(position => (
                                <div key={position.position_id} className={`position-card ${position.side}`}>
                                    <div className="position-header">
                                        <div className="position-symbol">
                                            <span className="symbol-name">{position.symbol}</span>
                                            <span className={`side-badge ${position.side}`}>{position.side.toUpperCase()}</span>
                                        </div>
                                        <div className="position-pnl">
                                            <span className={`pnl-value ${calculateUnrealizedPnL(position) >= 0 ? 'profit' : 'loss'}`}>
                                                {formatCurrency(calculateUnrealizedPnL(position))}
                                            </span>
                                        </div>
                                    </div>
                                    
                                    <div className="position-details">
                                        <div className="detail-row">
                                            <span>Size:</span>
                                            <span>{formatNumber(Math.abs(position.size), 4)}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>Entry:</span>
                                            <span>${formatNumber(position.entry_price, 4)}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>Mark Price:</span>
                                            <span>${formatNumber(getCurrentPrice(position.symbol), 4)}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>Leverage:</span>
                                            <span>{position.leverage}x</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>Margin:</span>
                                            <span>{formatCurrency(position.margin)}</span>
                                        </div>
                                        <div className="detail-row">
                                            <span>Liquidation:</span>
                                            <span className="liquidation-price">${formatNumber(position.liquidation_price, 4)}</span>
                                        </div>
                                    </div>

                                    <div className="position-actions">
                                        <button 
                                            onClick={() => {
                                                const amount = prompt('Margin hinzufügen ($):');
                                                if (amount && parseFloat(amount) > 0) {
                                                    modifyPositionMargin(position.position_id, 'add', amount);
                                                }
                                            }}
                                            className="margin-btn add"
                                        >
                                            + Margin
                                        </button>
                                        <button 
                                            onClick={() => {
                                                const amount = prompt('Margin reduzieren ($):');
                                                if (amount && parseFloat(amount) > 0) {
                                                    modifyPositionMargin(position.position_id, 'reduce', amount);
                                                }
                                            }}
                                            className="margin-btn reduce"
                                        >
                                            - Margin
                                        </button>
                                        <button 
                                            onClick={() => {
                                                const percentage = prompt('Position schließen (% von 1-100):', '50');
                                                if (percentage && parseFloat(percentage) > 0) {
                                                    closePosition(position.position_id, parseFloat(percentage));
                                                }
                                            }}
                                            className="close-btn partial"
                                        >
                                            Position schließen
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Trade History Panel */}
                <div className="history-panel">
                    <div className="panel-header">
                        <h3>Trade History</h3>
                    </div>
                    
                    {tradeHistory.length === 0 ? (
                        <div className="no-history">
                            <p>Keine Trades vorhanden</p>
                        </div>
                    ) : (
                        <div className="history-list">
                            {tradeHistory.map(trade => (
                                <div key={trade.order_id} className="history-item">
                                    <div className="history-main">
                                        <span className="trade-symbol">{trade.symbol}</span>
                                        <span className={`trade-side ${trade.side}`}>{trade.side.toUpperCase()}</span>
                                        <span className="trade-quantity">{formatNumber(trade.filled_quantity, 4)}</span>
                                        <span className="trade-price">${formatNumber(trade.filled_price, 4)}</span>
                                        <span className="trade-fee">Fee: ${formatNumber(trade.fee_paid, 4)}</span>
                                    </div>
                                    <div className="history-time">
                                        {new Date(trade.created_at).toLocaleString('de-DE')}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TradingInterface;