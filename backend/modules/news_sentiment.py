"""
News & Sentiment Analysis Module
Aggregates financial news and market sentiment from multiple free sources
"""

import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class NewsAndSentimentEngine:
    """Engine for aggregating news and sentiment data"""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.finnhub_base = "https://finnhub.io/api/v1"
        # Free tier - no API key needed for basic features
        
    async def get_crypto_news(self, limit: int = 10) -> List[Dict]:
        """Get latest crypto news from CoinGecko (free)"""
        try:
            async with aiohttp.ClientSession() as session:
                # CoinGecko trending coins (free endpoint)
                url = f"{self.coingecko_base}/search/trending"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        news_items = []
                        for coin in data.get('coins', [])[:limit]:
                            item = coin.get('item', {})
                            news_items.append({
                                'title': f"{item.get('name')} trending - Rank #{item.get('market_cap_rank', 'N/A')}",
                                'description': f"Price: ${item.get('data', {}).get('price', 'N/A')} | Market Cap Rank: {item.get('market_cap_rank')}",
                                'symbol': item.get('symbol', '').upper(),
                                'source': 'CoinGecko Trending',
                                'url': f"https://www.coingecko.com/en/coins/{item.get('id')}",
                                'published_at': datetime.now(timezone.utc).isoformat(),
                                'sentiment': self._analyze_price_change(item.get('data', {}).get('price_change_percentage_24h', {}).get('usd', 0))
                            })
                        
                        return news_items
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
            return []
    
    async def get_market_sentiment(self) -> Dict:
        """Get aggregated market sentiment from multiple indicators"""
        try:
            sentiment_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_sentiment': 'neutral',
                'sentiment_score': 0,
                'indicators': {}
            }
            
            # Get Fear & Greed Index approximation from market data
            async with aiohttp.ClientSession() as session:
                # Get BTC dominance and market data
                url = f"{self.coingecko_base}/global"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        market_data = data.get('data', {})
                        
                        # Calculate sentiment indicators
                        btc_dominance = market_data.get('market_cap_percentage', {}).get('btc', 0)
                        total_market_cap_change = market_data.get('market_cap_change_percentage_24h_usd', 0)
                        
                        sentiment_data['indicators']['btc_dominance'] = {
                            'value': btc_dominance,
                            'sentiment': 'bullish' if btc_dominance > 50 else 'bearish',
                            'description': f"Bitcoin Dominanz: {btc_dominance:.2f}%"
                        }
                        
                        sentiment_data['indicators']['market_cap_change'] = {
                            'value': total_market_cap_change,
                            'sentiment': 'bullish' if total_market_cap_change > 2 else 'bearish' if total_market_cap_change < -2 else 'neutral',
                            'description': f"Marktkapitalisierung 24h: {total_market_cap_change:+.2f}%"
                        }
                        
                        # Calculate overall sentiment score
                        score = 0
                        if total_market_cap_change > 5:
                            score += 30
                        elif total_market_cap_change > 2:
                            score += 15
                        elif total_market_cap_change < -5:
                            score -= 30
                        elif total_market_cap_change < -2:
                            score -= 15
                            
                        if btc_dominance > 55:
                            score += 10
                        elif btc_dominance < 40:
                            score -= 10
                        
                        sentiment_data['sentiment_score'] = max(-100, min(100, score))
                        
                        if score > 20:
                            sentiment_data['overall_sentiment'] = 'bullish'
                        elif score < -20:
                            sentiment_data['overall_sentiment'] = 'bearish'
                        else:
                            sentiment_data['overall_sentiment'] = 'neutral'
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error calculating market sentiment: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_sentiment': 'neutral',
                'sentiment_score': 0,
                'indicators': {}
            }
    
    async def get_economic_calendar(self) -> List[Dict]:
        """Get upcoming economic events (simplified free version)"""
        # Since we're using free APIs, return general market events
        events = [
            {
                'title': 'Crypto Market Weekly Analysis',
                'description': 'Wöchentliche Übersicht der wichtigsten Marktbewegungen',
                'date': datetime.now(timezone.utc).isoformat(),
                'importance': 'medium',
                'category': 'analysis'
            }
        ]
        return events
    
    def _analyze_price_change(self, change_24h: float) -> str:
        """Analyze sentiment based on 24h price change"""
        if change_24h > 5:
            return 'very_bullish'
        elif change_24h > 2:
            return 'bullish'
        elif change_24h < -5:
            return 'very_bearish'
        elif change_24h < -2:
            return 'bearish'
        else:
            return 'neutral'
    
    async def get_social_sentiment(self) -> Dict:
        """Get social media sentiment indicators"""
        try:
            # Using trending data as proxy for social sentiment
            async with aiohttp.ClientSession() as session:
                url = f"{self.coingecko_base}/search/trending"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        trending_count = len(data.get('coins', []))
                        
                        return {
                            'trending_coins': trending_count,
                            'sentiment': 'high_interest' if trending_count > 5 else 'moderate_interest',
                            'description': f"{trending_count} Coins im Trend",
                            'top_trending': [
                                {
                                    'name': coin['item']['name'],
                                    'symbol': coin['item']['symbol'],
                                    'rank': coin['item']['market_cap_rank']
                                }
                                for coin in data.get('coins', [])[:5]
                            ]
                        }
        except Exception as e:
            logger.error(f"Error fetching social sentiment: {e}")
            return {
                'trending_coins': 0,
                'sentiment': 'unknown',
                'description': 'Daten nicht verfügbar'
            }
    
    async def get_complete_news_and_sentiment(self) -> Dict:
        """Get all news and sentiment data combined"""
        try:
            # Run all requests concurrently
            news, sentiment, social = await asyncio.gather(
                self.get_crypto_news(limit=10),
                self.get_market_sentiment(),
                self.get_social_sentiment(),
                return_exceptions=True
            )
            
            return {
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'news': news if not isinstance(news, Exception) else [],
                'market_sentiment': sentiment if not isinstance(sentiment, Exception) else {},
                'social_sentiment': social if not isinstance(social, Exception) else {},
                'message': 'News und Sentiment-Daten erfolgreich abgerufen'
            }
            
        except Exception as e:
            logger.error(f"Error in get_complete_news_and_sentiment: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
