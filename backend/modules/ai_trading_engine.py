"""
AI Trading Engine powered by Gemini API
Comprehensive trading analysis, strategy development, and decision support
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import os
import google.generativeai as genai
import pandas as pd
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass 
class MarketContext:
    """Complete market context for AI analysis"""
    symbol: str
    current_price: float
    price_change_24h: float
    volume_24h: float
    market_cap: float = 0
    dominance: float = 0
    
    # Technical indicators
    rsi: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    bollinger_middle: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    macd: Optional[float] = None
    stoch_k: Optional[float] = None
    
    # Smart Money data
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    liquidation_levels_above: Optional[List[Dict]] = None
    liquidation_levels_below: Optional[List[Dict]] = None
    directional_bias: Optional[Dict] = None
    
    # Orderflow data
    buy_pressure: Optional[float] = None
    sell_pressure: Optional[float] = None
    order_book_imbalance: Optional[float] = None

@dataclass
class TradingRecommendation:
    """AI Trading recommendation with detailed analysis"""
    action: str  # 'buy', 'sell', 'hold', 'close'
    confidence: float  # 0-1
    position_size: float  # recommended size
    leverage: int  # recommended leverage
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    trade_type: str = 'swing'  # 'scalp', 'day', 'swing', 'position'
    reasoning: str = ''
    market_conditions: str = ''
    risk_assessment: str = ''
    probability_analysis: Dict = None

class AITradingEngine:
    def __init__(self, db, paper_trading_engine=None, enhanced_smart_money=None):
        self.db = db
        self.paper_trading = paper_trading_engine
        self.smart_money = enhanced_smart_money
        
        # Initialize Gemini API
        self.api_key = "AIzaSyBKFAeDjQbTOczapUVLaj7L0TNi0bwD83Y"
        genai.configure(api_key=self.api_key)
        
        # Initialize Gemini model with custom settings for trading
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            generation_config={
                "temperature": 0.2,  # Lower temperature for more consistent trading decisions
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 4000,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        
        # Chat session for continuous learning
        self.chat_session = self.model.start_chat(history=[])
        
        # Trading strategies database
        self.strategies = {}
        self.user_interactions = {}
        
        # Market analysis cache
        self.market_analysis_cache = {}
        
        logger.info("AI Trading Engine initialized with Gemini Pro")

    async def analyze_market_comprehensive(self, symbol: str, timeframe: str = "1day") -> MarketContext:
        """Gather comprehensive market data for AI analysis"""
        try:
            market_context = MarketContext(symbol=symbol, current_price=0, price_change_24h=0, volume_24h=0)
            
            # Get real-time price data
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://localhost:8001/api/realtime/latest?symbols={symbol}') as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status') == 'success' and symbol in data.get('data', {}):
                                price_data = data['data'][symbol]
                                market_context.current_price = price_data['price']
                                market_context.price_change_24h = price_data.get('change_24h', 0)
                                market_context.volume_24h = price_data.get('volume_24h', 0)
            except Exception as e:
                logger.warning(f"Could not fetch real-time price data: {e}")
            
            # Get technical indicators
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://localhost:8001/api/indicators/all?symbol={symbol}') as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status') == 'success':
                                indicators = data['data']
                                market_context.rsi = indicators.get('rsi', {}).get('value')
                                
                                bollinger = indicators.get('bollinger_bands', {})
                                market_context.bollinger_upper = bollinger.get('upper')
                                market_context.bollinger_lower = bollinger.get('lower')
                                market_context.bollinger_middle = bollinger.get('middle')
                                
                                market_context.ema_50 = indicators.get('ema_50', {}).get('value')
                                market_context.ema_200 = indicators.get('ema_200', {}).get('value')
                                market_context.macd = indicators.get('macd', {}).get('macd')
                                market_context.stoch_k = indicators.get('stochastic', {}).get('k')
            except Exception as e:
                logger.warning(f"Could not fetch technical indicators: {e}")
            
            # Get Smart Money data
            if self.smart_money:
                try:
                    smart_money_data = await self.smart_money.get_enhanced_smart_money_data_with_timeframe(symbol, timeframe)
                    if smart_money_data and 'liquidation_heatmap_2d' in smart_money_data:
                        liq_data = smart_money_data['liquidation_heatmap_2d']
                        
                        # Extract liquidation levels
                        levels = liq_data.get('liquidation_levels', [])
                        market_context.liquidation_levels_above = [l for l in levels if l.get('above_current')]
                        market_context.liquidation_levels_below = [l for l in levels if not l.get('above_current')]
                        market_context.directional_bias = liq_data.get('summary', {}).get('directional_bias', {})
                    
                    if smart_money_data and 'open_interest_detailed' in smart_money_data:
                        oi_data = smart_money_data['open_interest_detailed']
                        market_context.open_interest = oi_data.get('total_open_interest', 0)
                        market_context.funding_rate = oi_data.get('market_metrics', {}).get('avg_funding_rate', 0)
                
                except Exception as e:
                    logger.warning(f"Could not fetch smart money data: {e}")
            
            return market_context
            
        except Exception as e:
            logger.error(f"Error analyzing market for {symbol}: {e}")
            return MarketContext(symbol=symbol, current_price=0, price_change_24h=0, volume_24h=0)

    async def analyze_trade_opportunity(self, symbol: str, user_id: str, context: str = "") -> TradingRecommendation:
        """Comprehensive AI-powered trade analysis"""
        try:
            # Gather comprehensive market data
            market_context = await self.analyze_market_comprehensive(symbol)
            
            # Get user's trading history and behavior
            user_context = await self._get_user_trading_context(user_id)
            
            # Get recent chat history for context
            chat_context = await self._get_recent_chat_context(user_id)
            
            # Create comprehensive analysis prompt
            analysis_prompt = self._create_analysis_prompt(market_context, user_context, chat_context, context)
            
            # Get AI analysis
            response = await self._query_gemini_async(analysis_prompt)
            
            # Parse AI response into structured recommendation
            recommendation = await self._parse_ai_recommendation(response, symbol, market_context)
            
            # Store analysis for learning
            await self._store_analysis(user_id, symbol, market_context, recommendation, response)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error analyzing trade opportunity for {symbol}: {e}")
            return TradingRecommendation(
                action="hold", 
                confidence=0.0, 
                position_size=0, 
                leverage=1,
                reasoning="Analysis failed due to technical error"
            )

    def _create_analysis_prompt(self, market_context: MarketContext, user_context: Dict, chat_context: str, additional_context: str = "") -> str:
        """Create comprehensive analysis prompt for Gemini"""
        
        prompt = f"""
