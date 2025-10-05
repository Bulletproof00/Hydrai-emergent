import { useState } from 'react';
import axios from 'axios';
import { Brain } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Login = ({ onLogin }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
      const payload = isRegister 
        ? { email, password, username }
        : { email, password };

      const response = await axios.post(`${BACKEND_URL}${endpoint}`, payload);
      
      // Store token and user data
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      // Call onLogin callback
      onLogin(response.data.user, response.data.access_token);

    } catch (err) {
      setError(err.response?.data?.detail || 'Ein Fehler ist aufgetreten');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <Brain className="login-logo-icon" size={48} />
          <h1>Lunara Analyze AI</h1>
          <p>Professionelle Krypto Trading Plattform</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {isRegister && (
            <div className="form-group">
              <label>Benutzername</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Benutzername"
                required
                minLength={3}
                data-testid="register-username"
              />
            </div>
          )}

          <div className="form-group">
            <label>E-Mail</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="deine@email.com"
              required
              data-testid="login-email"
            />
          </div>

          <div className="form-group">
            <label>Passwort</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
              data-testid="login-password"
            />
          </div>

          {error && <div className="error-message" data-testid="error-message">{error}</div>}

          <button 
            type="submit" 
            className="login-button" 
            disabled={loading}
            data-testid="login-submit"
          >
            {loading ? 'Lädt...' : (isRegister ? 'Registrieren' : 'Anmelden')}
          </button>
        </form>

        <div className="login-toggle">
          <button 
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
            }}
            data-testid="toggle-register"
          >
            {isRegister ? 'Bereits ein Konto? Anmelden' : 'Neu hier? Registrieren'}
          </button>
        </div>
      </div>

      <div className="login-features">
        <div className="feature-item">
          <h3>📊 Erweiterte Charts</h3>
          <p>TradingView-ähnliche Candlestick-Charts mit allen Zeiträumen</p>
        </div>
        <div className="feature-item">
          <h3>💰 Paper Trading</h3>
          <p>Risikofrei mit $10.000 Startkapital handeln</p>
        </div>
        <div className="feature-item">
          <h3>🤖 KI-Analyse</h3>
          <p>Gemini-gestützte Pattern-Erkennung und Marktanalyse</p>
        </div>
        <div className="feature-item">
          <h3>📈 Smart Money</h3>
          <p>Orderflow, Liquidations und Funding Rates</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
