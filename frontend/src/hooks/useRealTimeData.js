import { useState, useEffect, useRef } from 'react';
import binanceClient from '../utils/binanceClient';

export const useRealTimeData = (selectedSymbol = 'BTC/USDT') => {
    const [realTimeData, setRealTimeData] = useState({});
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [isConnectionReady, setIsConnectionReady] = useState(false);
    
    const currentSymbolRef = useRef(selectedSymbol);
    const wsRef = useRef(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectTimeoutRef = useRef(null);

    // Initialize Binance WebSocket connection
    useEffect(() => {
        console.log('🔥 Starting Binance EXCLUSIVE integration for:', selectedSymbol);
        setConnectionStatus('connecting');
        
        // Subscribe to real-time price updates from Binance
        const handlePriceUpdate = (priceData) => {
            console.log('📈 Binance EXCLUSIVE price update:', selectedSymbol, `$${priceData.price.toLocaleString()}`, `${priceData.changePercent >= 0 ? '+' : ''}${priceData.changePercent.toFixed(2)}%`);
            
            setRealTimeData(prev => ({
                ...prev,
                [priceData.symbol]: {
                    price: priceData.price,
                    change: priceData.change,
                    change_percent: priceData.changePercent,
                    volume: priceData.volume,
                    high: priceData.high,
                    low: priceData.low,
                    timestamp: priceData.timestamp
                }
            }));
            
            setConnectionStatus('connected');
            setIsConnectionReady(true);
        };

        // Subscribe to Binance WebSocket
        binanceClient.subscribeToPrice(selectedSymbol, handlePriceUpdate);

        // Also fetch initial price immediately
        binanceClient.getCurrentPrice(selectedSymbol)
            .then(initialPrice => {
                if (initialPrice) {
                    handlePriceUpdate(initialPrice);
                    console.log(`💰 Binance EXCLUSIVE initial price for ${selectedSymbol}: $${initialPrice.price.toLocaleString()}`);
                }
            })
            .catch(err => console.error('Initial price fetch error:', err));

        currentSymbolRef.current = selectedSymbol;

        // Cleanup on unmount or symbol change
        return () => {
            console.log('🛑 Cleaning up Binance connection for:', selectedSymbol);
            binanceClient.unsubscribe(selectedSymbol);
        };
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

    // Helper functions for backward compatibility
    const getCurrentPriceCompat = (symbol = selectedSymbol) => realTimeData[symbol]?.price || 0;
    const getPriceChangeCompat = (symbol = selectedSymbol) => realTimeData[symbol]?.change_percent || 0;
    const getVolumeCompat = (symbol = selectedSymbol) => realTimeData[symbol]?.volume || 0;
    const isConnected = () => connectionStatus === 'connected';
    
    const formatPrice = (decimals = 2, symbol = selectedSymbol) => {
        const price = getCurrentPriceCompat(symbol);
        return price.toLocaleString('de-DE', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    };
    
    const formatChange = (symbol = selectedSymbol) => {
        const change = getPriceChangeCompat(symbol);
        return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    };

    return {
        realTimeData,
        connectionStatus,
        isConnectionReady,
        priceData: realTimeData[selectedSymbol] || priceData,
        
        // Original functions (keeping existing behavior)
        getCurrentPrice: getCurrentPriceCompat,
        getPriceChange: getPriceChangeCompat,
        getLastUpdate,
        isLive: (symbol) => {
            const data = realTimeData[symbol];
            if (!data?.timestamp) return false;
            
            const lastUpdate = new Date(data.timestamp);
            const now = new Date();
            return (now - lastUpdate) < 60000; // Live if updated within last minute
        },
        reconnect: connectWebSocket,
        
        // New utility functions
        getVolume: getVolumeCompat,
        isConnected,
        formatPrice,
        formatChange
    };
};