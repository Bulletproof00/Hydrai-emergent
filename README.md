# CHAiNALYZE - Advanced Crypto Trading & Analysis Platform

**CHAiNALYZE** is a comprehensive, AI-powered cryptocurrency trading and analysis platform with self-evolving capabilities, real-time market data, and advanced technical analysis tools.

## 🚀 Features

### Core Features
- **🧠 AI-Powered Analysis** - Self-evolving AI with continuous learning capabilities  
- **📊 Real-Time Market Data** - Multi-tier data system (Binance → CoinGecko → Synthetic fallbacks)
- **💹 Paper Trading** - Risk-free trading simulation with $10,000 virtual account
- **📈 Advanced Charting** - Professional candlestick charts with technical indicators
- **🤖 Smart Money Analysis** - Institutional trading patterns and liquidation heatmaps
- **📰 News & Sentiment** - Real-time market sentiment and financial news analysis

### AI Evolution System
- **Self-Improving AI** - Continuous optimization and learning cycles
- **Performance Tracking** - Real-time evolution metrics and performance scores
- **Strategy Development** - Automated trading strategy generation and backtesting

### Technical Analysis
- **Technical Indicators** - RSI, MFI, SMA, EMA, Bollinger Bands
- **Pattern Recognition** - Candlestick patterns (Doji, Hammer, Shooting Star)
- **Correlation Analysis** - BTC vs traditional markets (SPX, DXY, M2)
- **Smart Money Indicators** - Open Interest, Funding Rates, Liquidation data

### Multi-Language Support
- 🇩🇪 German (Deutsch)
- 🇺🇸 English
- 🇹🇷 Turkish (Türkçe)
- 🇪🇸 Spanish (Español)
- 🇨🇳 Chinese (中文)

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **MongoDB** - NoSQL database for market data and user sessions
- **Gemini AI** - Google's advanced AI model for analysis
- **CCXT** - Cryptocurrency exchange trading library
- **WebSockets** - Real-time data streaming

### Frontend
- **React** - Modern JavaScript UI library
- **Tailwind CSS** - Utility-first CSS framework
- **i18next** - Internationalization framework
- **Canvas API** - Custom chart rendering

### Data Sources
- **Binance API** - Primary crypto data source
- **CoinGecko API** - Fallback data provider (geographic restriction bypass)
- **Synthetic Data** - Last-resort fallback for continuous operation

## 📋 System Requirements

- **OS:** Ubuntu 20.04+ / Debian 10+ / CentOS 8+
- **RAM:** 4GB minimum, 8GB+ recommended
- **CPU:** 2 cores minimum, 4+ cores recommended
- **Storage:** 20GB free space
- **Ports:** 80, 443, 3000, 8001, 27017

## 🚀 Quick Installation

### 1. System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip nodejs npm mongodb supervisor nginx git curl
npm install -g yarn

# Python Virtual Environment
python3 -m venv /opt/chainalyze/venv
source /opt/chainalyze/venv/bin/activate
```

### 2. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/chainalyze.git /opt/chainalyze
cd /opt/chainalyze
```

### 3. Backend Setup
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Frontend Setup
```bash
cd ../frontend
yarn install
```

### 5. Configuration
Create `.env` files:

**Backend `.env`:**
```env
MONGO_URL=mongodb://localhost:27017/chainalyze_ai
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_secure_jwt_secret_key
ENVIRONMENT=production
DEBUG=False
```

**Frontend `.env`:**
```env
REACT_APP_BACKEND_URL=http://your-server-ip:8001
```

### 6. Start Services
```bash
# MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Configure Supervisor (see documentation for detailed configs)
sudo supervisorctl start chainalyze-backend
sudo supervisorctl start chainalyze-frontend
```

## 🔧 API Endpoints

### Core APIs
- `GET /api/health` - System health check
- `POST /api/chat` - AI chat interface
- `GET /api/sessions` - Chat session management

### Trading System
- `GET /api/trading/account` - Paper trading account
- `POST /api/trading/order` - Place trading orders
- `GET /api/trading/positions` - Active positions
- `GET /api/trading/portfolio` - Portfolio overview

