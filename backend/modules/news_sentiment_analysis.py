"""
News & Sentiment Analyse Modul mit Echtzeit-Datenintegration
Lädt Wirtschaftsdaten 1 Woche voraus und News 24h rückwirkend
"""

import asyncio
import aiohttp
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
import re
from textblob import TextBlob
import feedparser

logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """News article data structure"""
    id: str
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: float  # -1 (negative) to 1 (positive)
    impact_score: float     # 0 to 1 (market impact potential)
    category: str
    keywords: List[str]
    relevance_score: float  # 0 to 1 (crypto/finance relevance)

@dataclass
class EconomicEvent:
    """Economic calendar event"""
    id: str
    name: str
    country: str
    currency: str
    importance: str  # high, medium, low
    actual: Optional[str]
    forecast: Optional[str] 
    previous: Optional[str]
    event_time: datetime
    impact_currencies: List[str]
    market_impact: Optional[float]  # Calculated impact on BTC

@dataclass
class SentimentMetrics:
    """Market sentiment metrics"""
    timestamp: datetime
    overall_sentiment: float  # -1 to 1
    news_sentiment: float
    social_sentiment: float
    fear_greed_index: int  # 0 to 100
    volatility_index: float
    confidence_level: float

class NewsSentimentAnalysis:
    """Comprehensive news and sentiment analysis system"""
    
    def __init__(self, db):
        self.db = db
        
        # News sources and APIs
        self.news_sources = [
            {
                'name': 'CoinTelegraph',
                'rss': 'https://cointelegraph.com/rss',
                'category': 'crypto'
            },
            {
                'name': 'CoinDesk',
                'rss': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
                'category': 'crypto'
            },
            {
                'name': 'Reuters Business',
                'rss': 'https://feeds.reuters.com/reuters/businessNews',
                'category': 'business'
            },
            {
                'name': 'MarketWatch',
                'rss': 'https://feeds.marketwatch.com/marketwatch/topstories/',
                'category': 'markets'
            }
        ]
        
        # Economic calendar APIs
        self.economic_apis = {
            'investing_com': 'https://www.investing.com/economic-calendar/',
            'forexfactory': 'https://www.forexfactory.com/calendar.php',
            'econoday': 'https://www.econoday.com/'
        }
        
        # Sentiment keywords for crypto/finance
        self.positive_keywords = [
            'bullish', 'surge', 'rally', 'breakthrough', 'adoption', 'institutional', 
            'investment', 'growth', 'profit', 'gains', 'milestone', 'partnership',
            'upgrade', 'innovation', 'expansion', 'record', 'high', 'success'
        ]
        
        self.negative_keywords = [
            'bearish', 'crash', 'decline', 'dump', 'selloff', 'regulation', 
            'ban', 'hack', 'loss', 'bankruptcy', 'fraud', 'scam', 'bubble',
            'correction', 'risk', 'volatility', 'uncertainty', 'crisis'
        ]
        
        self.crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency', 'crypto',
            'blockchain', 'defi', 'nft', 'altcoin', 'binance', 'coinbase',
            'wallet', 'mining', 'halving', 'satoshi', 'web3', 'metaverse'
        ]

    async def fetch_news_24h_retrospective(self) -> List[NewsArticle]:
        """Fetch news from the last 24 hours"""
        logger.info("📰 Fetching news from last 24 hours...")
        
        all_articles = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        for source in self.news_sources:
            try:
                articles = await self._fetch_rss_news(source, cutoff_time)
                all_articles.extend(articles)
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching from {source['name']}: {e}")
        
        # Remove duplicates and sort by relevance
        unique_articles = self._deduplicate_articles(all_articles)
        relevant_articles = [a for a in unique_articles if a.relevance_score > 0.3]
        
        # Store in database
        await self._store_news_articles(relevant_articles)
        
        logger.info(f"✅ Fetched {len(relevant_articles)} relevant articles")
        return relevant_articles

    async def _fetch_rss_news(self, source: Dict, cutoff_time: datetime) -> List[NewsArticle]:
        """Fetch news from RSS feed"""
        articles = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source['rss'], timeout=10) as response:
                    if response.status == 200:
                        rss_content = await response.text()
                        feed = feedparser.parse(rss_content)
                        
                        for entry in feed.entries:
                            try:
                                # Parse publication date
                                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                                
                                if pub_date >= cutoff_time:
                                    # Extract content
                                    title = entry.title
                                    content = entry.get('summary', '')
                                    url = entry.link
                                    
                                    # Analyze sentiment and relevance
                                    sentiment = self._analyze_text_sentiment(f"{title} {content}")
                                    impact = self._calculate_impact_score(title, content)
                                    relevance = self._calculate_relevance_score(title, content)
                                    keywords = self._extract_keywords(f"{title} {content}")
                                    
                                    article = NewsArticle(
                                        id=f"{source['name']}_{hash(url)}",
                                        title=title,
                                        content=content,
                                        source=source['name'],
                                        url=url,
                                        published_at=pub_date,
                                        sentiment_score=sentiment,
                                        impact_score=impact,
                                        category=source['category'],
                                        keywords=keywords,
                                        relevance_score=relevance
                                    )
                                    
                                    articles.append(article)
                            
                            except Exception as e:
                                logger.debug(f"Error parsing RSS entry: {e}")
                                continue
        
        except Exception as e:
            logger.error(f"RSS fetch error for {source['name']}: {e}")
        
        return articles

    def _analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using TextBlob and keywords"""
        try:
            # Basic TextBlob sentiment
            blob = TextBlob(text.lower())
            base_sentiment = blob.sentiment.polarity
            
            # Keyword-based sentiment adjustment
            positive_count = sum(1 for word in self.positive_keywords if word in text.lower())
            negative_count = sum(1 for word in self.negative_keywords if word in text.lower())
            
            # Calculate keyword sentiment
            total_keywords = positive_count + negative_count
            if total_keywords > 0:
                keyword_sentiment = (positive_count - negative_count) / total_keywords
            else:
                keyword_sentiment = 0
            
            # Combine sentiments (TextBlob 70%, keywords 30%)
            final_sentiment = (base_sentiment * 0.7) + (keyword_sentiment * 0.3)
            
            # Clamp to [-1, 1]
            return max(-1.0, min(1.0, final_sentiment))
            
        except Exception as e:
            logger.debug(f"Sentiment analysis error: {e}")
            return 0.0

    def _calculate_impact_score(self, title: str, content: str) -> float:
        """Calculate potential market impact score"""
        text = f"{title} {content}".lower()
        
        # High impact indicators
        high_impact_terms = [
            'federal reserve', 'fed', 'interest rate', 'inflation', 'cpi',
            'regulation', 'sec', 'treasury', 'central bank', 'gdp',
            'institutional', 'etf', 'adoption', 'bitcoin', 'ethereum'
        ]
        
        # Medium impact indicators
        medium_impact_terms = [
            'cryptocurrency', 'crypto', 'blockchain', 'investment', 
            'market', 'price', 'trading', 'volume', 'volatility'
        ]
        
        high_count = sum(1 for term in high_impact_terms if term in text)
        medium_count = sum(1 for term in medium_impact_terms if term in text)
        
        # Calculate impact score
        impact = (high_count * 0.8 + medium_count * 0.4) / 5  # Normalize
        return min(1.0, impact)

    def _calculate_relevance_score(self, title: str, content: str) -> float:
        """Calculate crypto/finance relevance score"""
        text = f"{title} {content}".lower()
        
        crypto_count = sum(1 for word in self.crypto_keywords if word in text)
        
        # Finance keywords
        finance_keywords = [
            'market', 'finance', 'investment', 'trading', 'economy',
            'stock', 'bond', 'currency', 'dollar', 'inflation'
        ]
        finance_count = sum(1 for word in finance_keywords if word in text)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        # Calculate relevance (crypto weighted higher)
        relevance = (crypto_count * 2 + finance_count) / (total_words / 10)
        return min(1.0, relevance)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        text_lower = text.lower()
        found_keywords = []
        
        all_keywords = self.crypto_keywords + self.positive_keywords + self.negative_keywords
        
        for keyword in all_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]  # Limit to top 10

    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Create a simplified title for comparison
            simple_title = re.sub(r'[^\w\s]', '', article.title.lower())
            title_words = set(simple_title.split())
            
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                
                # Check for significant overlap
                if title_words and seen_words:
                    overlap = len(title_words.intersection(seen_words))
                    min_words = min(len(title_words), len(seen_words))
                    
                    if overlap / min_words > 0.7:  # 70% similarity threshold
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.add(simple_title)
        
        return unique_articles

    async def fetch_economic_events_1week_forward(self) -> List[EconomicEvent]:
        """Fetch economic events for the next week"""
        logger.info("📅 Fetching economic events for next week...")
        
        # For now, generate realistic mock economic events
        # In production, this would integrate with real economic calendar APIs
        
        events = await self._generate_mock_economic_events()
        
        # Store in database
        await self._store_economic_events(events)
        
        logger.info(f"✅ Generated {len(events)} economic events for next week")
        return events

    async def _generate_mock_economic_events(self) -> List[EconomicEvent]:
        """Generate realistic mock economic events for next week"""
        events = []
        base_date = datetime.now(timezone.utc)
        
        # Common economic events that affect crypto markets
        event_templates = [
            {
                'name': 'Consumer Price Index (CPI)',
                'country': 'US',
                'currency': 'USD',
                'importance': 'high',
                'day_offset': 2,
                'time_offset': 14.5  # 2:30 PM UTC
            },
            {
                'name': 'Federal Reserve Interest Rate Decision',
                'country': 'US', 
                'currency': 'USD',
                'importance': 'high',
                'day_offset': 4,
                'time_offset': 20.0  # 8:00 PM UTC
            },
            {
                'name': 'Non-Farm Payrolls',
                'country': 'US',
                'currency': 'USD', 
                'importance': 'high',
                'day_offset': 6,
                'time_offset': 14.5
            },
            {
                'name': 'Gross Domestic Product (GDP)',
                'country': 'US',
                'currency': 'USD',
                'importance': 'medium',
                'day_offset': 3,
                'time_offset': 14.5
            },
            {
                'name': 'European Central Bank Rate Decision',
                'country': 'EU',
                'currency': 'EUR',
                'importance': 'high',
                'day_offset': 5,
                'time_offset': 13.45  # 1:45 PM UTC
            },
            {
                'name': 'Initial Jobless Claims',
                'country': 'US',
                'currency': 'USD',
                'importance': 'medium',
                'day_offset': 1,
                'time_offset': 14.5
            }
        ]
        
        for i, template in enumerate(event_templates):
            event_time = base_date + timedelta(
                days=template['day_offset'],
                hours=template['time_offset']
            )
            
            # Generate realistic forecast/previous values
            if 'CPI' in template['name']:
                forecast = '0.2%'
                previous = '0.3%'
                impact_currencies = ['USD', 'BTC', 'ETH']
            elif 'Rate Decision' in template['name']:
                forecast = '5.25%'
                previous = '5.00%'
                impact_currencies = ['USD', 'BTC', 'ETH', 'EUR']
            elif 'Payrolls' in template['name']:
                forecast = '220K'
                previous = '215K'
                impact_currencies = ['USD', 'BTC']
            elif 'GDP' in template['name']:
                forecast = '2.1%'
                previous = '2.4%'
                impact_currencies = ['USD', 'BTC']
            else:
                forecast = 'TBD'
                previous = 'N/A'
                impact_currencies = ['USD']
            
            event = EconomicEvent(
                id=f"mock_event_{i}_{int(event_time.timestamp())}",
                name=template['name'],
                country=template['country'],
                currency=template['currency'],
                importance=template['importance'],
                actual=None,  # Will be filled when event occurs
                forecast=forecast,
                previous=previous,
                event_time=event_time,
                impact_currencies=impact_currencies,
                market_impact=None  # Will be calculated after event
            )
            
            events.append(event)
        
        return events

    async def calculate_real_time_sentiment(self) -> SentimentMetrics:
        """Calculate comprehensive real-time market sentiment"""
        logger.info("📊 Calculating real-time market sentiment...")
        
        try:
            # Get recent news sentiment
            news_sentiment = await self._get_recent_news_sentiment()
            
            # Calculate social sentiment (mock for now)
            social_sentiment = await self._calculate_social_sentiment()
            
            # Calculate Fear & Greed Index
            fear_greed = await self._calculate_fear_greed_index()
            
            # Calculate volatility index
            volatility = await self._calculate_volatility_index()
            
            # Combine all metrics
            overall_sentiment = (news_sentiment * 0.4 + social_sentiment * 0.3 + 
                               (fear_greed - 50) / 50 * 0.3)  # Normalize F&G to [-1,1]
            
            sentiment_metrics = SentimentMetrics(
                timestamp=datetime.now(timezone.utc),
                overall_sentiment=overall_sentiment,
                news_sentiment=news_sentiment,
                social_sentiment=social_sentiment,
                fear_greed_index=fear_greed,
                volatility_index=volatility,
                confidence_level=0.85  # Based on data quality
            )
            
            # Store in database
            await self._store_sentiment_metrics(sentiment_metrics)
            
            return sentiment_metrics
            
        except Exception as e:
            logger.error(f"Error calculating real-time sentiment: {e}")
            
            # Return neutral sentiment on error
            return SentimentMetrics(
                timestamp=datetime.now(timezone.utc),
                overall_sentiment=0.0,
                news_sentiment=0.0,
                social_sentiment=0.0,
                fear_greed_index=50,
                volatility_index=0.5,
                confidence_level=0.3
            )

    async def _get_recent_news_sentiment(self, hours_back: int = 6) -> float:
        """Get average sentiment from recent news"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            
            cursor = self.db.news_articles.find(
                {'published_at': {'$gte': cutoff_time}},
                {'sentiment_score': 1, 'relevance_score': 1, 'impact_score': 1}
            )
            
            weighted_sentiments = []
            async for doc in cursor:
                # Weight by relevance and impact
                weight = doc.get('relevance_score', 0.5) * doc.get('impact_score', 0.5)
                sentiment = doc.get('sentiment_score', 0.0)
                weighted_sentiments.append(sentiment * weight)
            
            if weighted_sentiments:
                return np.mean(weighted_sentiments)
            
        except Exception as e:
            logger.error(f"Error getting news sentiment: {e}")
        
        return 0.0  # Neutral if no data

    async def _calculate_social_sentiment(self) -> float:
        """Calculate social media sentiment (mock implementation)"""
        # In production, this would integrate with Twitter API, Reddit API, etc.
        # For now, generate realistic social sentiment
        
        base_sentiment = 0.15  # Slightly positive crypto sentiment
        daily_variation = np.random.normal(0, 0.2)  # Daily volatility
        
        return max(-1.0, min(1.0, base_sentiment + daily_variation))

    async def _calculate_fear_greed_index(self) -> int:
        """Calculate Fear & Greed Index (0-100)"""
        # Mock Fear & Greed calculation based on various factors
        # In production, would use real market data
        
        base_index = 58  # Slightly greedy
        market_volatility = np.random.normal(0, 10)  # Market noise
        
        index = base_index + market_volatility
        return max(0, min(100, int(index)))

    async def _calculate_volatility_index(self) -> float:
        """Calculate market volatility index"""
        try:
            # Get recent BTC price data
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            cursor = self.db.market_data_historical.find(
                {
                    'symbol': 'BTC/USDT',
                    'timeframe': '1h',
                    'timestamp': {'$gte': cutoff_time}
                },
                {'close': 1},
                sort=[('timestamp', 1)]
            )
            
            prices = []
            async for doc in cursor:
                prices.append(doc['close'])
            
            if len(prices) >= 12:  # At least 12 hours of data
                # Calculate hourly returns
                returns = np.diff(np.log(prices))
                # Annualized volatility
                volatility = np.std(returns) * np.sqrt(24 * 365)
                return min(2.0, volatility)  # Cap at 200%
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
        
        return 0.5  # Default moderate volatility

    async def _store_news_articles(self, articles: List[NewsArticle]):
        """Store news articles in database"""
        if not articles:
            return
        
        try:
            documents = []
            for article in articles:
                doc = asdict(article)
                doc['_id'] = article.id
                documents.append(doc)
            
            # Use upsert to avoid duplicates
            for doc in documents:
                await self.db.news_articles.update_one(
                    {'_id': doc['_id']},
                    {'$set': doc},
                    upsert=True
                )
            
        except Exception as e:
            logger.error(f"Error storing news articles: {e}")

    async def _store_economic_events(self, events: List[EconomicEvent]):
        """Store economic events in database"""
        if not events:
            return
        
        try:
            documents = []
            for event in events:
                doc = asdict(event)
                doc['_id'] = event.id
                documents.append(doc)
            
            # Use upsert to avoid duplicates
            for doc in documents:
                await self.db.economic_events.update_one(
                    {'_id': doc['_id']},
                    {'$set': doc},
                    upsert=True
                )
            
        except Exception as e:
            logger.error(f"Error storing economic events: {e}")

    async def _store_sentiment_metrics(self, metrics: SentimentMetrics):
        """Store sentiment metrics in database"""
        try:
            doc = asdict(metrics)
            doc['_id'] = f"sentiment_{int(metrics.timestamp.timestamp())}"
            
            await self.db.sentiment_metrics.update_one(
                {'_id': doc['_id']},
                {'$set': doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing sentiment metrics: {e}")

    async def get_sentiment_summary(self) -> Dict[str, Any]:
        """Get comprehensive sentiment summary for dashboard"""
        try:
            # Get latest sentiment metrics
            latest_sentiment = await self.db.sentiment_metrics.find_one(
                {},
                sort=[('timestamp', -1)]
            )
            
            # Get recent news count and sentiment
            recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            news_cursor = self.db.news_articles.find(
                {'published_at': {'$gte': recent_cutoff}},
                {'sentiment_score': 1, 'category': 1}
            )
            
            news_stats = {
                'total_articles': 0,
                'positive_articles': 0,
                'negative_articles': 0,
                'crypto_articles': 0,
                'avg_sentiment': 0.0
            }
            
            sentiments = []
            async for article in news_cursor:
                news_stats['total_articles'] += 1
                sentiment = article.get('sentiment_score', 0.0)
                sentiments.append(sentiment)
                
                if sentiment > 0.1:
                    news_stats['positive_articles'] += 1
                elif sentiment < -0.1:
                    news_stats['negative_articles'] += 1
                
                if article.get('category') == 'crypto':
                    news_stats['crypto_articles'] += 1
            
            if sentiments:
                news_stats['avg_sentiment'] = np.mean(sentiments)
            
            return {
                'latest_sentiment': latest_sentiment,
                'news_stats': news_stats,
                'summary_timestamp': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return {}

# Global instance
news_sentiment_analysis = None

async def get_news_sentiment_analysis(db) -> NewsSentimentAnalysis:
    """Get or create News Sentiment Analysis instance"""
    global news_sentiment_analysis
    if news_sentiment_analysis is None:
        news_sentiment_analysis = NewsSentimentAnalysis(db)
    return news_sentiment_analysis