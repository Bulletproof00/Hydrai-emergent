/**
 * Complete Frontend Binance Integration
 * Direct API calls to Binance REST + WebSocket without backend dependency
 */

class BinanceClient {
    constructor() {
        this.baseURL = 'https://api.binance.com';
        this.futuresURL = 'https://fapi.binance.com';
        this.wsURL = 'wss://stream.binance.com:9443/ws';
        this.futuresWsURL = 'wss://fstream.binance.com/ws';
        
        this.websockets = new Map();
        this.subscribers = new Map();
        
        console.log('🔥 Binance Client initialized - Frontend EXCLUSIVE');
    }

    // Convert symbol format (BTC/USDT <-> BTCUSDT)
    formatSymbol(symbol, toExchange = true) {
        if (toExchange) {
            return symbol.replace('/', ''); // BTC/USDT -> BTCUSDT
        } else {
            // BTCUSDT -> BTC/USDT (assuming USDT pairs)
            return symbol.replace('USDT', '/USDT');
        }
    }

    // Get current price from Binance Spot
    async getCurrentPrice(symbol) {
        try {
            const binanceSymbol = this.formatSymbol(symbol);
            const response = await fetch(`${this.baseURL}/api/v3/ticker/24hr?symbol=${binanceSymbol}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            return {
                symbol: symbol,
                price: parseFloat(data.lastPrice),
                change: parseFloat(data.priceChange),
                changePercent: parseFloat(data.priceChangePercent),
                volume: parseFloat(data.volume),
                high: parseFloat(data.highPrice),
                low: parseFloat(data.lowPrice),
                source: 'binance_spot',
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error(`❌ Binance spot price error for ${symbol}:`, error);
            return null;
        }
    }

    // Get futures price
    async getFuturesPrice(symbol) {
        try {
            const binanceSymbol = this.formatSymbol(symbol);
            const response = await fetch(`${this.futuresURL}/fapi/v1/ticker/24hr?symbol=${binanceSymbol}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            return {
                symbol: symbol,
                price: parseFloat(data.lastPrice),
                change: parseFloat(data.priceChange),
                changePercent: parseFloat(data.priceChangePercent),
                volume: parseFloat(data.volume),
                high: parseFloat(data.highPrice),
                low: parseFloat(data.lowPrice),
                source: 'binance_futures',
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error(`❌ Binance futures price error for ${symbol}:`, error);
            return null;
        }
    }

    // Get OHLCV data
    async getOHLCV(symbol, interval = '1h', limit = 100) {
        try {
            const binanceSymbol = this.formatSymbol(symbol);
            const response = await fetch(
                `${this.baseURL}/api/v3/klines?symbol=${binanceSymbol}&interval=${interval}&limit=${limit}`
            );
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            return data.map(candle => ({
                timestamp: candle[0],
                open: parseFloat(candle[1]),
                high: parseFloat(candle[2]),
                low: parseFloat(candle[3]),
                close: parseFloat(candle[4]),
                volume: parseFloat(candle[5])
            }));
            
        } catch (error) {
            console.error(`❌ Binance OHLCV error for ${symbol}:`, error);
            return [];
        }
    }

    // WebSocket for real-time price updates
    subscribeToPrice(symbol, callback) {
        const binanceSymbol = this.formatSymbol(symbol).toLowerCase();
        const streamName = `${binanceSymbol}@ticker`;
        
        if (this.websockets.has(streamName)) {
            // Add callback to existing subscription
            const callbacks = this.subscribers.get(streamName) || [];
            callbacks.push(callback);
            this.subscribers.set(streamName, callbacks);
            return;
        }

        try {
            const ws = new WebSocket(`${this.wsURL}/${streamName}`);
            
            ws.onopen = () => {
                console.log(`✅ Binance WebSocket connected: ${symbol}`);
                // Initialize subscribers array
                this.subscribers.set(streamName, [callback]);
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.e === '24hrTicker') {
                        const priceUpdate = {
                            symbol: symbol,
                            price: parseFloat(data.c),
                            change: parseFloat(data.p),
                            changePercent: parseFloat(data.P),
                            volume: parseFloat(data.v),
                            high: parseFloat(data.h),
                            low: parseFloat(data.l),
                            timestamp: new Date().toISOString(),
                            source: 'binance_websocket'
                        };

                        // Call all subscribers
                        const callbacks = this.subscribers.get(streamName) || [];
                        callbacks.forEach(cb => {
                            try {
                                cb(priceUpdate);
                            } catch (err) {
                                console.error('Subscriber callback error:', err);
                            }
                        });
                    }
                } catch (err) {
                    console.error('WebSocket message parse error:', err);
                }
            };

            ws.onerror = (error) => {
                console.error(`❌ Binance WebSocket error for ${symbol}:`, error);
            };

            ws.onclose = () => {
                console.log(`🔄 Binance WebSocket closed for ${symbol}, reconnecting...`);
                // Auto-reconnect after 3 seconds
                setTimeout(() => {
                    this.websockets.delete(streamName);
                    this.subscribeToPrice(symbol, callback);
                }, 3000);
            };

            this.websockets.set(streamName, ws);

        } catch (error) {
            console.error(`❌ Failed to create WebSocket for ${symbol}:`, error);
        }
    }

    // Unsubscribe from WebSocket
    unsubscribe(symbol) {
        const binanceSymbol = this.formatSymbol(symbol).toLowerCase();
        const streamName = `${binanceSymbol}@ticker`;
        
        const ws = this.websockets.get(streamName);
        if (ws) {
            ws.close();
            this.websockets.delete(streamName);
            this.subscribers.delete(streamName);
            console.log(`🛑 Unsubscribed from ${symbol}`);
        }
    }

    // Get order book
    async getOrderBook(symbol, limit = 20) {
        try {
            const binanceSymbol = this.formatSymbol(symbol);
            const response = await fetch(`${this.baseURL}/api/v3/depth?symbol=${binanceSymbol}&limit=${limit}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            return {
                symbol: symbol,
                bids: data.bids.map(bid => [parseFloat(bid[0]), parseFloat(bid[1])]),
                asks: data.asks.map(ask => [parseFloat(ask[0]), parseFloat(ask[1])]),
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error(`❌ Binance order book error for ${symbol}:`, error);
            return null;
        }
    }

    // Get multiple symbols at once
    async getAllPrices(symbols) {
        try {
            const promises = symbols.map(symbol => this.getCurrentPrice(symbol));
            const results = await Promise.all(promises);
            
            const priceMap = {};
            results.forEach(result => {
                if (result) {
                    priceMap[result.symbol] = result;
                }
            });
            
            return priceMap;
            
        } catch (error) {
            console.error('❌ Binance batch price error:', error);
            return {};
        }
    }

    // Close all WebSocket connections
    close() {
        this.websockets.forEach((ws, streamName) => {
            ws.close();
            console.log(`🛑 Closed WebSocket: ${streamName}`);
        });
        
        this.websockets.clear();
        this.subscribers.clear();
    }
}

// Create singleton instance
const binanceClient = new BinanceClient();

export default binanceClient;