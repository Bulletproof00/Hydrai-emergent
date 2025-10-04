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
  
  useEffect(() => {
    loadData();
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
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
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

    // Draw candlesticks
    visibleData.forEach((candle, i) => {
      const x = 60 + i * candleWidth;
      const isGreen = candle.close >= candle.open;
      
      // Calculate y positions
      const highY = ((maxPrice + padding - candle.high) / (maxPrice + padding - (minPrice - padding))) * chartHeight;
      const lowY = ((maxPrice + padding - candle.low) / (maxPrice + padding - (minPrice - padding))) * chartHeight;
      const openY = ((maxPrice + padding - candle.open) / (maxPrice + padding - (minPrice - padding))) * chartHeight;
      const closeY = ((maxPrice + padding - candle.close) / (maxPrice + padding - (minPrice - padding))) * chartHeight;
      
      // Draw wick
      ctx.strokeStyle = isGreen ? '#10b981' : '#ef4444';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x + candleWidth / 2, highY);
      ctx.lineTo(x + candleWidth / 2, lowY);
      ctx.stroke();
      
      // Draw body
      ctx.fillStyle = isGreen ? '#10b981' : '#ef4444';
      const bodyHeight = Math.abs(closeY - openY);
      const bodyY = Math.min(openY, closeY);
      ctx.fillRect(x + candleSpacing, bodyY, candleWidth - candleSpacing * 2, Math.max(bodyHeight, 1));
    });

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
          <span className="price-value">${currentPrice.toLocaleString('de-DE', {minimumFractionDigits: 2})}</span>
          <span className="bars-count">{data.length} Bars geladen</span>
        </div>
      )}
      
      <div className="chart-controls-mini">
        <button onClick={() => handleZoom(true)} className="zoom-btn">Zoom In</button>
        <button onClick={() => handleZoom(false)} className="zoom-btn">Zoom Out</button>
        <button onClick={loadData} className="refresh-btn" disabled={loading}>
          {loading ? 'Lädt...' : 'Aktualisieren'}
        </button>
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
