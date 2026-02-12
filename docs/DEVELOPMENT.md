# CHAiNALYZE Development Guide

## Project Structure

```
chainalyze/
├── backend/                  # FastAPI backend
│   ├── modules/              # Core modules
│   │   ├── auth/            # Authentication
│   │   ├── ai_data_module.py # AI data processing
│   │   ├── binance_data.py  # Binance integration
│   │   ├── coingecko_provider.py # CoinGecko fallback
│   │   ├── enhanced_smart_money.py # Smart money analysis
│   │   ├── integrated_ai_system.py # Main AI system
│   │   ├── paper_trading.py # Trading simulation
│   │   ├── real_time_enhanced.py # Real-time data
│   │   └── self_evolving_ai.py # AI evolution
│   ├── requirements.txt     # Python dependencies
│   └── server.py           # Main FastAPI server
├── frontend/               # React frontend
│   ├── public/            # Static files
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   ├── locales/       # Translations
│   │   ├── pages/         # Page components
│   │   └── utils/         # Utility functions
│   ├── package.json       # Node.js dependencies
│   └── tailwind.config.js # Tailwind CSS config
└── docs/                  # Documentation
```

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- MongoDB 6.0+
- Git

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
python server.py
```

### Frontend Development
```bash
cd frontend
yarn install
yarn start
```

## API Development

### Adding New Endpoints
1. Add route in `server.py`
2. Create module in `backend/modules/`
3. Update API documentation
4. Add tests

Example:
```python
@api_router.get("/api/new-feature")
async def new_feature():
    return {"status": "success", "data": "example"}
```

### Authentication
All protected endpoints require JWT token:
```python
async def protected_endpoint(authorization: str = Header(...)):
    user = await get_current_user(authorization)
    # Your logic here
```

## Frontend Development

### Component Structure
```javascript
// components/NewComponent.js
import React from 'react';
import { useTranslation } from 'react-i18next';

const NewComponent = () => {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1>{t('title')}</h1>
    </div>
  );
};

export default NewComponent;
```

### Adding Translations
Update all language files in `src/locales/`:
```json
{
  "title": "New Feature",
  "description": "Feature description"
}
```

### State Management
Use React hooks for local state:
```javascript
const [data, setData] = useState([]);
const [loading, setLoading] = useState(false);
```

## Database Schema

### Collections
- `users` - User accounts
- `chat_sessions` - Chat history
- `trading_accounts` - Paper trading data
- `market_data_historical` - Historical prices
- `ai_evolution_logs` - AI learning data

### Example Document
```javascript
// users collection
{
  "_id": "user_uuid",
  "email": "user@example.com",
  "created_at": "2025-01-01T00:00:00Z",
  "preferences": {
    "language": "en",
    "theme": "dark"
  }
}
```

## AI Evolution System

### Adding New Evolution Strategies
1. Create strategy in `modules/self_evolving_ai.py`
2. Register in evolution pipeline
3. Add performance metrics
4. Test with paper trading

Example:
```python
async def new_strategy(self, market_data):
    # Analyze market conditions
    signal = self.analyze_pattern(market_data)
    return {
        'action': 'buy' if signal > 0.7 else 'hold',
        'confidence': signal,
        'reasoning': 'Pattern detected'
    }
```

## Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
yarn test
```

### API Testing
```bash
# Test endpoint
curl -X GET http://localhost:8001/api/health

# Authenticated endpoint
curl -X GET http://localhost:8001/api/protected \
  -H "Authorization: Bearer your_jwt_token"
```

## Deployment

### Local Development
```bash
# Start all services
sudo supervisorctl start chainalyze-backend
sudo supervisorctl start chainalyze-frontend
```

### Production Deployment
1. Configure environment variables
2. Set up Nginx reverse proxy
3. Configure SSL certificates
4. Set up monitoring

## Performance Optimization

### Backend
- Use async/await for I/O operations
- Implement caching for expensive operations
- Use database indexes
- Monitor API response times

### Frontend
- Lazy load components
- Optimize bundle size
- Use React.memo for expensive components
- Implement virtual scrolling for large lists

## Security Considerations

### API Security
- Validate all inputs
- Use parameterized queries
- Implement rate limiting
- Log security events

### Frontend Security
- Sanitize user inputs
- Use HTTPS in production
- Implement CSP headers
- Validate data from APIs

## Monitoring & Logging

### Backend Logs
```bash
tail -f /var/log/supervisor/chainalyze-backend.out.log
```

### Performance Monitoring
- API response times
- Database query performance
- Memory usage
- Error rates

## Contributing Guidelines

1. Fork the repository
2. Create feature branch
3. Follow code style guidelines
4. Add tests for new features
5. Update documentation
6. Submit pull request

### Code Style
- Python: Follow PEP 8
- JavaScript: Use ESLint configuration
- Use meaningful variable names
- Add comments for complex logic

## Troubleshooting

### Common Issues

**Module Import Errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Database Connection:**
```bash
# Check MongoDB status
sudo systemctl status mongod
```

**Port Conflicts:**
```bash
# Check what's using port
sudo netstat -tulpn | grep :8001
```

### Debug Mode
Enable debug logging:
```bash
export DEBUG=True
python server.py
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Tailwind CSS](https://tailwindcss.com/)

## Support

For development questions:
1. Check this documentation
2. Search existing issues
3. Create new issue with details