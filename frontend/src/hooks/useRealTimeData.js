import { useState, useEffect, useRef } from 'react';

export const useRealTimeData = (selectedSymbol) => {
    const [realTimeData, setRealTimeData] = useState({});
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    // Helper function to safely send WebSocket messages
    const safeSendMessage = (message, description = 'message') => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            try {
                wsRef.current.send(JSON.stringify(message));
                console.log(`📡 Sent ${description}:`, message);
                return true;
            } catch (error) {
                console.error(`Failed to send ${description}:`, error);
                return false;
            }
        } else {
            console.warn(`Cannot send ${description}: WebSocket not ready (state: ${wsRef.current?.readyState})`);
            return false;
        }
    };

    const connectWebSocket = () => {
        try {
            const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://smart-trade-ai-28.preview.emergentagent.com';
            const wsUrl = backendUrl.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/realtime';
            
            console.log('Connecting to WebSocket:', wsUrl);
            
            wsRef.current = new WebSocket(wsUrl);
            
            wsRef.current.onopen = () => {
                console.log('✅ Real-time WebSocket connected');
                setConnectionStatus('connected');
                reconnectAttempts.current = 0;
                
                // Small delay to ensure WebSocket is fully ready
                setTimeout(() => {
                    // Subscribe to symbols using safe send
                    if (selectedSymbol) {
                        safeSendMessage({
                            type: 'subscribe',
                            symbols: [selectedSymbol]
                        }, 'initial subscription');
                    }
                }, 100); // 100ms delay
            };
            
            wsRef.current.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    
                    switch (message.type) {
                        case 'initial_data':
                            console.log('📊 Received initial data:', Object.keys(message.data).length, 'symbols');
                            setRealTimeData(message.data);
                            break;
                            
                        case 'price_update':
                            console.log('📈 Price update:', message.symbol, '$' + message.data.price?.toFixed(2));
                            setRealTimeData(prev => ({
                                ...prev,
                                [message.symbol]: message.data
                            }));
                            break;
                            
                        case 'tick':
                            setRealTimeData(prev => ({
                                ...prev,
                                [message.data.symbol]: message.data
                            }));
                            break;
                            
                        case 'pong':
                            // Heartbeat response
                            break;
                            
                        default:
                            console.log('Unknown message type:', message.type);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            wsRef.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setConnectionStatus('error');
            };
            
            wsRef.current.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                setConnectionStatus('disconnected');
                
                // Attempt to reconnect with exponential backoff
                if (reconnectAttempts.current < 5) {
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

    // Subscribe to new symbol when selection changes
    useEffect(() => {
        if (selectedSymbol) {
            safeSendMessage({
                type: 'subscribe',
                symbols: [selectedSymbol]
            }, 'symbol change subscription');
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
        getCurrentPrice,
        getPriceChange,
        getLastUpdate,
        isLive,
        reconnect: connectWebSocket
    };
};