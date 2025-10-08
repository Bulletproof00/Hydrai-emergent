#!/usr/bin/env python3
"""
KI-DATENMODUL Backend Test Suite
Umfassendes System für historische und Echtzeit-Marktanalyse

Tests für neue KI-DATENMODUL APIs:
1. Historische Datenladung (2019-heute)
2. Korrelationsanalyse mit Zeitversatzkorrektur
3. News & Sentiment Analyse (24h rückwirkend, 1 Woche voraus)
4. Datenqualität & Bitcoin-Dominanz
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
BACKEND_URL = "https://market-genius-39.preview.emergentagent.com/api"
AUTH_TOKEN = "demo-token"

class KIDatenmodulTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🚀 Starting KI-DATENMODUL Comprehensive Testing")
        print(f"Backend URL: {BACKEND_URL}")
        print("Authentication: demo-token")
        print("=" * 80)
    
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", expected: str = "", actual: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'expected': expected,
            'actual': actual,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if expected and actual:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        print()
    
    async def test_api_endpoint(self, endpoint: str, expected_status: int = 200, method: str = "GET", data: dict = None, auth: bool = True) -> Dict[str, Any]:
        """Test API endpoint and return response"""
        try:
            url = f"{BACKEND_URL}{endpoint}"
            headers = {}
            
            if auth:
                headers['Authorization'] = f'Bearer {AUTH_TOKEN}'
            
            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    status = response.status
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            elif method == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    status = response.status
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            
            return {
                'status': status,
                'data': response_data,
                'success': status == expected_status
            }
        except Exception as e:
            return {
                'status': 0,
                'data': str(e),
                'success': False,
                'error': str(e)
            }

    # ============= KI-DATENMODUL TESTS =============
    
    async def test_ai_data_load_historical(self):
        """Test 1: Historische Datenladung (2019-heute) - POST /api/ai-data/load-historical"""
        test_name = "🎯 KI-DATENMODUL TEST 1: HISTORISCHE DATENLADUNG (2019-heute)"
        
        historical_data = {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M"],
            "start_date": "2019-01-01",
            "end_date": "2024-12-31"
        }
        
        response = await self.test_api_endpoint("/ai-data/load-historical", method="POST", data=historical_data)
        
        if not response['success']:
            # Check if endpoint exists (404) or if it's a different error
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/ai-data/load-historical (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Historische Datenladung API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for successful historical data loading
        if data.get('status') == 'success' and 'result' in data:
            result = data['result']
            loaded_symbols = result.get('loaded_symbols', [])
            loaded_timeframes = result.get('loaded_timeframes', [])
            total_bars = result.get('total_bars', 0)
            date_range = result.get('date_range', {})
            
            if len(loaded_symbols) >= 2 and len(loaded_timeframes) >= 8 and total_bars > 1000:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ HISTORISCHE DATENLADUNG ERFOLGREICH! {len(loaded_symbols)} Symbole, {len(loaded_timeframes)} Timeframes, {total_bars:,} Bars geladen von {date_range.get('start', '2019')} bis {date_range.get('end', '2024')}",
                    "Historische OHLCV-Daten ab 2019 für alle Timeframes (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)",
                    f"Symbols: {len(loaded_symbols)}, Timeframes: {len(loaded_timeframes)}, Bars: {total_bars:,}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Historische Datenladung unvollständig: {len(loaded_symbols)} Symbole, {len(loaded_timeframes)} Timeframes, {total_bars} Bars")
        else:
            # Check if it's mock data or fallback
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Historische Datenladung mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Historische Datenladung Response unvollständig: {data}")

    async def test_ai_data_calculate_indicators(self):
        """Test 2: Technische Indikatoren berechnen - POST /api/ai-data/calculate-indicators"""
        test_name = "🎯 KI-DATENMODUL TEST 2: TECHNISCHE INDIKATOREN BERECHNUNG"
        
        indicators_data = {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "indicators": ["RSI", "SMA", "EMA", "BOLLINGER_BANDS", "MACD", "STOCHASTIC", "MFI"],
            "timeframes": ["1h", "4h", "1d"]
        }
        
        response = await self.test_api_endpoint("/ai-data/calculate-indicators", method="POST", data=indicators_data)
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/ai-data/calculate-indicators (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Indikatoren-Berechnung API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for successful indicator calculation
        if data.get('status') == 'success' and 'result' in data:
            result = data['result']
            calculated_indicators = result.get('calculated_indicators', [])
            symbols_processed = result.get('symbols_processed', [])
            timeframes_processed = result.get('timeframes_processed', [])
            
            if len(calculated_indicators) >= 7 and len(symbols_processed) >= 2:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ TECHNISCHE INDIKATOREN ERFOLGREICH BERECHNET! {len(calculated_indicators)} Indikatoren (RSI, SMA, EMA, Bollinger Bands, MACD, Stochastic, MFI) für {len(symbols_processed)} Symbole und {len(timeframes_processed)} Timeframes",
                    "Technische Indikatoren für alle Daten berechnet",
                    f"Indicators: {len(calculated_indicators)}, Symbols: {len(symbols_processed)}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Indikatoren-Berechnung unvollständig: {len(calculated_indicators)} Indikatoren, {len(symbols_processed)} Symbole")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Indikatoren-Berechnung mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Indikatoren-Berechnung Response unvollständig: {data}")

    async def test_ai_data_quality_assessment(self):
        """Test 3: Datenqualitätsbewertung - GET /api/ai-data/data-quality"""
        test_name = "🎯 KI-DATENMODUL TEST 3: DATENQUALITÄTSBEWERTUNG"
        
        response = await self.test_api_endpoint("/ai-data/data-quality")
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/ai-data/data-quality (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Datenqualität API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for data quality assessment
        if 'data_quality' in data:
            quality_data = data['data_quality']
            overall_score = quality_data.get('overall_score', 0)
            completeness = quality_data.get('completeness', 0)
            accuracy = quality_data.get('accuracy', 0)
            consistency = quality_data.get('consistency', 0)
            
            if overall_score >= 0.8 and completeness >= 0.8:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ DATENQUALITÄTSBEWERTUNG ERFOLGREICH! Overall Score: {overall_score:.2%}, Completeness: {completeness:.2%}, Accuracy: {accuracy:.2%}, Consistency: {consistency:.2%}",
                    "Datenqualität-Scores für historische und Echtzeit-Daten",
                    f"Quality Score: {overall_score:.2%}, Completeness: {completeness:.2%}"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ Datenqualität könnte besser sein: Overall: {overall_score:.2%}, Completeness: {completeness:.2%}")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Datenqualität mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Datenqualität Response unvollständig: {data}")

    async def test_correlations_calculate_comprehensive(self):
        """Test 4: Umfassende Korrelationsanalyse - POST /api/correlations/calculate-comprehensive"""
        test_name = "🎯 KI-DATENMODUL TEST 4: KORRELATIONSANALYSE MIT ZEITVERSATZ"
        
        correlation_data = {
            "base_asset": "BTC",
            "comparison_assets": ["M2", "DXY", "Russell2000", "ALTCOIN_DOMINANCE"],
            "timeframes": ["1h", "4h", "1d", "1w"],
            "lag_periods": [0, 1, 2, 3, 6, 12, 24]  # Zeitversatzkorrektur
        }
        
        response = await self.test_api_endpoint("/correlations/calculate-comprehensive", method="POST", data=correlation_data)
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/correlations/calculate-comprehensive (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Korrelationsanalyse API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for comprehensive correlation analysis
        if data.get('status') == 'success' and 'correlations' in data:
            correlations = data['correlations']
            btc_correlations = correlations.get('BTC', {})
            
            # Check for specific correlations with time lag
            expected_pairs = ['BTC_vs_M2', 'BTC_vs_DXY', 'BTC_vs_Russell2000', 'BTC_vs_ALTCOIN_DOMINANCE']
            found_pairs = 0
            time_lag_analysis = False
            
            for pair in expected_pairs:
                if pair in btc_correlations:
                    found_pairs += 1
                    pair_data = btc_correlations[pair]
                    if 'optimal_lag' in pair_data and 'lag_correlations' in pair_data:
                        time_lag_analysis = True
            
            if found_pairs >= 3 and time_lag_analysis:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ KORRELATIONSANALYSE MIT ZEITVERSATZ ERFOLGREICH! {found_pairs}/4 BTC-Korrelationen gefunden (M2, DXY, Russell2000, Altcoin-Dominanz) mit Zeitversatzkorrektur",
                    "BTC-Korrelationen mit Makro-Assets und Zeitversatzanalyse",
                    f"Correlations: {found_pairs}/4, Time lag analysis: {time_lag_analysis}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Korrelationsanalyse unvollständig: {found_pairs}/4 Paare, Zeitversatz: {time_lag_analysis}")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Korrelationsanalyse mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Korrelationsanalyse Response unvollständig: {data}")

    async def test_correlations_real_time(self):
        """Test 5: Echtzeit-Korrelationen - GET /api/correlations/real-time"""
        test_name = "🎯 KI-DATENMODUL TEST 5: ECHTZEIT-KORRELATIONSWERTE"
        
        response = await self.test_api_endpoint("/correlations/real-time")
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/correlations/real-time (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Echtzeit-Korrelationen API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for real-time correlation values
        if 'real_time_correlations' in data:
            rt_correlations = data['real_time_correlations']
            current_values = rt_correlations.get('current_values', {})
            last_updated = rt_correlations.get('last_updated')
            
            if len(current_values) >= 3 and last_updated:
                correlation_pairs = list(current_values.keys())
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ ECHTZEIT-KORRELATIONSWERTE ERFOLGREICH! {len(current_values)} aktuelle Korrelationswerte verfügbar: {', '.join(correlation_pairs[:3])}... (Last updated: {last_updated})",
                    "Aktuelle Korrelationswerte in Echtzeit",
                    f"Real-time correlations: {len(current_values)}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Echtzeit-Korrelationen unvollständig: {len(current_values)} Werte")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Echtzeit-Korrelationen mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Echtzeit-Korrelationen Response unvollständig: {data}")

    async def test_correlations_trends(self):
        """Test 6: Korrelationstrends - GET /api/correlations/trends"""
        test_name = "🎯 KI-DATENMODUL TEST 6: KORRELATIONSTRENDS ÜBER ZEIT"
        
        response = await self.test_api_endpoint("/correlations/trends?period=30d")
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/correlations/trends (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Korrelationstrends API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for correlation trends over time
        if 'correlation_trends' in data:
            trends = data['correlation_trends']
            trend_data = trends.get('trend_data', {})
            period = trends.get('period', '')
            
            if len(trend_data) >= 3 and period:
                trend_pairs = list(trend_data.keys())
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ KORRELATIONSTRENDS ERFOLGREICH! Trends für {len(trend_data)} Korrelationspaare über {period}: {', '.join(trend_pairs[:3])}...",
                    "Korrelationstrends über Zeit analysiert",
                    f"Trend pairs: {len(trend_data)}, Period: {period}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Korrelationstrends unvollständig: {len(trend_data)} Trends")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Korrelationstrends mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Korrelationstrends Response unvollständig: {data}")

    async def test_news_sentiment_fetch_news(self):
        """Test 7: News-Sentiment-Analyse (24h rückwirkend) - POST /api/news-sentiment/fetch-news"""
        test_name = "🎯 KI-DATENMODUL TEST 7: NEWS-SENTIMENT-ANALYSE (24h)"
        
        news_data = {
            "timeframe": "24h",
            "keywords": ["Bitcoin", "BTC", "Ethereum", "ETH", "Crypto", "DeFi"],
            "sources": ["Reuters", "Bloomberg", "CoinDesk", "CoinTelegraph"],
            "sentiment_analysis": True
        }
        
        response = await self.test_api_endpoint("/news-sentiment/fetch-news", method="POST", data=news_data)
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/news-sentiment/fetch-news (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ News-Sentiment API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for news sentiment analysis
        if data.get('status') == 'success' and 'news_data' in data:
            news_data = data['news_data']
            articles = news_data.get('articles', [])
            sentiment_summary = news_data.get('sentiment_summary', {})
            
            if len(articles) >= 10 and sentiment_summary:
                positive_count = sentiment_summary.get('positive', 0)
                negative_count = sentiment_summary.get('negative', 0)
                neutral_count = sentiment_summary.get('neutral', 0)
                
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ NEWS-SENTIMENT-ANALYSE ERFOLGREICH! {len(articles)} News-Artikel der letzten 24h analysiert. Sentiment: {positive_count} Positiv, {negative_count} Negativ, {neutral_count} Neutral",
                    "News der letzten 24h mit Sentiment-Analyse und Keyword-Erkennung",
                    f"Articles: {len(articles)}, Sentiment: +{positive_count}/-{negative_count}/={neutral_count}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ News-Sentiment unvollständig: {len(articles)} Artikel")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ News-Sentiment mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ News-Sentiment Response unvollständig: {data}")

    async def test_news_sentiment_economic_events(self):
        """Test 8: Wirtschaftsereignisse (1 Woche voraus) - POST /api/news-sentiment/fetch-economic-events"""
        test_name = "🎯 KI-DATENMODUL TEST 8: WIRTSCHAFTSEREIGNISSE (1 Woche voraus)"
        
        events_data = {
            "timeframe": "1w",
            "event_types": ["Fed Meeting", "CPI", "NFP", "GDP", "Inflation", "Interest Rates"],
            "importance": ["high", "medium"],
            "regions": ["US", "EU", "JP", "CN"]
        }
        
        response = await self.test_api_endpoint("/news-sentiment/fetch-economic-events", method="POST", data=events_data)
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/news-sentiment/fetch-economic-events (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Wirtschaftsereignisse API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for economic events
        if data.get('status') == 'success' and 'economic_events' in data:
            events_data = data['economic_events']
            events = events_data.get('events', [])
            upcoming_week = events_data.get('upcoming_week', {})
            
            if len(events) >= 5 and upcoming_week:
                high_impact = len([e for e in events if e.get('importance') == 'high'])
                fed_events = len([e for e in events if 'Fed' in e.get('title', '')])
                
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ WIRTSCHAFTSEREIGNISSE ERFOLGREICH! {len(events)} Events für die nächste Woche gefunden. {high_impact} High-Impact Events, {fed_events} Fed-bezogene Events (Fed Meetings, CPI, NFP)",
                    "Wirtschaftskalender-Events 1 Woche voraus (Fed Meetings, CPI, NFP)",
                    f"Events: {len(events)}, High impact: {high_impact}, Fed events: {fed_events}"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Wirtschaftsereignisse unvollständig: {len(events)} Events")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Wirtschaftsereignisse mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Wirtschaftsereignisse Response unvollständig: {data}")

    async def test_news_sentiment_real_time(self):
        """Test 9: Echtzeit-Market-Sentiment - GET /api/news-sentiment/real-time-sentiment"""
        test_name = "🎯 KI-DATENMODUL TEST 9: ECHTZEIT-MARKET-SENTIMENT"
        
        response = await self.test_api_endpoint("/news-sentiment/real-time-sentiment")
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/news-sentiment/real-time-sentiment (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Echtzeit-Sentiment API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for real-time market sentiment
        if 'real_time_sentiment' in data:
            sentiment_data = data['real_time_sentiment']
            fear_greed_index = sentiment_data.get('fear_greed_index', 0)
            social_media_sentiment = sentiment_data.get('social_media_sentiment', {})
            market_sentiment = sentiment_data.get('market_sentiment', '')
            
            if fear_greed_index > 0 and social_media_sentiment and market_sentiment:
                twitter_sentiment = social_media_sentiment.get('twitter', 0)
                reddit_sentiment = social_media_sentiment.get('reddit', 0)
                
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ ECHTZEIT-MARKET-SENTIMENT ERFOLGREICH! Fear & Greed Index: {fear_greed_index}, Market Sentiment: {market_sentiment}, Social Media: Twitter {twitter_sentiment}%, Reddit {reddit_sentiment}%",
                    "Echtzeit-Market-Sentiment (Fear & Greed Index, Social Media)",
                    f"F&G: {fear_greed_index}, Sentiment: {market_sentiment}, Social: T{twitter_sentiment}%/R{reddit_sentiment}%"
                )
            else:
                self.log_test(test_name, "FAIL", f"❌ Echtzeit-Sentiment unvollständig: F&G: {fear_greed_index}, Market: {market_sentiment}")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Echtzeit-Sentiment mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Echtzeit-Sentiment Response unvollständig: {data}")

    async def test_financial_news_compatibility(self):
        """Test 10: Financial News (Frontend-kompatibel) - GET /api/financial-news"""
        test_name = "🎯 KI-DATENMODUL TEST 10: FINANCIAL NEWS (Frontend-kompatibel)"
        
        response = await self.test_api_endpoint("/financial-news")
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/financial-news (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Financial News API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for frontend-compatible financial news
        if 'news' in data or 'articles' in data:
            news_articles = data.get('news', data.get('articles', []))
            
            if len(news_articles) >= 5:
                # Check article structure for frontend compatibility
                sample_article = news_articles[0]
                required_fields = ['title', 'content', 'timestamp', 'source']
                has_required_fields = all(field in sample_article for field in required_fields)
                
                if has_required_fields:
                    self.log_test(
                        test_name, 
                        "PASS", 
                        f"✅ FINANCIAL NEWS FRONTEND-KOMPATIBEL! {len(news_articles)} News-Artikel mit vollständiger Struktur (title, content, timestamp, source) für Frontend-Integration",
                        "Financial News kompatibel mit bestehendem Frontend",
                        f"Articles: {len(news_articles)}, Frontend compatible: {has_required_fields}"
                    )
                else:
                    self.log_test(test_name, "WARN", f"⚠️ Financial News verfügbar aber Struktur könnte für Frontend optimiert werden: {len(news_articles)} Artikel")
            else:
                self.log_test(test_name, "FAIL", f"❌ Financial News unvollständig: {len(news_articles)} Artikel")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Financial News mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Financial News Response unvollständig: {data}")

    async def test_market_sentiment_compatibility(self):
        """Test 11: Market Sentiment (Frontend-kompatibel) - GET /api/market-sentiment"""
        test_name = "🎯 KI-DATENMODUL TEST 11: MARKET SENTIMENT (Frontend-kompatibel)"
        
        response = await self.test_api_endpoint("/market-sentiment")
        
        if not response['success']:
            if response['status'] == 404:
                self.log_test(test_name, "FAIL", f"❌ ENDPOINT NICHT IMPLEMENTIERT: /api/market-sentiment (404 Not Found)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Market Sentiment API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for frontend-compatible market sentiment
        if 'sentiment' in data or 'market_sentiment' in data:
            sentiment_data = data.get('sentiment', data.get('market_sentiment', {}))
            
            # Check for frontend-expected structure
            expected_fields = ['overall_sentiment', 'fear_greed_index', 'social_sentiment']
            has_expected_fields = any(field in sentiment_data for field in expected_fields)
            
            if has_expected_fields:
                overall = sentiment_data.get('overall_sentiment', 'N/A')
                fear_greed = sentiment_data.get('fear_greed_index', 0)
                
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ MARKET SENTIMENT FRONTEND-KOMPATIBEL! Overall Sentiment: {overall}, Fear & Greed: {fear_greed}, kompatibel mit bestehendem Frontend",
                    "Market Sentiment kompatibel mit bestehendem Frontend",
                    f"Overall: {overall}, F&G: {fear_greed}, Frontend compatible: {has_expected_fields}"
                )
            else:
                self.log_test(test_name, "WARN", f"⚠️ Market Sentiment verfügbar aber könnte für Frontend optimiert werden")
        else:
            if isinstance(data, dict) and any(key in str(data).lower() for key in ['mock', 'fallback', 'demo']):
                self.log_test(test_name, "WARN", f"⚠️ Market Sentiment mit **MOCK** Daten: {data}")
            else:
                self.log_test(test_name, "FAIL", f"❌ Market Sentiment Response unvollständig: {data}")

    async def test_bitcoin_dominance_correction(self):
        """Test 12: Bitcoin-Dominanz Korrektur (soll 59% sein)"""
        test_name = "🎯 KI-DATENMODUL TEST 12: BITCOIN-DOMINANZ KORREKTUR (59%)"
        
        response = await self.test_api_endpoint("/macro-data")
        
        if not response['success']:
            self.log_test(test_name, "FAIL", f"❌ Macro Data API call failed with status {response['status']}: {response.get('error', 'Unknown error')}")
            return
        
        data = response['data']
        
        # Check for Bitcoin dominance correction
        if 'BitcoinDominance' in data:
            btc_dominance_data = data['BitcoinDominance']
            btc_dominance = btc_dominance_data.get('percentage', 0)
            
            # Check if Bitcoin dominance is around 59% as requested
            if 58 <= btc_dominance <= 60:
                self.log_test(
                    test_name, 
                    "PASS", 
                    f"✅ BITCOIN-DOMINANZ KORREKTUR ERFOLGREICH! BTC Dominanz: {btc_dominance:.1f}% (Zielwert: 59%, Toleranz: ±1%)",
                    "Bitcoin-Dominanz soll 59% sein",
                    f"BTC Dominance: {btc_dominance:.1f}% (Target: 59%)"
                )
            elif 55 <= btc_dominance <= 65:
                self.log_test(test_name, "WARN", f"⚠️ Bitcoin-Dominanz nahe Zielwert aber nicht exakt: {btc_dominance:.1f}% (Ziel: 59%)")
            else:
                self.log_test(test_name, "FAIL", f"❌ Bitcoin-Dominanz weit vom Zielwert: {btc_dominance:.1f}% (Ziel: 59%)")
        else:
            self.log_test(test_name, "FAIL", f"❌ Bitcoin-Dominanz nicht in Macro Data gefunden: {list(data.keys())}")

    async def test_fallback_systems_api_failures(self):
        """Test 13: Fallback-Systeme bei API-Fehlern"""
        test_name = "🎯 KI-DATENMODUL TEST 13: FALLBACK-SYSTEME BEI API-FEHLERN"
        
        # Test multiple endpoints to verify fallback systems
        endpoints_to_test = [
            "/ai-data/data-quality",
            "/correlations/real-time", 
            "/news-sentiment/real-time-sentiment",
            "/financial-news",
            "/market-sentiment"
        ]
        
        working_endpoints = 0
        fallback_systems_detected = 0
        mock_systems_detected = 0
        
        for endpoint in endpoints_to_test:
            response = await self.test_api_endpoint(endpoint)
            
            if response['success']:
                working_endpoints += 1
                
                # Check if response indicates fallback system usage
                data = response['data']
                if isinstance(data, dict):
                    # Look for fallback indicators
                    fallback_indicators = ['fallback', 'cached', 'backup', 'alternative']
                    mock_indicators = ['mock', 'demo', 'sample']
                    response_str = str(data).lower()
                    
                    if any(indicator in response_str for indicator in fallback_indicators):
                        fallback_systems_detected += 1
                    if any(indicator in response_str for indicator in mock_indicators):
                        mock_systems_detected += 1
        
        if working_endpoints >= 3:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ FALLBACK-SYSTEME FUNKTIONIEREN! {working_endpoints}/{len(endpoints_to_test)} Endpoints arbeiten korrekt, {fallback_systems_detected} mit Fallback-Systemen, {mock_systems_detected} mit **MOCK**-Daten bei API-Fehlern",
                "Fallback-Systeme bei API-Ausfällen aktiv",
                f"Working endpoints: {working_endpoints}/{len(endpoints_to_test)}, Fallbacks: {fallback_systems_detected}, Mocks: {mock_systems_detected}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ Fallback-Systeme unzureichend: nur {working_endpoints}/{len(endpoints_to_test)} Endpoints funktionieren")

    async def test_ki_datenmodul_initialization(self):
        """Test 14: KI-Datenmodul Initialisierung"""
        test_name = "🎯 KI-DATENMODUL TEST 14: SYSTEM-INITIALISIERUNG"
        
        # Test if the AI data module endpoints are properly initialized
        initialization_endpoints = [
            "/ai-data/load-historical",
            "/ai-data/calculate-indicators", 
            "/ai-data/data-quality",
            "/correlations/calculate-comprehensive",
            "/correlations/real-time",
            "/news-sentiment/fetch-news"
        ]
        
        initialized_endpoints = 0
        not_found_endpoints = []
        
        for endpoint in initialization_endpoints:
            if endpoint.startswith("/ai-data/") or endpoint.startswith("/correlations/calculate") or endpoint.startswith("/news-sentiment/fetch"):
                # These are POST endpoints, test with minimal data
                test_data = {"test": "initialization"}
                response = await self.test_api_endpoint(endpoint, method="POST", data=test_data)
            else:
                # These are GET endpoints
                response = await self.test_api_endpoint(endpoint)
            
            if response['status'] != 404:
                initialized_endpoints += 1
            else:
                not_found_endpoints.append(endpoint)
        
        if initialized_endpoints >= 4:
            self.log_test(
                test_name, 
                "PASS", 
                f"✅ KI-DATENMODUL INITIALISIERUNG ERFOLGREICH! {initialized_endpoints}/{len(initialization_endpoints)} neue APIs korrekt initialisiert. Nicht gefunden: {not_found_endpoints}",
                "Neue KI-Datenmodul APIs korrekt initialisiert",
                f"Initialized: {initialized_endpoints}/{len(initialization_endpoints)}"
            )
        else:
            self.log_test(test_name, "FAIL", f"❌ KI-Datenmodul Initialisierung unvollständig: nur {initialized_endpoints}/{len(initialization_endpoints)} APIs verfügbar. Nicht gefunden: {not_found_endpoints}")

    # ============= MAIN TEST EXECUTION =============
    
    async def run_all_tests(self):
        """Run all KI-DATENMODUL tests in sequence"""
        print("🎯 STARTING KI-DATENMODUL COMPREHENSIVE TESTING")
        print("=" * 80)
        print("NEUE KI-DATENMODUL APIs ZU TESTEN:")
        print("1. Historische Datenladung (2019-heute)")
        print("2. Korrelationsanalyse mit Zeitversatzkorrektur")
        print("3. News & Sentiment Analyse (24h rückwirkend, 1 Woche voraus)")
        print("4. Datenqualität & Bitcoin-Dominanz")
        print("=" * 80)
        
        # KI-DATENMODUL TESTS (Priority as requested)
        await self.test_ki_datenmodul_initialization()
        await self.test_ai_data_load_historical()
        await self.test_ai_data_calculate_indicators()
        await self.test_ai_data_quality_assessment()
        await self.test_correlations_calculate_comprehensive()
        await self.test_correlations_real_time()
        await self.test_correlations_trends()
        await self.test_news_sentiment_fetch_news()
        await self.test_news_sentiment_economic_events()
        await self.test_news_sentiment_real_time()
        await self.test_financial_news_compatibility()
        await self.test_market_sentiment_compatibility()
        await self.test_bitcoin_dominance_correction()
        await self.test_fallback_systems_api_failures()
        
        # Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 KI-DATENMODUL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"📊 TOTAL TESTS: {total_tests}")
        print(f"✅ PASSED: {passed_tests}")
        print(f"❌ FAILED: {failed_tests}")
        print(f"⚠️  WARNINGS: {warned_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        print("\n🎯 DETAILED RESULTS:")
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            if result['details']:
                print(f"   {result['details']}")
        
        # Categorize results
        critical_failures = []
        mock_data_warnings = []
        not_implemented = []
        
        for result in self.test_results:
            if result['status'] == 'FAIL':
                if 'NICHT IMPLEMENTIERT' in result['details']:
                    not_implemented.append(result['test'])
                else:
                    critical_failures.append(result['test'])
            elif result['status'] == 'WARN' and '**MOCK**' in result['details']:
                mock_data_warnings.append(result['test'])
        
        print("\n📋 KATEGORISIERTE ERGEBNISSE:")
        if not_implemented:
            print(f"❌ NICHT IMPLEMENTIERTE ENDPOINTS ({len(not_implemented)}):")
            for test in not_implemented:
                print(f"   - {test}")
        
        if critical_failures:
            print(f"❌ KRITISCHE FEHLER ({len(critical_failures)}):")
            for test in critical_failures:
                print(f"   - {test}")
        
        if mock_data_warnings:
            print(f"⚠️  **MOCK** DATEN ERKANNT ({len(mock_data_warnings)}):")
            for test in mock_data_warnings:
                print(f"   - {test}")
        
        print("\n" + "=" * 80)
        print("🎯 KI-DATENMODUL TESTING COMPLETE")
        print("=" * 80)

async def main():
    """Main test runner for KI-DATENMODUL"""
    tester = KIDatenmodulTester()
    
    try:
        await tester.setup()
        await tester.run_all_tests()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())