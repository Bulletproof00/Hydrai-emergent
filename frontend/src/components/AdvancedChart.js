import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TIMEFRAMES = [
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1h', value: '1h' },
  { label: '4h', value: '4h' },
  { label: '6h', value: '6h' },
  { label: '12h', value: '12h' },
  { label: '1D', value: '1d' },
  { label: '1W', value: '1w' },
  { label: '1M', value: '1M' }
];

const AdvancedChart = ({ symbol = "BTC/USDT", onSymbolChange }) => {
  const chartContainerRef = useRef();
  const chart = useRef(null);
  const candlestickSeries = useRef(null);
  const volumeSeries = useRef(null);
  const [timeframe, setTimeframe] = useState('1h');
  const [availableCoins, setAvailableCoins] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAvailableCoins();
  }, []);

  useEffect(() => {
    if (chartContainerRef.current && !chart.current) {
      initChart();
    }
    loadChartData();
  }, [symbol, timeframe]);

  const fetchAvailableCoins = async () => {
    try {
      const response = await axios.get(`${API}/coins`);
      setAvailableCoins(response.data.coins);
    } catch (error) {
      console.error('Error fetching coins:', error);
    }
  };

  const initChart = () => {
    if (!chartContainerRef.current) return;

    const chartInstance = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 600,
      layout: {
        background: { color: '#0f172a' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chart.current = chartInstance;

    // Candlestick series
    const candleSeries = chartInstance.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });
    candlestickSeries.current = candleSeries;

    // Volume series
    const volSeries = chartInstance.addHistogramSeries({
      color: '#3b82f6',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });
    volumeSeries.current = volSeries;

    // Handle resize
    const handleResize = () => {
      if (chartInstance && chartContainerRef.current) {
        chartInstance.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartInstance) {
        chartInstance.remove();
      }
    };
  };

  const loadChartData = async () => {
    if (!candlestickSeries.current || !volumeSeries.current) return;
    
    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/chart-data/${symbol.replace('/', '-')}?timeframe=${timeframe}&limit=200`
      );
      const data = response.data.data;

      if (data && data.length > 0) {
        // Set candlestick data
        candlestickSeries.current.setData(data);

        // Set volume data
        const volumeData = data.map(d => ({
          time: d.time,
          value: d.volume,
          color: d.close >= d.open ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'
        }));
        volumeSeries.current.setData(volumeData);

        // Set current price
        setCurrentPrice(data[data.length - 1].close);

        // Fit content
        if (chart.current) {
          chart.current.timeScale().fitContent();
        }
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTimeframeChange = (tf) => {
    setTimeframe(tf);
  };

  const handleSymbolChange = (newSymbol) => {
    if (onSymbolChange) {
      onSymbolChange(newSymbol);
    }
  };

  return (
    <div className="advanced-chart-container">
      <div className="chart-controls">
        <div className="coin-selector">
          <label>Coin:</label>
          <select 
            value={symbol} 
            onChange={(e) => handleSymbolChange(e.target.value)}
            className="coin-select"
            data-testid="coin-selector"
          >
            {availableCoins.map(coin => (
              <option key={coin} value={coin}>{coin}</option>
            ))}
          </select>
        </div>

        <div className="timeframe-selector">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf.value}
              className={`timeframe-btn ${timeframe === tf.value ? 'active' : ''}`}
              onClick={() => handleTimeframeChange(tf.value)}
              data-testid={`timeframe-${tf.value}`}
            >
              {tf.label}
            </button>
          ))}
        </div>

        {currentPrice && (
          <div className="current-price" data-testid="current-price">
            <span className="price-label">Preis:</span>
            <span className="price-value">${currentPrice.toLocaleString('de-DE', {minimumFractionDigits: 2})}</span>
          </div>
        )}
      </div>

      <div 
        ref={chartContainerRef} 
        className="chart-canvas"
        data-testid="chart-canvas"
      />

      {loading && (
        <div className="chart-loading">
          Lade Chart-Daten...
        </div>
      )}
    </div>
  );
};

export default AdvancedChart;
