import { useState, useEffect, useRef } from 'react';

/**
 * Direct Binance WebSocket Hook for Real-time Prices
 * Bypasses slow backend and connects directly to Binance
 */
export const useBinancePrice = (symbol = 'BTCUSDT') => {
    const [priceData, setPriceData] = useState({
        price: 0,
        change: 0,
        volume: 0,
        high: 0,
        low: 0,
        timestamp: null,
        connected: false
    });
    
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    
    // Convert symbol format (BTC/USDT to BTCUSDT)
    const binanceSymbol = symbol.replace('/', '').toLowerCase();
    
    const connectWebSocket = () => {
        try {
            // Close existing connection
            if (wsRef.current) {
                wsRef.current.close();
            }
            
            // Binance WebSocket URL for 24hr ticker
            const wsUrl = `wss://stream.binance.com:9443/ws/${binanceSymbol}@ticker`;
            
            console.log(`🔄 Connecting to Binance WebSocket: ${binanceSymbol}`);
            
            wsRef.current = new WebSocket(wsUrl);
            
            wsRef.current.onopen = () => {
                console.log(`✅ Binance WebSocket connected for ${binanceSymbol}`);
                setPriceData(prev => ({
                    ...prev,
                    connected: true
                }));
            };
            
            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.e === '24hrTicker') {
                        const newPriceData = {
                            price: parseFloat(data.c), // Current price
                            change: parseFloat(data.P), // 24h change percentage
                            volume: parseFloat(data.v), // 24h volume
                            high: parseFloat(data.h), // 24h high
                            low: parseFloat(data.l), // 24h low
                            timestamp: new Date().toISOString(),
                            connected: true
                        };
                        
                        setPriceData(newPriceData);
                        
                        // Debug log every 10 seconds
                        if (Math.random() < 0.01) {
                            console.log(`💰 ${symbol}: $${newPriceData.price.toLocaleString()} (${newPriceData.change >= 0 ? '+' : ''}${newPriceData.change.toFixed(2)}%)`);
                        }
                    }
                } catch (error) {
                    console.error('Binance WebSocket message error:', error);
                }
            };
            
            wsRef.current.onclose = () => {
                console.log(`🔄 Binance WebSocket closed for ${binanceSymbol}, reconnecting...`);
                setPriceData(prev => ({
                    ...prev,
                    connected: false
                }));
                
                // Reconnect after 3 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    connectWebSocket();
                }, 3000);
            };
            
            wsRef.current.onerror = (error) => {
                console.error('Binance WebSocket error:', error);
                setPriceData(prev => ({
                    ...prev,
                    connected: false
                }));
            };
            
        } catch (error) {
            console.error('Failed to connect to Binance WebSocket:', error);
        }
    };
    
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
    }, [binanceSymbol]);
    
    // Helper functions
    const getCurrentPrice = () => priceData.price;
    const getPriceChange = () => priceData.change;
    const getVolume = () => priceData.volume;
    const isConnected = () => priceData.connected;
    
    const formatPrice = (decimals = 2) => {
        return priceData.price.toLocaleString('de-DE', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    };
    
    const formatChange = () => {
        const change = priceData.change;
        return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    };
    
    return {
        priceData,
        getCurrentPrice,
        getPriceChange,
        getVolume,
        isConnected,
        formatPrice,
        formatChange,
        
        // Backward compatibility with existing useRealTimeData
        realTimeData: {
            [symbol]: priceData
        },
        connectionStatus: priceData.connected ? 'connected' : 'disconnected'
    };
};

export default useBinancePrice;