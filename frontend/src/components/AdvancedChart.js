import { useEffect, useState } from 'react';
import axios from 'axios';
import CandlestickChart from './CandlestickChart';

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
  const [markets, setMarkets] = useState({ crypto: [], traditional: {} });
  const [assetType, setAssetType] = useState('crypto');
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);

  useEffect(() => {
    fetchMarkets();
  }, []);

  useEffect(() => {
    setSelectedSymbol(symbol);
  }, [symbol]);

  const fetchMarkets = async () => {
    try {
      const response = await axios.get(`${API}/markets`);
      setMarkets(response.data);
    } catch (error) {
      console.error('Error fetching markets:', error);
    }
  };

  const handleTimeframeChange = (tf) => {
    setTimeframe(tf);
  };

  const handleSymbolChange = (newSymbol) => {
    setSelectedSymbol(newSymbol);
    if (onSymbolChange) {
      onSymbolChange(newSymbol);
    }
  };

  const handleAssetTypeChange = (type) => {
    setAssetType(type);
    // Set default symbol for asset type
    if (type === 'crypto' && markets.crypto.length > 0) {
      handleSymbolChange(markets.crypto[0]);
    } else if (type === 'traditional' && markets.traditional?.indices?.length > 0) {
      handleSymbolChange(markets.traditional.indices[0]);
    }
  };

  const getAvailableSymbols = () => {
    if (assetType === 'crypto') {
      return markets.crypto || [];
    } else if (assetType === 'traditional') {
      return [
        ...(markets.traditional?.indices || []),
        ...(markets.traditional?.forex || []),
        ...(markets.traditional?.commodities || [])
      ];
    }
    return [];
  };

  return (
    <div className="advanced-chart-container">
      <div className="chart-controls">
        <div className="asset-type-selector">
          <button
            className={`asset-type-btn ${assetType === 'crypto' ? 'active' : ''}`}
            onClick={() => handleAssetTypeChange('crypto')}
          >
            Krypto
          </button>
          <button
            className={`asset-type-btn ${assetType === 'traditional' ? 'active' : ''}`}
            onClick={() => handleAssetTypeChange('traditional')}
          >
            Traditionell
          </button>
        </div>

        <div className="coin-selector">
          <label>Asset:</label>
          <select 
            value={selectedSymbol} 
            onChange={(e) => handleSymbolChange(e.target.value)}
            className="coin-select"
            data-testid="coin-selector"
          >
            {getAvailableSymbols().map(sym => (
              <option key={sym} value={sym}>{sym}</option>
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
      </div>

      <CandlestickChart 
        symbol={selectedSymbol}
        timeframe={timeframe}
        height={700}
      />
    </div>
  );
};

export default AdvancedChart;
