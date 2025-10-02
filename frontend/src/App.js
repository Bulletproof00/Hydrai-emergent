import { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Send, TrendingUp, Activity, BarChart3, Brain, Zap, Settings } from "lucide-react";

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
    
    const priceInterval = setInterval(fetchLivePrice, 10000);
    const indicatorInterval = setInterval(fetchIndicators, 30000);
    
    return () => {
      clearInterval(priceInterval);
      clearInterval(indicatorInterval);
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
        limit: 100,
        indicators: ["rsi", "mfi", "bollinger"]
      });
      setIndicators(response.data);
    } catch (error) {
      console.error("Error fetching indicators:", error);
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
            <h1>Marktanalyse</h1>
            {indicators && (
              <div className="analysis-grid">
                <div className="analysis-card">
                  <h3>Aktuelle Daten</h3>
                  <p className="analysis-label">Symbol</p>
                  <p className="analysis-value">{indicators.symbol}</p>
                  <p className="analysis-label">Aktueller Preis</p>
                  <p className="analysis-value">${indicators.current_price?.toLocaleString()}</p>
                  <p className="analysis-label">Zeitrahmen</p>
                  <p className="analysis-value">{indicators.timeframe}</p>
                </div>

                <div className="analysis-card">
                  <h3>RSI (Relative Strength Index)</h3>
                  <div className="rsi-gauge">
                    <div className="gauge-value">{indicators.indicators?.rsi?.toFixed(2)}</div>
                    <div className="gauge-label">
                      {indicators.indicators?.rsi < 30 ? 'Überverkauft' : 
                       indicators.indicators?.rsi > 70 ? 'Überkauft' : 'Neutral'}
                    </div>
                  </div>
                </div>

                <div className="analysis-card">
                  <h3>MFI (Money Flow Index)</h3>
                  <div className="rsi-gauge">
                    <div className="gauge-value">{indicators.indicators?.mfi?.toFixed(2)}</div>
                  </div>
                </div>

                <div className="analysis-card">
                  <h3>Bollinger Bands</h3>
                  {indicators.indicators?.bollinger && (
                    <div className="bollinger-data">
                      <div className="bb-row">
                        <span>Upper Band:</span>
                        <span>${indicators.indicators.bollinger.upper.toFixed(2)}</span>
                      </div>
                      <div className="bb-row">
                        <span>Middle Band:</span>
                        <span>${indicators.indicators.bollinger.middle.toFixed(2)}</span>
                      </div>
                      <div className="bb-row">
                        <span>Lower Band:</span>
                        <span>${indicators.indicators.bollinger.lower.toFixed(2)}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
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