### Market Data
- `GET /api/chart-data/{symbol}` - OHLCV candlestick data
- `GET /api/realtime/latest` - Live cryptocurrency prices
- `GET /api/markets` - Market overview

### AI Evolution
- `GET /api/ai/evolution/status` - AI evolution status
- `POST /api/ai/evolution/chat` - Evolution AI chat
- `GET /api/ai/coding/plugins` - Self-coding plugins

### Analysis Tools
- `GET /api/correlations` - Market correlations
- `GET /api/market-sentiment` - Sentiment analysis
- `GET /api/financial-news` - Latest financial news

## 🎨 Screenshots

### Trading Interface
Professional paper trading with real-time data and advanced order types.

### AI Evolution Dashboard  
Track your AI's learning progress and performance improvements.

### Advanced Charts
Professional candlestick charts with technical indicators and pattern recognition.

### Multi-Language Support
Full interface available in 5 languages.

## 🔑 Required API Keys

### Essential (for full functionality)
- **Gemini AI API Key** - [Get from Google AI Studio](https://makersuite.google.com/app/apikey)

### Optional (enhanced features)
- **Binance API Key** - [Get from Binance](https://www.binance.com/en/binance-api)

*Note: The system works without API keys using fallback data sources.*

## 🏗️ Architecture

### Multi-Tier Fallback System
1. **Primary:** Binance API (fastest, most accurate)
2. **Fallback:** CoinGecko API (geographic restriction bypass)
3. **Emergency:** Synthetic data generation (ensures continuous operation)

### AI Evolution Pipeline
1. **Data Collection** - Continuous market data ingestion
2. **Pattern Analysis** - AI identifies trading patterns
3. **Strategy Evolution** - Self-improving trading algorithms
4. **Performance Tracking** - Real-time evolution metrics

## 📊 Performance Metrics

- **Backend API Success Rate:** 85%+
- **Chart Data Availability:** 99%+  
- **Real-time Data Latency:** <500ms
- **AI Evolution Cycles:** Automated every 8 hours

## 🛡️ Security Features

- **JWT Authentication** - Secure user sessions
- **API Rate Limiting** - Prevents abuse
- **Input Validation** - SQL injection protection
- **CORS Security** - Cross-origin request protection

## 📈 Production Deployment

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
    }
}
```

### SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com
```

### Process Management
```bash
# Status check
sudo supervisorctl status

# Restart services  
sudo supervisorctl restart chainalyze-backend
sudo supervisorctl restart chainalyze-frontend
```

## 🔄 Updates & Maintenance

### Update System
```bash
cd /opt/chainalyze
git pull origin main
cd backend && pip install -r requirements.txt
cd ../frontend && yarn install
sudo supervisorctl restart chainalyze-backend chainalyze-frontend
```

### Log Monitoring
```bash
# Backend logs
sudo tail -f /var/log/chainalyze-backend.out.log

# Frontend logs
sudo tail -f /var/log/chainalyze-frontend.out.log
```

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
sudo netstat -tulpn | grep :3000
sudo kill -9 PID
```

**MongoDB Connection:**
```bash
sudo systemctl status mongod
sudo systemctl restart mongod
```

**Permission Issues:**
```bash
sudo chown -R www-data:www-data /opt/chainalyze
sudo chmod -R 755 /opt/chainalyze
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Binance API** - Primary cryptocurrency data source
- **CoinGecko API** - Reliable fallback data provider
- **Google Gemini AI** - Advanced AI analysis capabilities
- **MongoDB** - Robust data storage solution
- **React Community** - Excellent frontend framework

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review troubleshooting section above

## 🚀 Future Roadmap

- [ ] Mobile app development
- [ ] Advanced backtesting engine
- [ ] Social trading features
- [ ] Multi-exchange support
- [ ] Advanced AI strategies
- [ ] Portfolio optimization tools

---

**CHAiNALYZE** - Revolutionizing cryptocurrency trading through AI-powered analysis and continuous evolution.