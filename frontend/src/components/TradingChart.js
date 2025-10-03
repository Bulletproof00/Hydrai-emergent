import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TradingChart = ({ symbol = "BTC/USDT", timeframe = "1h" }) => {
  const chartContainerRef = useRef();
  const chart = useRef();
  const candlestickSeries = useRef();
  const volumeSeries = useRef();
  const [patterns, setPatterns] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const newChart = createChart(chartContainerRef.current, {
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
      },
    });

    chart.current = newChart;

    // Add candlestick series
    const candleSeries = newChart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    candlestickSeries.current = candleSeries;

    // Add volume series
    const volSeries = newChart.addHistogramSeries({
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
      if (newChart) {
        newChart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Load data
    loadChartData();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (newChart) {
        newChart.remove();
      }
    };
  }, [symbol, timeframe]);

  const loadChartData = async () => {
    try {
      const response = await axios.get(`${API}/chart-data/${symbol.replace('/', '-')}?timeframe=${timeframe}&limit=200`);
      const data = response.data.data;

      // Set candlestick data
      candlestickSeries.current.setData(data);

      // Set volume data
      const volumeData = data.map(d => ({
        time: d.time,
        value: d.volume,
        color: d.close >= d.open ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'
      }));
      volumeSeries.current.setData(volumeData);

      // Fit content
      chart.current.timeScale().fitContent();

    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  const analyzePatterns = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/analyze-patterns`, {
        symbol: symbol,
        timeframe: timeframe,
        limit: 200,
        indicators: ['rsi', 'ema50', 'ema200']
      });
      setPatterns(response.data);
    } catch (error) {
      console.error('Error analyzing patterns:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="trading-chart-container">
      <div className="chart-header">
        <h2>{symbol}</h2>
        <button 
          onClick={analyzePatterns} 
          disabled={loading}
          className="analyze-button"
          data-testid="analyze-patterns-button"
        >
          {loading ? 'Analysiere...' : 'KI Pattern-Analyse'}
        </button>
      </div>

      <div ref={chartContainerRef} className="chart-wrapper" data-testid="trading-chart" />

      {patterns && (
        <div className="patterns-panel">
          <div className="patterns-section">
            <h3>Erkannte Muster</h3>
            
            {patterns.candlestick_patterns && patterns.candlestick_patterns.length > 0 && (
              <div className="pattern-group">
                <h4>Candlestick-Muster</h4>
                {patterns.candlestick_patterns.map((pattern, idx) => (
                  <div key={idx} className={`pattern-item pattern-${pattern.type}`}>
                    <span className="pattern-name">{pattern.name}</span>
                    <span className="pattern-strength">{pattern.strength}</span>
                    <p className="pattern-desc">{pattern.description}</p>
                  </div>
                ))}
              </div>
            )}

            {patterns.divergences && patterns.divergences.length > 0 && (
              <div className="pattern-group">
                <h4>Divergenzen</h4>
                {patterns.divergences.map((div, idx) => (
                  <div key={idx} className="pattern-item pattern-warning">
                    <span className="pattern-name">{div.type}</span>
                    <span className="pattern-strength">{div.strength}</span>
                    <p className="pattern-desc">{div.description}</p>
                  </div>
                ))}
              </div>
            )}

            {patterns.chart_patterns && patterns.chart_patterns.length > 0 && (
              <div className="pattern-group">
                <h4>Chart-Patterns</h4>
                {patterns.chart_patterns.map((pattern, idx) => (
                  <div key={idx} className={`pattern-item pattern-${pattern.type}`}>
                    <span className="pattern-name">{pattern.name}</span>
                    <p className="pattern-desc">{pattern.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {patterns.ai_analysis && (
            <div className="ai-analysis-section">
              <h3>Gemini KI-Analyse</h3>
              <div className="ai-analysis-content">
                {patterns.ai_analysis}
              </div>
            </div>
          )}

          <div className="patterns-summary">
            <div className="summary-item">
              <span>Bullische Signale:</span>
              <span className="bullish">{patterns.summary?.bullish_signals || 0}</span>
            </div>
            <div className="summary-item">
              <span>Bearische Signale:</span>
              <span className="bearish">{patterns.summary?.bearish_signals || 0}</span>
            </div>
            <div className="summary-item">
              <span>Divergenzen:</span>
              <span className={patterns.summary?.has_divergence ? 'warning' : ''}>{patterns.summary?.has_divergence ? 'Ja' : 'Nein'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingChart;
