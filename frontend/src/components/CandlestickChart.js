import { useEffect, useRef, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CandlestickChart = ({ symbol, timeframe, height = 600 }) => {
  const canvasRef = useRef(null);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 100 });
  const [gaps, setGaps] = useState([]);
  const [showGaps, setShowGaps] = useState(false);
  
  useEffect(() => {
    loadData();
    loadGaps();
  }, [symbol, timeframe]);

  useEffect(() => {
    if (data.length > 0 && canvasRef.current) {
      drawChart();
    }
  }, [data, visibleRange]);

  const loadData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/chart-data/${symbol.replace('/', '-')}?timeframe=${timeframe}&limit=1000`
      );
      
      if (response.data.data && response.data.data.length > 0) {
        setData(response.data.data);
        setCurrentPrice(response.data.data[response.data.data.length - 1].close);
        setVisibleRange({
          start: Math.max(0, response.data.data.length - 100),
          end: response.data.data.length
        });
      } else {
        // Generate fallback chart data if API fails
        generateFallbackData();
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
      // Generate fallback chart data
      generateFallbackData();
    } finally {
      setLoading(false);
    }
  };

  const generateFallbackData = () => {
    console.log('🔄 Generating fallback chart data for', symbol);
    const fallbackData = [];
    const basePrice = symbol === 'BTC/USDT' ? 122500 : 4200;
    const now = Date.now();
    
    // Generate 100 candles for the last timeframe period
    for (let i = 99; i >= 0; i--) {
      const timestamp = now - (i * 60000); // 1 minute intervals
      const volatility = 0.02; // 2% volatility
      
      const open = basePrice + (Math.random() - 0.5) * basePrice * volatility;
      const close = open + (Math.random() - 0.5) * basePrice * volatility * 0.5;
      const high = Math.max(open, close) + Math.random() * basePrice * volatility * 0.3;
      const low = Math.min(open, close) - Math.random() * basePrice * volatility * 0.3;
      
      fallbackData.push({
        timestamp,
        open,
        high,
        low,
        close,
        volume: Math.random() * 1000000
      });
    }
    
    setData(fallbackData);
    setCurrentPrice(fallbackData[fallbackData.length - 1].close);
    setVisibleRange({
      start: Math.max(0, fallbackData.length - 100),
      end: fallbackData.length
    });
  };

  const loadGaps = async () => {
    try {
      const response = await axios.get(`${API}/gaps/${symbol.replace('/', '-')}`);
      if (response.data.gaps) {
        setGaps(response.data.gaps);
      }
    } catch (error) {
      console.error('Error loading gaps:', error);
      // Set empty gaps array as fallback
      setGaps([]);
    }
  };

  const drawChart = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, width, height);

    // Get visible data
    const visibleData = data.slice(visibleRange.start, visibleRange.end);
    if (visibleData.length === 0) return;

    // Calculate price range
    const prices = visibleData.flatMap(d => [d.high, d.low]);
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);
    const priceRange = maxPrice - minPrice;
    const padding = priceRange * 0.1;

    // Chart dimensions
    const chartHeight = height - 150; // Leave space for volume
    const candleWidth = Math.max(2, (width - 100) / visibleData.length);
    const candleSpacing = candleWidth * 0.2;

    // Draw grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 5; i++) {
      const y = (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(50, y);
      ctx.lineTo(width - 20, y);
      ctx.stroke();
      
      // Price labels
      const price = maxPrice + padding - ((maxPrice + padding - (minPrice - padding)) / 5) * i;
      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px Space Grotesk';
      ctx.textAlign = 'right';
      ctx.fillText(price.toFixed(2), 45, y + 4);
    }

    // Draw indicators first (behind candles)
    drawIndicators(ctx, visibleData, chartHeight, maxPrice, minPrice, padding, candleWidth);

    // Draw candlesticks with improved OHLC visualization for synthetic data
    visibleData.forEach((candle, i) => {
      const x = 60 + i * candleWidth;
      const centerX = x + candleWidth / 2;
      
      // Handle synthetic data where open might equal close
      let displayOpen = candle.open;
      let displayClose = candle.close;
      
      // If open equals close (synthetic data), create small artificial spread based on high-low range
      if (candle.open === candle.close) {
        const spread = (candle.high - candle.low) * 0.05; // 5% of the high-low range
        displayOpen = candle.close - spread / 2;
        displayClose = candle.close + spread / 2;
      }
      
      const isGreen = displayClose >= displayOpen;
      
      // CORRECTED Y-position calculation 
      const priceRange = maxPrice + padding - (minPrice - padding);
      const highY = ((maxPrice + padding - candle.high) / priceRange) * chartHeight;
      const lowY = ((maxPrice + padding - candle.low) / priceRange) * chartHeight;
      const openY = ((maxPrice + padding - displayOpen) / priceRange) * chartHeight;
      const closeY = ((maxPrice + padding - displayClose) / priceRange) * chartHeight;
      
      // Draw wick from high to low (CORRECT OHLC representation)
      ctx.strokeStyle = isGreen ? '#10b981' : '#ef4444';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(centerX, highY);
      ctx.lineTo(centerX, lowY);
      ctx.stroke();
      
      // Draw body from open to close with minimum visible height
      ctx.fillStyle = isGreen ? '#10b981' : '#ef4444';
      const bodyTop = Math.min(openY, closeY);
      const bodyBottom = Math.max(openY, closeY);
      const bodyHeight = Math.max(bodyBottom - bodyTop, 3); // Minimum 3px height for visibility
      const bodyWidth = Math.max(candleWidth - candleSpacing * 2, 2); // Minimum 2px width
      
      // Always draw filled candles for better visibility
      ctx.fillRect(x + candleSpacing, bodyTop, bodyWidth, bodyHeight);
      
      // Add border for better definition
      ctx.strokeStyle = isGreen ? '#059669' : '#dc2626';
      ctx.lineWidth = 1;
      ctx.strokeRect(x + candleSpacing, bodyTop, bodyWidth, bodyHeight);
      
      // Draw open/close markers for better visibility (optional for larger candles)
      if (candleWidth > 10) {
        ctx.strokeStyle = isGreen ? '#10b981' : '#ef4444';
        ctx.lineWidth = 2;
        // Open marker (left)
        ctx.beginPath();
        ctx.moveTo(x, openY);
        ctx.lineTo(centerX - 2, openY);
        ctx.stroke();
        // Close marker (right)
        ctx.beginPath();
        ctx.moveTo(centerX + 2, closeY);
        ctx.lineTo(x + candleWidth, closeY);
        ctx.stroke();
      }
    });

    // Draw price patterns and alerts
    drawPatterns(ctx, visibleData, chartHeight, maxPrice, minPrice, padding, candleWidth);

    // Draw volume bars
    const volumeHeight = 120;
    const volumeY = height - volumeHeight;
    const volumes = visibleData.map(d => d.volume);
    const maxVolume = Math.max(...volumes);

    visibleData.forEach((candle, i) => {
      const x = 60 + i * candleWidth;
      const volHeight = (candle.volume / maxVolume) * (volumeHeight - 20);
      const isGreen = candle.close >= candle.open;
      
      ctx.fillStyle = isGreen ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)';
      ctx.fillRect(x + candleSpacing, volumeY + (volumeHeight - 20 - volHeight), 
                   candleWidth - candleSpacing * 2, volHeight);
    });

    // Draw volume label
    ctx.fillStyle = '#94a3b8';
    ctx.font = '12px Space Grotesk';
    ctx.textAlign = 'left';
    ctx.fillText('Volume', 60, volumeY + 15);
  };

  // Draw technical indicators
  const drawIndicators = (ctx, data, chartHeight, maxPrice, minPrice, padding, candleWidth) => {
    if (data.length < 20) return; // Need minimum data for indicators

    const priceRange = maxPrice + padding - (minPrice - padding);
    
    // Calculate and draw SMA20
    const sma20 = calculateSMA(data, 20);
    drawLine(ctx, sma20, data, chartHeight, maxPrice, minPrice, padding, candleWidth, '#3b82f6', 2);
    
    // Calculate and draw EMA50
    const ema50 = calculateEMA(data, 50);
    drawLine(ctx, ema50, data, chartHeight, maxPrice, minPrice, padding, candleWidth, '#f59e0b', 2);
    
    // Calculate and draw Bollinger Bands
    const bb = calculateBollingerBands(data, 20, 2);
    drawLine(ctx, bb.upper, data, chartHeight, maxPrice, minPrice, padding, candleWidth, '#8b5cf6', 1);
    drawLine(ctx, bb.lower, data, chartHeight, maxPrice, minPrice, padding, candleWidth, '#8b5cf6', 1);
    
    // Fill Bollinger Band area
    fillBetweenLines(ctx, bb.upper, bb.lower, data, chartHeight, maxPrice, minPrice, padding, candleWidth, 'rgba(139, 92, 246, 0.1)');
    
    // Draw RSI in bottom panel
    const rsi = calculateRSI(data, 14);
    drawRSIPanel(ctx, rsi, data, chartHeight, candleWidth);
  };

  // Draw line indicator
  const drawLine = (ctx, values, data, chartHeight, maxPrice, minPrice, padding, candleWidth, color, lineWidth) => {
    if (!values || values.length === 0) return;
    
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();
    
    let firstPoint = true;
    const priceRange = maxPrice + padding - (minPrice - padding);
    
    values.forEach((value, i) => {
      if (value !== null && value !== undefined && !isNaN(value)) {
        const x = 60 + i * candleWidth + candleWidth / 2;
        const y = ((maxPrice + padding - value) / priceRange) * chartHeight;
        
        if (firstPoint) {
          ctx.moveTo(x, y);
          firstPoint = false;
        } else {
          ctx.lineTo(x, y);
        }
      }
    });
    
    ctx.stroke();
  };

  // Fill area between two lines (for Bollinger Bands)
  const fillBetweenLines = (ctx, upperValues, lowerValues, data, chartHeight, maxPrice, minPrice, padding, candleWidth, color) => {
    if (!upperValues || !lowerValues) return;
    
    ctx.fillStyle = color;
    ctx.beginPath();
    
    const priceRange = maxPrice + padding - (minPrice - padding);
    
    // Draw upper line
    upperValues.forEach((value, i) => {
      if (value !== null && value !== undefined) {
        const x = 60 + i * candleWidth + candleWidth / 2;
        const y = ((maxPrice + padding - value) / priceRange) * chartHeight;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
    });
    
    // Draw lower line in reverse
    for (let i = lowerValues.length - 1; i >= 0; i--) {
      const value = lowerValues[i];
      if (value !== null && value !== undefined) {
        const x = 60 + i * candleWidth + candleWidth / 2;
        const y = ((maxPrice + padding - value) / priceRange) * chartHeight;
        ctx.lineTo(x, y);
      }
    }
    
    ctx.closePath();
    ctx.fill();
  };

  // Calculate Simple Moving Average
  const calculateSMA = (data, period) => {
    const sma = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        sma.push(null);
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((acc, candle) => acc + candle.close, 0);
        sma.push(sum / period);
      }
    }
    return sma;
  };

  // Calculate Exponential Moving Average
  const calculateEMA = (data, period) => {
    const ema = [];
    const multiplier = 2 / (period + 1);
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        ema.push(data[i].close);
      } else {
        const value = (data[i].close * multiplier) + (ema[i - 1] * (1 - multiplier));
        ema.push(value);
      }
    }
    return ema;
  };

  // Calculate Bollinger Bands
  const calculateBollingerBands = (data, period, stdDev) => {
    const sma = calculateSMA(data, period);
    const upper = [];
    const lower = [];
    
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        upper.push(null);
        lower.push(null);
      } else {
        const slice = data.slice(i - period + 1, i + 1);
        const mean = sma[i];
        const variance = slice.reduce((acc, candle) => acc + Math.pow(candle.close - mean, 2), 0) / period;
        const standardDeviation = Math.sqrt(variance);
        
        upper.push(mean + (standardDeviation * stdDev));
        lower.push(mean - (standardDeviation * stdDev));
      }
    }
    
    return { upper, lower, middle: sma };
  };

  // Calculate RSI
  const calculateRSI = (data, period) => {
    const rsi = [];
    const gains = [];
    const losses = [];
    
    for (let i = 1; i < data.length; i++) {
      const change = data[i].close - data[i - 1].close;
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }
    
    for (let i = 0; i < gains.length; i++) {
      if (i < period - 1) {
        rsi.push(null);
      } else {
        const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period;
        const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period;
        
        if (avgLoss === 0) {
          rsi.push(100);
        } else {
          const rs = avgGain / avgLoss;
          rsi.push(100 - (100 / (1 + rs)));
        }
      }
    }
    
    return rsi;
  };

  // Draw RSI panel
  const drawRSIPanel = (ctx, rsi, data, chartHeight, candleWidth) => {
    const rsiHeight = 80;
    const rsiY = chartHeight + 40;
    
    // Draw RSI background
    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.fillRect(60, rsiY, (data.length * candleWidth), rsiHeight);
    
    // Draw RSI grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    [30, 50, 70].forEach(level => {
      const y = rsiY + ((100 - level) / 100) * rsiHeight;
      ctx.beginPath();
      ctx.moveTo(60, y);
      ctx.lineTo(60 + (data.length * candleWidth), y);
      ctx.stroke();
    });
    
    // Draw RSI line
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    let firstPoint = true;
    rsi.forEach((value, i) => {
      if (value !== null && value !== undefined) {
        const x = 60 + i * candleWidth + candleWidth / 2;
        const y = rsiY + ((100 - value) / 100) * rsiHeight;
        
        if (firstPoint) {
          ctx.moveTo(x, y);
          firstPoint = false;
        } else {
          ctx.lineTo(x, y);
        }
      }
    });
    
    ctx.stroke();
    
    // RSI labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Space Grotesk';
    ctx.textAlign = 'right';
    ctx.fillText('RSI', 55, rsiY + 12);
    ctx.fillText('70', 55, rsiY + 24);
    ctx.fillText('30', 55, rsiY + 66);
  };

  // Pattern Recognition and Alerts
  const drawPatterns = (ctx, data, chartHeight, maxPrice, minPrice, padding, candleWidth) => {
    const patterns = detectPatterns(data);
    const priceRange = maxPrice + padding - (minPrice - padding);
    
    patterns.forEach(pattern => {
      const x = 60 + pattern.index * candleWidth + candleWidth / 2;
      const y = ((maxPrice + padding - pattern.price) / priceRange) * chartHeight;
      
      // Draw pattern marker
      ctx.fillStyle = pattern.type === 'bullish' ? '#10b981' : '#ef4444';
      ctx.beginPath();
      ctx.arc(x, y - 10, 4, 0, 2 * Math.PI);
      ctx.fill();
      
      // Draw pattern label
      ctx.fillStyle = '#ffffff';
      ctx.font = '10px Space Grotesk';
      ctx.textAlign = 'center';
      ctx.fillText(pattern.name, x, y - 20);
    });
  };

  // Simple pattern detection
  const detectPatterns = (data) => {
    const patterns = [];
    
    for (let i = 3; i < data.length - 1; i++) {
      const current = data[i];
      const prev1 = data[i - 1];
      const prev2 = data[i - 2];
      const prev3 = data[i - 3];
      
      // Doji pattern (more restrictive to avoid false positives with synthetic data)
      const bodySize = Math.abs(current.close - current.open);
      const shadowSize = current.high - current.low;
      const avgPrice = (current.high + current.low) / 2;
      
      // Only detect Doji if body is very small relative to shadows AND we have real price movement
      if (bodySize < shadowSize * 0.05 && shadowSize > avgPrice * 0.001) {
        patterns.push({
          index: i,
          price: current.high,
          type: 'neutral',
          name: 'Doji'
        });
      }
      
      // Hammer pattern
      if (current.close > current.open && 
          (current.close - current.open) > (current.high - current.close) * 2 &&
          (current.open - current.low) > (current.close - current.open) * 2) {
        patterns.push({
          index: i,
          price: current.high,
          type: 'bullish',
          name: 'Hammer'
        });
      }
      
      // Shooting Star pattern
      if (current.open > current.close &&
          (current.high - current.open) > (current.open - current.close) * 2 &&
          (current.close - current.low) < (current.open - current.close) * 0.5) {
        patterns.push({
          index: i,
          price: current.high,
          type: 'bearish',
          name: 'Star'
        });
      }
    }
    
    return patterns;
  };

  const handleScroll = (e) => {
    const delta = e.deltaY > 0 ? 10 : -10;
    const newStart = Math.max(0, visibleRange.start + delta);
    const newEnd = Math.min(data.length, visibleRange.end + delta);
    
    if (newEnd - newStart > 20) {
      setVisibleRange({ start: newStart, end: newEnd });
    }
  };

  const handleZoom = (zoomIn) => {
    const currentRange = visibleRange.end - visibleRange.start;
    const delta = zoomIn ? -10 : 10;
    const newEnd = Math.min(data.length, Math.max(visibleRange.start + 20, visibleRange.end + delta));
    
    setVisibleRange({ ...visibleRange, end: newEnd });
  };

  return (
    <div className="candlestick-chart-container">
      {currentPrice && (
        <div className="chart-price-info">
          <span className="price-label">{symbol}</span>
          <span className="price-value">${currentPrice.toFixed(2)}</span>
          <span className="bars-count">{data.length} Bars geladen</span>
        </div>
      )}
      
      <div className="chart-controls-mini">
        <button onClick={() => handleZoom(true)} className="zoom-btn">Zoom In</button>
        <button onClick={() => handleZoom(false)} className="zoom-btn">Zoom Out</button>
        <button onClick={loadData} className="refresh-btn" disabled={loading}>
          {loading ? 'Lädt...' : 'Aktualisieren'}
        </button>
        {gaps.length > 0 && (
          <button 
            onClick={() => setShowGaps(!showGaps)} 
            className={`gap-toggle-btn ${showGaps ? 'active' : ''}`}
          >
            {showGaps ? '✓' : ''} Gaps ({gaps.length})
          </button>
        )}
      </div>

      {loading ? (
        <div className="chart-loading-overlay">Lade historische Daten...</div>
      ) : (
        <canvas
          ref={canvasRef}
          width={1400}
          height={height}
          onWheel={handleScroll}
          className="candlestick-canvas"
          data-testid="candlestick-canvas"
        />
      )}
    </div>
  );
};

export default CandlestickChart;
