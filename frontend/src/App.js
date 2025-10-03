import { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Send, TrendingUp, Activity, BarChart3, Brain, Zap, Settings, LineChart } from "lucide-react";
import TradingChart from "./components/TradingChart";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [livePrice, setLivePrice] = useState(null);
  const [indicators, setIndicators] = useState(null);
  const [plugins, setPlugins] = useState([]);
  const [activeView, setActiveView] = useState("chat");
  const [macroData, setMacroData] = useState(null);
  const [correlations, setCorrelations] = useState(null);
  const [marketOverview, setMarketOverview] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    initializeSession();
    fetchPlugins();
    fetchLivePrice();
    fetchIndicators();
    fetchMacroData();
    fetchMarketOverview();
    
    const priceInterval = setInterval(fetchLivePrice, 10000);
    const indicatorInterval = setInterval(fetchIndicators, 30000);
    const macroInterval = setInterval(fetchMacroData, 60000);
    const overviewInterval = setInterval(fetchMarketOverview, 60000);
    
    return () => {
      clearInterval(priceInterval);
      clearInterval(indicatorInterval);
      clearInterval(macroInterval);
      clearInterval(overviewInterval);
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const initializeSession = async () => {
    try {
      const response = await axios.post(`${API}/sessions`);
      setSessionId(response.data.id);
      
      // Add welcome message
      setMessages([{
        role: "assistant",
        content: "Willkommen bei Hydra AI! 🚀\n\nIch bin dein KI-gestützter Trading-Analyse-Assistent. Ich kann dir helfen mit:\n\n• Live-Marktdaten von Binance\n• Technische Indikatoren (RSI, MFI, Bollinger Bands)\n• Backtesting von Trading-Strategien\n• Marktanalysen und Empfehlungen\n\nWie kann ich dir heute helfen?",
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error("Error creating session:", error);
    }
  };

  const fetchPlugins = async () => {
    try {
      const response = await axios.get(`${API}/plugins`);
      setPlugins(response.data);
    } catch (error) {
      console.error("Error fetching plugins:", error);
    }
  };

  const fetchLivePrice = async () => {
    try {
      const response = await axios.get(`${API}/price/BTC-USDT`);
      setLivePrice(response.data);
    } catch (error) {
      console.error("Error fetching price:", error);
    }
  };

  const fetchIndicators = async () => {
    try {
      const response = await axios.post(`${API}/indicators`, {
        symbol: "BTC/USDT",
        timeframe: "1h",
        limit: 200,
        indicators: ["rsi", "mfi", "bollinger", "stochastic", "stoch_rsi", "obv", "vwap", "ema50", "ema200", "volume_pvsra"]
      });
      setIndicators(response.data);
    } catch (error) {
      console.error("Error fetching indicators:", error);
    }
  };

  const fetchMacroData = async () => {
    try {
      const response = await axios.get(`${API}/macro-data`);
      setMacroData(response.data);
    } catch (error) {
      console.error("Error fetching macro data:", error);
    }
  };

  const fetchMarketOverview = async () => {
    try {
      const response = await axios.get(`${API}/market-overview`);
      setMarketOverview(response.data);
      if (response.data.correlations) {
        setCorrelations(response.data.correlations);
      }
    } catch (error) {
      console.error("Error fetching market overview:", error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        session_id: sessionId,
        content: input
      });

      setMessages(prev => [...prev, {
        role: "assistant",
        content: response.data.content,
        timestamp: response.data.timestamp
      }]);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Entschuldigung, es gab einen Fehler bei der Verarbeitung deiner Anfrage.",
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const runBacktest = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/backtest`, {
        symbol: "BTC/USDT",
        timeframe: "1h",
        strategy: "rsi_crossover",
        params: {
          rsi_period: 14,
          oversold: 30,
          overbought: 70
        }
      });

      const backtestMessage = {
        role: "assistant",
        content: `📊 Backtest Ergebnisse:\n\nStrategie: RSI Crossover\nGesamtrendite: ${response.data.total_return.toFixed(2)}%\nWinrate: ${response.data.win_rate.toFixed(2)}%\nAnzahl Trades: ${response.data.total_trades}\nProfitable Trades: ${response.data.profitable_trades}\n\nLetztes Signal: ${response.data.last_signal === 1 ? 'KAUFEN' : response.data.last_signal === -1 ? 'VERKAUFEN' : 'NEUTRAL'}\nAktueller RSI: ${response.data.last_rsi?.toFixed(2)}`,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, backtestMessage]);
    } catch (error) {
      console.error("Error running backtest:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <Brain className="logo-icon" />
            <span>HYDRA AI</span>
          </div>
        </div>

        <nav className="nav-menu">
          <button 
            className={`nav-item ${activeView === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveView('chat')}
            data-testid="nav-chat"
          >
            <Brain size={20} />
            <span>Chat</span>
          </button>
          <button 
            className={`nav-item ${activeView === 'analysis' ? 'active' : ''}`}
            onClick={() => setActiveView('analysis')}
            data-testid="nav-analysis"
          >
            <Activity size={20} />
            <span>Analyse</span>
          </button>
          <button 
            className={`nav-item ${activeView === 'chart' ? 'active' : ''}`}
            onClick={() => setActiveView('chart')}
            data-testid="nav-chart"
          >
            <LineChart size={20} />
            <span>Chart</span>
          </button>
          <button 
            className={`nav-item ${activeView === 'plugins' ? 'active' : ''}`}
            onClick={() => setActiveView('plugins')}
            data-testid="nav-plugins"
          >
            <Zap size={20} />
            <span>Plugins</span>
          </button>
        </nav>

        {/* Live Price Widget */}
        {livePrice && (
          <div className="price-widget">
            <div className="price-header">
              <TrendingUp size={16} />
              <span>BTC/USDT</span>
            </div>
            <div className="price-value" data-testid="live-price">
              ${livePrice.price?.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className={`price-change ${livePrice.change_24h >= 0 ? 'positive' : 'negative'}`}>
              {livePrice.change_24h >= 0 ? '+' : ''}{livePrice.change_24h?.toFixed(2)}%
            </div>
          </div>
        )}

        {/* Indicators Widget */}
        {indicators && (
          <div className="indicators-widget">
            <div className="widget-title">Indikatoren</div>
            {indicators.indicators?.rsi && (
              <div className="indicator-item">
                <span>RSI</span>
                <span className={`indicator-value ${indicators.indicators.rsi < 30 ? 'oversold' : indicators.indicators.rsi > 70 ? 'overbought' : ''}`}>
                  {indicators.indicators.rsi.toFixed(2)}
                </span>
              </div>
            )}
            {indicators.indicators?.mfi && (
              <div className="indicator-item">
                <span>MFI</span>
                <span className="indicator-value">{indicators.indicators.mfi.toFixed(2)}</span>
              </div>
            )}
            {indicators.indicators?.bollinger && (
              <div className="indicator-item">
                <span>BB Upper</span>
                <span className="indicator-value">${indicators.indicators.bollinger.upper.toFixed(2)}</span>
              </div>
            )}
          </div>
        )}

        {/* Correlations Widget */}
        {correlations && Object.keys(correlations).length > 0 && (
          <div className="indicators-widget" style={{marginTop: '16px'}}>
            <div className="widget-title">Korrelationen</div>
            {Object.entries(correlations).slice(0, 3).map(([key, value]) => (
              <div key={key} className="indicator-item">
                <span className="correlation-mini-label">{key.replace('BTC_vs_', '')}</span>
                <span className={`indicator-value ${value > 0.5 ? 'positive' : value < -0.5 ? 'negative' : ''}`}>
                  {value?.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="main-content">
        {activeView === 'chat' && (
          <>
            <div className="chat-header">
              <h1 data-testid="chat-title">Hydra AI Trading Assistant</h1>
              <button className="backtest-btn" onClick={runBacktest} disabled={loading} data-testid="backtest-button">
                <BarChart3 size={18} />
                Backtest ausführen
              </button>
            </div>

            <div className="messages-container" data-testid="messages-container">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role}`} data-testid={`message-${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'assistant' ? <Brain size={20} /> : <div className="user-avatar">U</div>}
                  </div>
                  <div className="message-content">
                    <div className="message-text">{msg.content}</div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message assistant" data-testid="loading-message">
                  <div className="message-avatar">
                    <Brain size={20} />
                  </div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form className="input-form" onSubmit={sendMessage}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Frage mich etwas über Trading, Indikatoren oder Strategien..."
                className="message-input"
                disabled={loading}
                data-testid="chat-input"
              />
              <button type="submit" className="send-button" disabled={loading || !input.trim()} data-testid="send-button">
                <Send size={20} />
              </button>
            </form>
          </>
        )}

        {activeView === 'analysis' && (
          <div className="analysis-view">
            <h1>Umfassende Marktanalyse</h1>
            
            {/* Makrodaten Section */}
            {macroData && (
              <>
                <h2 className="section-title">Makroökonomische Daten</h2>
                <div className="analysis-grid">
                  {macroData.Bitcoin && (
                    <div className="analysis-card">
                      <h3>Bitcoin</h3>
                      <div className="macro-value">${macroData.Bitcoin.price?.toLocaleString('de-DE', {minimumFractionDigits: 2})}</div>
                      <div className={`macro-change ${macroData.Bitcoin.change_24h >= 0 ? 'positive' : 'negative'}`}>
                        {macroData.Bitcoin.change_24h >= 0 ? '+' : ''}{macroData.Bitcoin.change_24h?.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {macroData.Ethereum && (
                    <div className="analysis-card">
                      <h3>Ethereum</h3>
                      <div className="macro-value">${macroData.Ethereum.price?.toLocaleString('de-DE', {minimumFractionDigits: 2})}</div>
                      <div className={`macro-change ${macroData.Ethereum.change_24h >= 0 ? 'positive' : 'negative'}`}>
                        {macroData.Ethereum.change_24h >= 0 ? '+' : ''}{macroData.Ethereum.change_24h?.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {macroData.SPX && (
                    <div className="analysis-card">
                      <h3>S&P 500</h3>
                      <div className="macro-value">{macroData.SPX.price?.toFixed(2)}</div>
                      <div className={`macro-change ${macroData.SPX.change_24h >= 0 ? 'positive' : 'negative'}`}>
                        {macroData.SPX.change_24h >= 0 ? '+' : ''}{macroData.SPX.change_24h?.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {macroData.NASDAQ && (
                    <div className="analysis-card">
                      <h3>NASDAQ</h3>
                      <div className="macro-value">{macroData.NASDAQ.price?.toFixed(2)}</div>
                      <div className={`macro-change ${macroData.NASDAQ.change_24h >= 0 ? 'positive' : 'negative'}`}>
                        {macroData.NASDAQ.change_24h >= 0 ? '+' : ''}{macroData.NASDAQ.change_24h?.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {macroData.Gold && (
                    <div className="analysis-card">
                      <h3>Gold</h3>
                      <div className="macro-value">${macroData.Gold.price?.toFixed(2)}</div>
                      <div className={`macro-change ${macroData.Gold.change_24h >= 0 ? 'positive' : 'negative'}`}>
                        {macroData.Gold.change_24h >= 0 ? '+' : ''}{macroData.Gold.change_24h?.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {macroData.DXY && (
                    <div className="analysis-card">
                      <h3>US Dollar Index</h3>
                      <div className="macro-value">{macroData.DXY.price?.toFixed(2)}</div>
                      <div className={`macro-change ${macroData.DXY.change_24h >= 0 ? 'positive' : 'negative'}`}>
                        {macroData.DXY.change_24h >= 0 ? '+' : ''}{macroData.DXY.change_24h?.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {macroData.Russell2000 && (
                    <div className="analysis-card">
                      <h3>Russell 2000</h3>
                      <div className="macro-value">{macroData.Russell2000.price?.toFixed(2)}</div>
                      <div className={`macro-change ${macroData.Russell2000.change_24h >= 0 ? 'positive' : 'negative'}`}>
                        {macroData.Russell2000.change_24h >= 0 ? '+' : ''}{macroData.Russell2000.change_24h?.toFixed(2)}%
                      </div>
                    </div>
                  )}
                  {macroData.BitcoinDominance && (
                    <div className="analysis-card">
                      <h3>Bitcoin Dominanz</h3>
                      <div className="macro-value">{macroData.BitcoinDominance.percentage?.toFixed(2)}%</div>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Korrelationen */}
            {correlations && Object.keys(correlations).length > 0 && (
              <>
                <h2 className="section-title">Korrelationsanalyse</h2>
                <div className="correlation-grid">
                  {Object.entries(correlations).map(([key, value]) => (
                    <div key={key} className="correlation-card">
                      <div className="correlation-label">{key.replace('BTC_vs_', 'BTC ⟷ ')}</div>
                      <div className={`correlation-value ${value > 0.5 ? 'strong-positive' : value < -0.5 ? 'strong-negative' : 'weak'}`}>
                        {value?.toFixed(3)}
                      </div>
                      <div className="correlation-bar">
                        <div className="correlation-fill" style={{width: `${Math.abs(value) * 100}%`, backgroundColor: value > 0 ? '#10b981' : '#ef4444'}}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Technische Indikatoren */}
            {indicators && (
              <>
                <h2 className="section-title">Technische Indikatoren</h2>
                <div className="analysis-grid">
                  {indicators.indicators?.rsi && (
                    <div className="analysis-card">
                      <h3>RSI</h3>
                      <div className="gauge-value">{indicators.indicators.rsi.toFixed(2)}</div>
                      <div className="gauge-label">
                        {indicators.indicators.rsi < 30 ? 'Überverkauft' : 
                         indicators.indicators.rsi > 70 ? 'Überkauft' : 'Neutral'}
                      </div>
                    </div>
                  )}
                  {indicators.indicators?.stochastic && (
                    <div className="analysis-card">
                      <h3>Stochastic</h3>
                      <div className="indicator-row">
                        <span>%K:</span>
                        <span>{indicators.indicators.stochastic.k?.toFixed(2)}</span>
                      </div>
                      <div className="indicator-row">
                        <span>%D:</span>
                        <span>{indicators.indicators.stochastic.d?.toFixed(2)}</span>
                      </div>
                    </div>
                  )}
                  {indicators.indicators?.stoch_rsi && (
                    <div className="analysis-card">
                      <h3>Stochastic RSI</h3>
                      <div className="indicator-row">
                        <span>%K:</span>
                        <span>{indicators.indicators.stoch_rsi.k?.toFixed(2)}</span>
                      </div>
                      <div className="indicator-row">
                        <span>%D:</span>
                        <span>{indicators.indicators.stoch_rsi.d?.toFixed(2)}</span>
                      </div>
                    </div>
                  )}
                  {indicators.indicators?.obv && (
                    <div className="analysis-card">
                      <h3>OBV</h3>
                      <div className="macro-value">{indicators.indicators.obv?.toLocaleString('de-DE')}</div>
                    </div>
                  )}
                  {indicators.indicators?.vwap && (
                    <div className="analysis-card">
                      <h3>VWAP</h3>
                      <div className="macro-value">${indicators.indicators.vwap?.toFixed(2)}</div>
                    </div>
                  )}
                  {indicators.indicators?.ema50 && (
                    <div className="analysis-card">
                      <h3>EMA 50</h3>
                      <div className="macro-value">${indicators.indicators.ema50?.toFixed(2)}</div>
                    </div>
                  )}
                  {indicators.indicators?.ema200 && (
                    <div className="analysis-card">
                      <h3>EMA 200</h3>
                      <div className="macro-value">${indicators.indicators.ema200?.toFixed(2)}</div>
                    </div>
                  )}
                  {indicators.indicators?.volume_pvsra && (
                    <div className="analysis-card">
                      <h3>Volume PVSRA</h3>
                      <div className="indicator-row">
                        <span>Klassifizierung:</span>
                        <span className="volume-class">{indicators.indicators.volume_pvsra.classification}</span>
                      </div>
                      <div className="indicator-row">
                        <span>Stärke:</span>
                        <span>{indicators.indicators.volume_pvsra.strength}</span>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {activeView === 'plugins' && (
          <div className="plugins-view">
            <h1>Plugin System</h1>
            <div className="plugins-grid">
              {plugins.map((plugin, idx) => (
                <div key={idx} className="plugin-card" data-testid={`plugin-${plugin.id}`}>
                  <div className="plugin-header">
                    <Zap size={24} className="plugin-icon" />
                    <span className={`plugin-status ${plugin.status}`}>{plugin.status}</span>
                  </div>
                  <h3>{plugin.name}</h3>
                  <p className="plugin-type">{plugin.type}</p>
                  <p className="plugin-description">{plugin.description}</p>
                  <p className="plugin-version">v{plugin.version}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;