# PROFESSIONAL CRYPTO TRADING ANALYSIS

You are an elite cryptocurrency trading analyst with access to comprehensive market data. Provide a detailed trading recommendation based on the following data:

## MARKET DATA for {market_context.symbol}
- **Current Price**: ${market_context.current_price:,.2f}
- **24h Change**: {market_context.price_change_24h:+.2f}%
- **24h Volume**: ${market_context.volume_24h:,.0f}

## TECHNICAL INDICATORS
- **RSI**: {market_context.rsi or 'N/A'}
- **Bollinger Bands**: Upper: {market_context.bollinger_upper or 'N/A'}, Middle: {market_context.bollinger_middle or 'N/A'}, Lower: {market_context.bollinger_lower or 'N/A'}
- **EMA 50**: {market_context.ema_50 or 'N/A'}
- **EMA 200**: {market_context.ema_200 or 'N/A'}
- **MACD**: {market_context.macd or 'N/A'}
- **Stochastic K**: {market_context.stoch_k or 'N/A'}

## SMART MONEY & ORDER FLOW
- **Open Interest**: ${market_context.open_interest or 0:,.0f}
- **Funding Rate**: {market_context.funding_rate or 0:.4f}%
- **Liquidation Levels Above**: {len(market_context.liquidation_levels_above or [])} levels
- **Liquidation Levels Below**: {len(market_context.liquidation_levels_below or [])} levels
- **Directional Bias**: {market_context.directional_bias.get('bias', 'neutral') if market_context.directional_bias else 'neutral'} ({market_context.directional_bias.get('strength', 0) if market_context.directional_bias else 0:.2f} strength)

## USER TRADING CONTEXT
{json.dumps(user_context, indent=2)}

## RECENT CHAT CONTEXT
{chat_context}

## ADDITIONAL CONTEXT
{additional_context}

# ANALYSIS REQUIREMENTS

Please provide a comprehensive analysis in the following JSON format:

