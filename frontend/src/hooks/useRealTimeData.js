import { useState, useEffect, useRef } from 'react';

export const useRealTimeData = (selectedSymbol) => {
    const [realTimeData, setRealTimeData] = useState({});
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [isConnectionReady, setIsConnectionReady] = useState(false);
    const [priceData, setPriceData] = useState({
        price: 0,
        change: 0,
        volume: 0,
        high: 0,
        low: 0
    });
    
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    // Helper function to safely send WebSocket messages
    const safeSendMessage = (message, description = 'message') => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && isConnectionReady) {
            try {
                wsRef.current.send(JSON.stringify(message));
                console.log(`📡 Sent ${description}:`, message);
                return true;
            } catch (error) {
                console.error(`Failed to send ${description}:`, error);
                return false;
            }
        } else {
            const state = wsRef.current?.readyState;
            const stateNames = {
                [WebSocket.CONNECTING]: 'CONNECTING',
                [WebSocket.OPEN]: 'OPEN', 
                [WebSocket.CLOSING]: 'CLOSING',
                [WebSocket.CLOSED]: 'CLOSED'
            };
            console.warn(`Cannot send ${description}: WebSocket not ready (state: ${stateNames[state] || 'UNKNOWN'}, ready: ${isConnectionReady})`);
            return false;
        }
    };

    const connectWebSocket = () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            // Direct Binance WebSocket connection (bypassing slow backend)
            const binanceSymbol = selectedSymbol.replace('/', '').toLowerCase(); // BTC/USDT -> btcusdt
            const wsUrl = `wss://stream.binance.com:9443/ws/${binanceSymbol}@ticker`;
            
            console.log('🔄 Connecting to Binance WebSocket:', binanceSymbol);
            setConnectionStatus('connecting');

            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                console.log('✅ Binance WebSocket connected successfully for', selectedSymbol);
                setConnectionStatus('connected');
                setIsConnectionReady(true);
                reconnectAttempts.current = 0;
                // Binance WebSocket doesn't require subscription messages
            };
            
            wsRef.current.onmessage = (event) => {
                try {
                    const binanceData = JSON.parse(event.data);
                    
                    // Binance ticker format: { s: "BTCUSDT", c: "43250.00", P: "1.25", ... }
                    if (binanceData.s && binanceData.c) {
                        const symbol = selectedSymbol; // Use the selected symbol format (BTC/USDT)
                        const price = parseFloat(binanceData.c);
                        const changePercent = parseFloat(binanceData.P);
                        const volume = parseFloat(binanceData.v);
                        const high = parseFloat(binanceData.h);
                        const low = parseFloat(binanceData.l);
                        
                        console.log('📈 Binance price update:', symbol, '$' + price.toFixed(2), changePercent.toFixed(2) + '%');
                        
                        setRealTimeData(prev => ({
                            ...prev,
                            [symbol]: {
                                price: price,
                                change: (price * changePercent) / 100, // Calculate absolute change
                                change_percent: changePercent,
                                volume: volume,
                                high: high,
                                low: low,
                                timestamp: new Date().toISOString()
                            }
                        }));
                    }
                } catch (error) {
                    console.error('Error parsing Binance WebSocket message:', error);
                }
            };
            
            wsRef.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setConnectionStatus('error');
                setIsConnectionReady(false);
            };
            
            wsRef.current.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                setConnectionStatus('disconnected');
                setIsConnectionReady(false);
                
                // Attempt to reconnect with exponential backoff
                if (reconnectAttempts.current < maxReconnectAttempts) {
                    const delay = Math.pow(2, reconnectAttempts.current) * 1000; // 1s, 2s, 4s, 8s, 16s
                    console.log(`Reconnecting in ${delay}ms... (attempt ${reconnectAttempts.current + 1})`);
                    
                    reconnectTimeoutRef.current = setTimeout(() => {
                        reconnectAttempts.current++;
                        connectWebSocket();
                    }, delay);
                }
            };
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            setConnectionStatus('error');
        }
    };

    // Heartbeat to keep connection alive
    useEffect(() => {
        const heartbeat = setInterval(() => {
            safeSendMessage({ type: 'ping' }, 'heartbeat');
        }, 30000); // Ping every 30 seconds
        
        return () => clearInterval(heartbeat);
    }, []);

    // Initialize WebSocket connection
    useEffect(() => {
        connectWebSocket();
        
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    // Reconnect to new Binance WebSocket when symbol changes
    useEffect(() => {
        if (selectedSymbol && wsRef.current) {
            console.log('🔄 Symbol changed to:', selectedSymbol, '- reconnecting WebSocket');
            wsRef.current.close(); // Close current connection
            setTimeout(() => {
                connectWebSocket(); // Reconnect with new symbol
            }, 100);
        }
    }, [selectedSymbol]);

    // Fallback API polling if WebSocket fails
    useEffect(() => {
        let pollInterval;
        
        if (connectionStatus === 'disconnected' || connectionStatus === 'error') {
            console.log('WebSocket not available, falling back to API polling');
            
            const pollLatestPrices = async () => {
                try {
                    const backendUrl = process.env.REACT_APP_BACKEND_URL;
                    const response = await fetch(`${backendUrl}/api/realtime/latest`);
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        setRealTimeData(data.data);
                        console.log('📊 Fallback API data updated:', Object.keys(data.data).length, 'symbols');
                    }
                } catch (error) {
                    console.error('Fallback API error:', error);
                }
            };
            
            // Poll immediately and then every 5 seconds
            pollLatestPrices();
            pollInterval = setInterval(pollLatestPrices, 5000);
        }
        
        return () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        };
    }, [connectionStatus]);

    const getCurrentPrice = (symbol) => {
        const data = realTimeData[symbol];
        return data?.price || 0;
    };

    const getPriceChange = (symbol) => {
        const data = realTimeData[symbol];
        return {
            change: data?.change || 0,
            changePercent: data?.change_percent || 0,
            isPositive: (data?.change_percent || 0) >= 0
        };
    };

    const getLastUpdate = (symbol) => {
        const data = realTimeData[symbol];
        return data?.timestamp ? new Date(data.timestamp) : null;
    };

    const isLive = (symbol) => {
        const data = realTimeData[symbol];
        if (!data?.timestamp) return false;
        
        const lastUpdate = new Date(data.timestamp);
        const now = new Date();
        return (now - lastUpdate) < 60000; // Live if updated within last minute
    };

    return {
        realTimeData,
        connectionStatus,
        isConnectionReady,
        getCurrentPrice,
        getPriceChange,
        getLastUpdate,
        isLive,
        reconnect: connectWebSocket
    };
};