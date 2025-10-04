import { useEffect, useRef, useState } from 'react';
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
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
  const [timeframe, setTimeframe] = useState('1h');
  const [availableCoins, setAvailableCoins] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    fetchAvailableCoins();
  }, []);

  useEffect(() => {
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
    // Chart will be rendered using Recharts instead
    return;
  };

  const loadChartData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/chart-data/${symbol.replace('/', '-')}?timeframe=${timeframe}&limit=100`
      );
      const data = response.data.data;

      if (data && data.length > 0) {
        // Format data for Recharts
        const formattedData = data.map(d => ({
          time: new Date(d.time * 1000).toLocaleTimeString('de-DE', { 
            hour: '2-digit', 
            minute: '2-digit',
            day: '2-digit',
            month: '2-digit'
          }),
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
          volume: d.volume,
          color: d.close >= d.open ? '#10b981' : '#ef4444'
        }));

        setChartData(formattedData);
        setCurrentPrice(data[data.length - 1].close);
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

      <div className="chart-canvas" data-testid="chart-canvas">
        {loading ? (
          <div className="chart-loading">Lade Chart-Daten...</div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={450}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  dataKey="time" 
                  stroke="#94a3b8"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  stroke="#94a3b8"
                  tick={{ fill: '#94a3b8', fontSize: 12 }}
                  domain={['dataMin - 100', 'dataMax + 100']}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(30, 41, 59, 0.95)', 
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#e4e4e7'
                  }}
                  formatter={(value, name) => {
                    if (name === 'close' || name === 'open' || name === 'high' || name === 'low') {
                      return [`$${value.toFixed(2)}`, name.toUpperCase()];
                    }
                    return [value, name];
                  }}
                />
                <Line type="monotone" dataKey="high" stroke="#3b82f6" strokeWidth={1} dot={false} opacity={0.3} />
                <Line type="monotone" dataKey="low" stroke="#ef4444" strokeWidth={1} dot={false} opacity={0.3} />
                <Line type="monotone" dataKey="close" stroke="#10b981" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>

            <ResponsiveContainer width="100%" height={120}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  dataKey="time" 
                  stroke="#94a3b8"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  stroke="#94a3b8"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(30, 41, 59, 0.95)', 
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#e4e4e7'
                  }}
                />
                <Bar dataKey="volume">
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} opacity={0.6} />
                  ))}
                </Bar>
              </ComposedChart>
            </ResponsiveContainer>
          </>
        )}
      </div>
    </div>
  );
};

export default AdvancedChart;
