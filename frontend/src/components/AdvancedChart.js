import { useEffect, useState } from 'react';
import axios from 'axios';
import CandlestickChart from './CandlestickChart';
import { useRealTimeData } from '../hooks/useRealTimeData';

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

const AdvancedChart = ({ symbol = "BTC/USDT", onSymbolChange, globalTimeframe, setGlobalTimeframe }) => {
  const [markets, setMarkets] = useState({ crypto: [], traditional: {} });
  const [assetType, setAssetType] = useState('crypto');
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);
  
  // Use global timeframe if provided, otherwise default to '1h'
  const timeframe = globalTimeframe || '1h';
  
  // Real-time data hook
  const { 
    realTimeData, 
    connectionStatus, 
    getCurrentPrice, 
    getPriceChange, 
    isLive 
  } = useRealTimeData(selectedSymbol);

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
    // Update global timeframe instead of local state
    if (setGlobalTimeframe) {
      setGlobalTimeframe(tf);
    }
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

      {/* Real-time price display */}
      <div className="realtime-price-display">
        <div className="price-header">
          <span className="symbol-name">{selectedSymbol}</span>
          <div className="connection-status">
            <div className={`status-indicator ${connectionStatus}`}></div>
            <span className="status-text">
              {connectionStatus === 'connected' ? 'Live' : 
               connectionStatus === 'disconnected' ? 'API' : 'Error'}
            </span>
          </div>
        </div>
        
        <div className="price-info">
          <span className="current-price">
            ${getCurrentPrice(selectedSymbol).toLocaleString(undefined, { 
              minimumFractionDigits: 2, 
              maximumFractionDigits: 2 
            })}
          </span>
          
          {(() => {
            const priceChange = getPriceChange(selectedSymbol);
            return (
              <span className={`price-change ${priceChange.isPositive ? 'positive' : 'negative'}`}>
                {priceChange.isPositive ? '+' : ''}{priceChange.changePercent.toFixed(2)}%
                {isLive(selectedSymbol) && <span className="live-indicator">●</span>}
              </span>
            );
          })()}
        </div>
        
        {Object.keys(realTimeData).length > 0 && (
          <div className="data-source">
            Quelle: {realTimeData[selectedSymbol]?.source || 'N/A'}
          </div>
        )}
      </div>

      <CandlestickChart 
        symbol={selectedSymbol}
        timeframe={timeframe}
        height={700}
        realTimePrice={getCurrentPrice(selectedSymbol)}
      />
    </div>
  );
};

export default AdvancedChart;
