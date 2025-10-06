import { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Send, TrendingUp, Activity, BarChart3, Brain, Zap, Settings, LineChart, LogOut, DollarSign, Menu } from "lucide-react";
import AdvancedChart from "./components/AdvancedChart";
import SmartMoneyPanel from "./components/SmartMoneyPanel";
import EnhancedSmartMoneyPanel from "./components/EnhancedSmartMoneyPanel";
import TradingInterface from "./components/TradingInterface";
import SelfEvolvingAI from "./components/SelfEvolvingAI";
import Login from "./pages/Login";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Trading Positions Widget Component
const TradingPositionsWidget = () => {
  const [positions, setPositions] = useState([]);
  const [account, setAccount] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTradingData();
    const interval = setInterval(fetchTradingData, 10000); // Update every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchTradingData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const headers = { 'Authorization': `Bearer ${token}` };

      // Fetch account and positions
      const [accountRes, positionsRes] = await Promise.all([
        axios.get(`${API}/trading/account`, { headers }),
        axios.get(`${API}/trading/positions`, { headers })
      ]);

      if (accountRes.data.status === 'success') {
        setAccount(accountRes.data.account);
      }
      if (positionsRes.data.status === 'success') {
        setPositions(positionsRes.data.positions || []);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching trading data:', error);
      setLoading(false);
    }
  };

  if (loading) return null;

  const totalPnL = account?.unrealized_pnl || 0;
  const openPositionsCount = positions.filter(p => p.status === 'open').length;

  return (
    <div className="trading-widget">
      <div className="widget-title">Trading Übersicht</div>
      
      <div className="trading-stat">
        <span className="stat-label">Offene Positionen</span>
        <span className="stat-value">{openPositionsCount}</span>
      </div>

      <div className="trading-stat">
        <span className="stat-label">Unrealisierter PnL</span>
        <span className={`stat-value ${totalPnL >= 0 ? 'positive' : 'negative'}`}>
          {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)} USD
        </span>
      </div>

      {positions.slice(0, 2).map((pos, idx) => (
        <div key={idx} className="position-mini">
          <div className="position-mini-header">
            <span className="position-symbol">{pos.symbol}</span>
            <span className={`position-side ${pos.side}`}>{pos.side === 'long' ? 'Long' : 'Short'}</span>
          </div>
          <div className="position-mini-stats">
            <span className="position-size">{pos.size} @ {pos.leverage}x</span>
            <span className={`position-pnl ${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
              {pos.unrealized_pnl >= 0 ? '+' : ''}{pos.unrealized_pnl?.toFixed(2)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

function App() {
  // Auth state
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [livePrice, setLivePrice] = useState(null);
  const [indicators, setIndicators] = useState(null);
  const [plugins, setPlugins] = useState([]);
  const [activeView, setActiveView] = useState("chart");
  const [selectedSymbol, setSelectedSymbol] = useState("BTC/USDT");
  const [macroData, setMacroData] = useState(null);
  const [correlations, setCorrelations] = useState(null);
  const [marketOverview, setMarketOverview] = useState(null);
  const messagesEndRef = useRef(null);
  
  // Mobile navigation state
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Global timeframe state for synchronization across all components
  const [globalTimeframe, setGlobalTimeframe] = useState("15m");
  
  // Analysis sub-tab state
  const [analysisTab, setAnalysisTab] = useState("indicators");

  // Check for existing auth on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      setIsAuthenticated(true);
    }
  }, []);
  
  // Mobile detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  // Close mobile menu when view changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [activeView]);

  useEffect(() => {
    if (isAuthenticated) {
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
    }
  }, [isAuthenticated]);

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
        content: "Willkommen bei Lunara Analyze AI! 🧠\n\nIch bin deine selbst-evolvierende KI für Trading-Analysen. Meine Fähigkeiten:\n\n• 🔄 **Self-Evolution**: Kontinuierliche Selbstoptimierung und Lernen\n• 📊 Live-Marktdaten & Smart Money Analyse\n• 🧮 Technische Indikatoren (RSI, MFI, Bollinger Bands)\n• 💹 Paper Trading mit AI-gestützten Empfehlungen\n• 🎯 Backtesting & Strategieentwicklung\n• 🚀 Neue Algorithmen-Entwicklung\n\n**NEU:** Besuche den 'AI Evolution' Tab um meine Selbstverbesserung zu verfolgen!\n\nWie kann ich dir heute helfen?",
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
        timeframe: globalTimeframe,
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
      // Get authentication token
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const response = await axios.post(`${API}/chat`, {
        session_id: sessionId,
        content: input
      }, { headers });

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

  const handleLogin = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);
  };

  // Mobile navigation handlers
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };
  
  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };
  
  const handleViewChange = (view) => {
    setActiveView(view);
    if (isMobile) {
      setIsMobileMenuOpen(false);
    }
  };

  // If not authenticated, show login page
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

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
      {/* Mobile Header */}
      {isMobile && (
        <div className="mobile-header">
          <button className="mobile-menu-button" onClick={toggleMobileMenu}>
            <Menu size={24} />
          </button>
          <div className="mobile-title">
            Lunara Analyze AI
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Abmelden">
            <LogOut size={18} />
          </button>
        </div>
      )}

      {/* Mobile Overlay */}
      {isMobile && (
        <div 
          className={`mobile-overlay ${isMobileMenuOpen ? 'active' : ''}`}
          onClick={closeMobileMenu}
        />
      )}

      {/* Sidebar */}
      <div className={`sidebar ${isMobile && isMobileMenuOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <Brain className="logo-icon" />
            <span>LUNARA ANALYZE AI</span>
          </div>
          {!isMobile && (
            <div className="user-info">
              <span className="username">{user?.username}</span>
              <button className="logout-btn" onClick={handleLogout} title="Abmelden">
                <LogOut size={18} />
              </button>
            </div>
          )}
        </div>

        <nav className="nav-menu">
          <button 
            className={`nav-item ${activeView === 'chat' ? 'active' : ''}`}
            onClick={() => handleViewChange('chat')}
            data-testid="nav-chat"
          >
            <Brain size={20} />
            <span>Chat</span>
          </button>
          <button 
            className={`nav-item ${activeView === 'analysis' ? 'active' : ''}`}
            onClick={() => handleViewChange('analysis')}
            data-testid="nav-analysis"
          >
            <Activity size={20} />
            <span>Analyse</span>
          </button>
          <button 
            className={`nav-item ${activeView === 'chart' ? 'active' : ''}`}
            onClick={() => handleViewChange('chart')}
            data-testid="nav-chart"
          >
            <LineChart size={20} />
            <span>Charts</span>
          </button>
          <button 
            className={`nav-item ${activeView === 'trading' ? 'active' : ''}`}
            onClick={() => handleViewChange('trading')}
            data-testid="nav-trading"
          >
            <DollarSign size={20} />
            <span>Trading</span>
          </button>
          <button 
            className={`nav-item ${activeView === 'evolution' ? 'active' : ''}`}
            onClick={() => handleViewChange('evolution')}
            data-testid="nav-evolution"
          >
            <Brain size={20} />
            <span>AI Evolution</span>
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

        {/* Trading Positions Widget */}
        <TradingPositionsWidget />
      </div>

      {/* Main Content */}
      <div className="main-content">
        {activeView === 'chat' && (
          <>
            <div className="chat-header">
              <h1 data-testid="chat-title">Lunara Analyze AI Assistant</h1>
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
            <h1>Analyse</h1>
            
            {/* Sub-tabs for Analysis */}
            <div className="analysis-tabs">
              <button 
                className={`analysis-tab ${analysisTab === 'indicators' ? 'active' : ''}`}
                onClick={() => setAnalysisTab('indicators')}
              >
                <Zap size={18} />
                <span>Indikatoren</span>
              </button>
              <button 
                className={`analysis-tab ${analysisTab === 'heatmaps' ? 'active' : ''}`}
                onClick={() => setAnalysisTab('heatmaps')}
              >
                <TrendingUp size={18} />
                <span>Heatmaps</span>
              </button>
              <button 
                className={`analysis-tab ${analysisTab === 'news' ? 'active' : ''}`}
                onClick={() => setAnalysisTab('news')}
              >
                <Activity size={18} />
                <span>Wirtschaftsdaten & News</span>
              </button>
              <button 
                className={`analysis-tab ${analysisTab === 'sentiment' ? 'active' : ''}`}
                onClick={() => setAnalysisTab('sentiment')}
              >
                <BarChart3 size={18} />
                <span>Sentiment</span>
              </button>
            </div>

            {/* Timeframe Selector - Global for all tabs */}
            <div className="global-timeframe-selector">
              <label>Timeframe:</label>
              <select value={globalTimeframe} onChange={(e) => setGlobalTimeframe(e.target.value)}>
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minuten</option>
                <option value="15m">15 Minuten</option>
                <option value="30m">30 Minuten</option>
                <option value="1h">1 Stunde</option>
                <option value="4h">4 Stunden</option>
                <option value="1d">1 Tag</option>
                <option value="1w">1 Woche</option>
              </select>
            </div>

            {/* Tab Content */}
            {analysisTab === 'indicators' && (
              <div className="indicators-content">
                <h2 className="section-title">Technische Indikatoren</h2>

                {/* Technical Indicators */}
                {indicators && (
                  <>
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
                      {indicators.indicators?.mfi && (
                        <div className="analysis-card">
                          <h3>MFI</h3>
                          <div className="gauge-value">{indicators.indicators.mfi.toFixed(2)}</div>
                          <div className="gauge-label">
                            {indicators.indicators.mfi < 20 ? 'Überverkauft' : 
                             indicators.indicators.mfi > 80 ? 'Überkauft' : 'Neutral'}
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

            {analysisTab === 'heatmaps' && (
              <div className="heatmaps-content">
                <h2 className="section-title">Smart Money Heatmaps</h2>
                <EnhancedSmartMoneyPanel globalTimeframe={globalTimeframe} />
              </div>
            )}

            {analysisTab === 'news' && (
              <div className="news-content">
                <h2 className="section-title">Wirtschaftsdaten & News</h2>
                
                {/* Makrodaten Section */}
                {macroData && (
                  <>
                    <h3 className="subsection-title">Makroökonomische Daten</h3>
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
                    <h3 className="subsection-title">Korrelationsanalyse</h3>
                    <div className="correlation-grid">
                      {Object.entries(correlations).map(([key, value]) => (
                        <div key={key} className="correlation-card">
                          <div className="correlation-label">{key.replace('BTC_vs_', 'BTC ⟷ ').replace('_', ' ')}</div>
                          <div className={`correlation-value ${value > 0.5 ? 'strong-positive' : value < -0.5 ? 'strong-negative' : 'weak'}`}>
                            {(value * 100).toFixed(1)}%
                          </div>
                          <div className="correlation-bar">
                            <div className="correlation-fill" style={{width: `${Math.abs(value) * 100}%`, backgroundColor: value > 0 ? '#10b981' : '#ef4444'}}></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}

                <div className="news-feed">
                  <h3 className="subsection-title">Aktuelle News</h3>
                  <p className="coming-soon">News-Integration wird in Phase 4 hinzugefügt...</p>
                </div>
              </div>
            )}

            {analysisTab === 'sentiment' && (
              <div className="sentiment-content">
                <h2 className="section-title">Market Sentiment Analyse</h2>
                <p className="coming-soon">Sentiment-Analyse wird in Phase 4 hinzugefügt...</p>
              </div>
            )}
          </div>
        )}

        {activeView === 'chart' && (
          <div className="chart-view" style={{padding: '24px', height: '100%'}}>
            <AdvancedChart 
              symbol={selectedSymbol} 
              onSymbolChange={setSelectedSymbol}
              globalTimeframe={globalTimeframe}
              setGlobalTimeframe={setGlobalTimeframe}
            />
          </div>
        )}

        {activeView === 'trading' && (
          <div className="trading-view">
            <TradingInterface />
          </div>
        )}

        {activeView === 'evolution' && (
          <div className="evolution-view">
            <SelfEvolvingAI />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;