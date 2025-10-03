import { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart } from 'recharts';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TradingChart = ({ symbol = "BTC/USDT", timeframe = "1h" }) => {
  const [chartData, setChartData] = useState([]);
  const [patterns, setPatterns] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadChartData();
  }, [symbol, timeframe]);

  const loadChartData = async () => {
    try {
      const response = await axios.get(`${API}/chart-data/${symbol.replace('/', '-')}?timeframe=${timeframe}&limit=100`);
      const data = response.data.data;

      // Format data for recharts
      const formattedData = data.map(d => ({
        time: new Date(d.time * 1000).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }),
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
        color: d.close >= d.open ? '#10b981' : '#ef4444'
      }));

      setChartData(formattedData);

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