```json
{{
  "action": "buy|sell|hold|close",
  "confidence": 0.0-1.0,
  "position_size_percent": 1-100,
  "recommended_leverage": 1-100,
  "entry_price": number or null,
  "stop_loss": number or null,
  "take_profit": number or null,
  "risk_reward_ratio": number,
  "trade_type": "scalp|day|swing|position",
  "reasoning": "detailed explanation of the analysis",
  "market_conditions": "current market assessment",
  "risk_assessment": "risk analysis and warnings",
  "probability_analysis": {{
    "win_probability": 0.0-1.0,
    "expected_return": number,
    "max_drawdown_risk": number,
    "time_horizon": "expected trade duration"
  }}
}}
```

## ANALYSIS FOCUS AREAS:
1. **Technical Analysis**: RSI, Bollinger Bands, EMA convergence/divergence, MACD signals
2. **Smart Money Analysis**: Liquidation clusters, open interest trends, funding rate implications
3. **Market Structure**: Support/resistance levels, trend direction, momentum
4. **Risk Management**: Position sizing, leverage recommendations, stop loss placement
5. **Trade Timing**: Entry timing, trade type classification (scalp/day/swing)
6. **Probability Assessment**: Win rate estimation, risk/reward analysis

Provide professional, actionable insights based on all available data.
"""
        
        return prompt

    async def _query_gemini_async(self, prompt: str) -> str:
        """Query Gemini API asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.chat_session.send_message, prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error querying Gemini API: {e}")
            return "Error: Could not get AI analysis"

    async def _parse_ai_recommendation(self, ai_response: str, symbol: str, market_context: MarketContext) -> TradingRecommendation:
        """Parse AI response into structured recommendation"""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed_data = json.loads(json_str)
                
                return TradingRecommendation(
                    action=parsed_data.get('action', 'hold'),
                    confidence=float(parsed_data.get('confidence', 0.5)),
                    position_size=float(parsed_data.get('position_size_percent', 5)),
                    leverage=int(parsed_data.get('recommended_leverage', 1)),
                    entry_price=parsed_data.get('entry_price'),
                    stop_loss=parsed_data.get('stop_loss'),
                    take_profit=parsed_data.get('take_profit'),
                    risk_reward_ratio=parsed_data.get('risk_reward_ratio'),
                    trade_type=parsed_data.get('trade_type', 'swing'),
                    reasoning=parsed_data.get('reasoning', ''),
                    market_conditions=parsed_data.get('market_conditions', ''),
                    risk_assessment=parsed_data.get('risk_assessment', ''),
                    probability_analysis=parsed_data.get('probability_analysis', {})
                )
            else:
                # Fallback parsing if JSON not found
                return TradingRecommendation(
                    action="hold",
                    confidence=0.5,
                    position_size=5,
                    leverage=1,
                    reasoning=ai_response[:500] + "..." if len(ai_response) > 500 else ai_response
                )
                
        except Exception as e:
            logger.error(f"Error parsing AI recommendation: {e}")
            return TradingRecommendation(
                action="hold",
                confidence=0.0,
                position_size=0,
                leverage=1,
                reasoning="Could not parse AI analysis"
            )

    async def _get_user_trading_context(self, user_id: str) -> Dict:
        """Get user's trading history and behavior patterns"""
        try:
            # Get user account
            account = None
            if self.paper_trading:
                account = await self.paper_trading.get_user_account(user_id)
            
            # Get recent positions
            positions = []
            if self.paper_trading:
                positions = await self.paper_trading.get_positions(user_id)
            
            # Get trade history
            history = []
            if self.paper_trading:
                history = await self.paper_trading.get_trade_history(user_id, 20)
            
            # Analyze trading patterns
            trading_style = self._analyze_trading_style(history)
            
            return {
                'account_balance': account.get('balance', 0) if account else 0,
                'current_equity': account.get('equity', 0) if account else 0,
                'open_positions': len(positions),
                'total_trades': len(history),
                'trading_style': trading_style,
                'recent_performance': self._calculate_recent_performance(history),
                'risk_profile': self._assess_risk_profile(history, positions)
            }
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {}

    async def _get_recent_chat_context(self, user_id: str, limit: int = 10) -> str:
        """Get recent chat messages for context"""
        try:
            messages = await self.db.messages.find(
                {'user_id': user_id}
            ).sort('created_at', -1).limit(limit).to_list(None)
            
            context = "Recent chat context:\n"
            for msg in reversed(messages):
                context += f"User: {msg.get('message', '')}\n"
                context += f"AI: {msg.get('response', '')}\n"
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting chat context: {e}")
            return "No recent chat context available"

    def _analyze_trading_style(self, history: List[Dict]) -> str:
        """Analyze user's trading style from history"""
        if not history:
            return "new_trader"
        
        # Analyze trade durations, sizes, frequency
        # This is a simplified analysis
        avg_leverage = sum(trade.get('leverage', 1) for trade in history) / len(history)
        
        if avg_leverage > 50:
            return "high_risk_trader"
        elif avg_leverage > 10:
            return "moderate_risk_trader"
        else:
            return "conservative_trader"

    def _calculate_recent_performance(self, history: List[Dict]) -> Dict:
        """Calculate recent trading performance metrics"""
        if not history:
            return {'win_rate': 0, 'avg_return': 0, 'total_pnl': 0}
        
        # Simple performance calculation
        total_pnl = sum(trade.get('realized_pnl', 0) for trade in history[-10:])
        wins = len([t for t in history[-10:] if t.get('realized_pnl', 0) > 0])
        
        return {
            'win_rate': wins / min(len(history), 10),
            'avg_return': total_pnl / min(len(history), 10),
            'total_pnl': total_pnl
        }

    def _assess_risk_profile(self, history: List[Dict], positions: List[Dict]) -> str:
        """Assess user's risk profile"""
        if not history and not positions:
            return "unknown"
        
        # Analyze current positions and historical leverage usage
        current_risk = sum(pos.get('leverage', 1) for pos in positions) / max(len(positions), 1)
        
        if current_risk > 25:
            return "high_risk"
        elif current_risk > 10:
            return "moderate_risk"
        else:
            return "low_risk"

    async def _store_analysis(self, user_id: str, symbol: str, market_context: MarketContext, 
                            recommendation: TradingRecommendation, ai_response: str):
        """Store AI analysis for learning and improvement"""
        try:
            analysis_record = {
                'user_id': user_id,
                'symbol': symbol,
                'timestamp': datetime.now(timezone.utc),
                'market_context': {
                    'current_price': market_context.current_price,
                    'price_change_24h': market_context.price_change_24h,
                    'rsi': market_context.rsi,
                    'directional_bias': market_context.directional_bias
                },
                'recommendation': {
                    'action': recommendation.action,
                    'confidence': recommendation.confidence,
                    'position_size': recommendation.position_size,
                    'leverage': recommendation.leverage,
                    'trade_type': recommendation.trade_type
                },
                'ai_response': ai_response,
                'outcome': None  # To be updated when trade is closed
            }
            
            await self.db.ai_trading_analysis.insert_one(analysis_record)
            
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")

    async def execute_chat_command(self, user_id: str, command: str) -> Dict:
        """Execute trading commands from chat"""
        try:
            # Parse trading command using AI
            command_prompt = f"""
Parse the following trading command and extract trading parameters:

Command: "{command}"

Return a JSON response with the following structure:
```json
{{
  "command_type": "open_position|close_position|modify_position|market_analysis|strategy_request",
  "symbol": "symbol if specified",
  "action": "buy|sell|close",
  "quantity": number or null,
  "leverage": number or null,
  "order_type": "market|limit",
  "price": number or null,
  "stop_loss": number or null,
  "take_profit": number or null,
  "strategy": "strategy description if any",
  "parsed_intent": "human readable interpretation"
}}
```

Examples:
- "Long BTC 0.1 at 65000" → open_position, BTC/USDT, buy, 0.1, market
- "Close 50% ETH position" → close_position, ETH/USDT, close, 50%
- "What's your analysis on SOL?" → market_analysis, SOL/USDT
- "Go long on next bollinger cross" → strategy_request, strategy analysis
"""
            
            ai_response = await self._query_gemini_async(command_prompt)
            
            # Parse the AI response
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
            if json_match:
                parsed_command = json.loads(json_match.group(1))
                
                # Execute the command based on type
                if parsed_command['command_type'] == 'open_position':
                    return await self._execute_open_position(user_id, parsed_command)
                elif parsed_command['command_type'] == 'close_position':
                    return await self._execute_close_position(user_id, parsed_command)
                elif parsed_command['command_type'] == 'market_analysis':
                    return await self._execute_market_analysis(user_id, parsed_command)
                elif parsed_command['command_type'] == 'strategy_request':
                    return await self._execute_strategy_request(user_id, parsed_command)
                else:
                    return {
                        'success': False,
                        'message': f"Command type '{parsed_command['command_type']}' not implemented yet"
                    }
            else:
                return {
                    'success': False,
                    'message': 'Could not parse trading command'
                }
                
        except Exception as e:
            logger.error(f"Error executing chat command: {e}")
            return {
                'success': False,
                'message': f'Error executing command: {str(e)}'
            }

    async def _execute_open_position(self, user_id: str, command: Dict) -> Dict:
        """Execute open position command"""
        try:
            if not self.paper_trading:
                return {'success': False, 'message': 'Paper trading not available'}
            
            symbol = command.get('symbol', '').upper()
            if not symbol.endswith('/USDT'):
                symbol += '/USDT'
            
            # Get AI recommendation for this trade
            recommendation = await self.analyze_trade_opportunity(user_id, symbol, f"User wants to {command.get('action')} {symbol}")
            
            # Execute the trade using paper trading engine
            result = await self.paper_trading.place_order(
                user_id=user_id,
                symbol=symbol,
                side=command.get('action', 'buy'),
                order_type=command.get('order_type', 'market'),
                quantity=float(command.get('quantity', recommendation.position_size)),
                price=command.get('price'),
                leverage=int(command.get('leverage', recommendation.leverage)),
                stop_loss=command.get('stop_loss') or recommendation.stop_loss,
                take_profit=command.get('take_profit') or recommendation.take_profit
            )
            
            if result.get('success'):
                return {
                    'success': True,
                    'message': f"Position opened successfully",
                    'order': result.get('order'),
                    'ai_analysis': {
                        'confidence': recommendation.confidence,
                        'reasoning': recommendation.reasoning,
                        'risk_assessment': recommendation.risk_assessment
                    }
                }
            else:
                return {
                    'success': False,
                    'message': result.get('error', 'Failed to open position')
                }
                
        except Exception as e:
            logger.error(f"Error executing open position: {e}")
            return {'success': False, 'message': str(e)}

    async def _execute_close_position(self, user_id: str, command: Dict) -> Dict:
        """Execute close position command"""
        # Implementation for closing positions
        return {'success': False, 'message': 'Close position not implemented yet'}

    async def _execute_market_analysis(self, user_id: str, command: Dict) -> Dict:
        """Execute market analysis command"""
        try:
            symbol = command.get('symbol', '').upper()
            if not symbol.endswith('/USDT'):
                symbol += '/USDT'
            
            recommendation = await self.analyze_trade_opportunity(user_id, symbol, "Provide comprehensive market analysis")
            
            return {
                'success': True,
                'analysis': {
                    'symbol': symbol,
                    'recommendation': recommendation.action,
                    'confidence': recommendation.confidence,
                    'reasoning': recommendation.reasoning,
                    'market_conditions': recommendation.market_conditions,
                    'risk_assessment': recommendation.risk_assessment,
                    'trade_type': recommendation.trade_type,
                    'probability_analysis': recommendation.probability_analysis
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing market analysis: {e}")
            return {'success': False, 'message': str(e)}

    async def _execute_strategy_request(self, user_id: str, command: Dict) -> Dict:
        """Execute strategy development request"""
        try:
            strategy_prompt = f"""
The user is requesting strategy development: "{command.get('strategy', '')}"

Please create a comprehensive trading strategy including:
1. Entry conditions
2. Exit conditions 
3. Risk management rules
4. Position sizing
5. Timeframe recommendations
6. Market conditions where this strategy works best

Provide a detailed strategy document that can be implemented.
"""
            
            strategy_response = await self._query_gemini_async(strategy_prompt)
            
            return {
                'success': True,
                'strategy': {
                    'description': command.get('strategy', ''),
                    'detailed_plan': strategy_response
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing strategy request: {e}")
            return {'success': False, 'message': str(e)}

    async def learn_from_interaction(self, user_id: str, interaction_data: Dict):
        """Learn from user interactions and feedback"""
        try:
            # Store interaction for learning
            learning_record = {
                'user_id': user_id,
                'timestamp': datetime.now(timezone.utc),
                'interaction_type': interaction_data.get('type'),
                'data': interaction_data,
                'feedback': interaction_data.get('feedback'),
                'outcome': interaction_data.get('outcome')
            }
            
            await self.db.ai_learning.insert_one(learning_record)
            
            # Update user behavior model
            if user_id not in self.user_interactions:
                self.user_interactions[user_id] = []
            
            self.user_interactions[user_id].append(learning_record)
            
            # Keep only recent interactions
            self.user_interactions[user_id] = self.user_interactions[user_id][-100:]
            
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")

    async def close_session(self):
        """Clean up resources"""
        try:
            # Save any pending learning data
            pass
        except Exception as e:
            logger.error(f"Error closing AI trading engine session: {e}")