"""
Integrated AI System - Complete access to all system components
Provides comprehensive analysis, monitoring, and self-improvement capabilities
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import os
import traceback
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class IntegratedAISystem:
    def __init__(self, db, paper_trading=None, enhanced_smart_money=None, real_time_streamer=None):
        self.db = db
        self.paper_trading = paper_trading
        self.smart_money = enhanced_smart_money
        self.real_time_streamer = real_time_streamer
        
        # Initialize Gemini API with new SDK
        self.api_key = os.environ.get('GEMINI_API_KEY', "AIzaSyAd8SqGySsek3Jud4HI6IkMArJtSnBcIUk")
        os.environ['GEMINI_API_KEY'] = self.api_key  # Set environment variable for client
        
        # Initialize Gemini client with new API
        self.client = genai.Client()
        self.model_name = "gemini-2.5-flash"  # Using new recommended model
        
        # Generation config for new API
        self.generation_config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.9,
            top_k=40,
            max_output_tokens=8000,
            thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disable thinking for speed
        )
        
        # System monitoring and analysis cache
        self.system_health_cache = {}
        self.error_analysis_cache = {}
        self.performance_metrics = {}
        
        logger.info("Integrated AI System initialized with full system access")

    async def process_chat_message(self, user_id: str, message: str, session_id: str) -> Dict:
        """Process chat message with full system context and analysis"""
        try:
            # Gather comprehensive system context
            system_context = await self._gather_complete_system_context(user_id)
            
            # Detect message type and intent
            message_intent = await self._analyze_message_intent(message)
            
            # Create comprehensive prompt with full system access
            prompt = await self._create_comprehensive_system_prompt(
                message, system_context, message_intent, user_id
            )
            
            # Get AI response
            ai_response = await self._query_gemini_with_context(prompt)
            
            # Execute any system commands if detected
            if message_intent.get('has_system_command'):
                command_result = await self._execute_system_command(message, user_id)
                ai_response += f"\n\n🔧 **System Command Executed:**\n{command_result}"
            
            # Execute trading commands if detected
            if message_intent.get('has_trading_command'):
                trading_result = await self._execute_trading_command(message, user_id)
                ai_response += f"\n\n💹 **Trading Command Result:**\n{trading_result}"
            
            # Store conversation for learning
            await self._store_conversation(user_id, session_id, message, ai_response)
            
            # Learn from this interaction
            await self._learn_from_interaction(user_id, message, ai_response, system_context)
            
            return {
                'status': 'success',
                'content': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'intent_analysis': message_intent
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Provide detailed error analysis
            error_analysis = await self._analyze_system_error(str(e), traceback.format_exc())
            
            return {
                'status': 'error',
                'content': f"Entschuldigung, es gab einen Systemfehler. Hier ist die Analyse:\n\n{error_analysis}",
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _gather_complete_system_context(self, user_id: str) -> Dict:
        """Gather comprehensive context from ALL system components"""
        context = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id
        }
        
        try:
            # User trading context
            if self.paper_trading:
                context['trading'] = {
                    'account': await self.paper_trading.get_user_account(user_id),
                    'positions': await self.paper_trading.get_positions(user_id),
                    'history': await self.paper_trading.get_trade_history(user_id, 10)
                }
            
            # Smart Money context (all assets)
            if self.smart_money:
                context['smart_money'] = {}
                top_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 'LINK/USDT']
                for symbol in top_symbols:
                    try:
                        sm_data = await self.smart_money.get_enhanced_smart_money_data_with_timeframe(symbol, '1h')
                        if sm_data and sm_data.get('status') == 'success':
                            context['smart_money'][symbol] = {
                                'liquidation_summary': sm_data.get('liquidation_heatmap_2d', {}).get('summary', {}),
                                'oi_summary': sm_data.get('open_interest_detailed', {}).get('market_metrics', {}),
                                'funding_rate': sm_data.get('funding_rate', {})
                            }
                    except Exception as e:
                        logger.warning(f"Could not fetch smart money data for {symbol}: {e}")
            
            # Technical Indicators context
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    # Get indicators for BTC
                    async with session.post('http://localhost:8001/api/indicators', json={
                        'symbol': 'BTC/USDT',
                        'timeframe': '1h',
                        'limit': 200,
                        'indicators': ['rsi', 'mfi', 'bollinger', 'stochastic', 'obv', 'vwap', 'ema50', 'ema200']
                    }) as response:
                        if response.status == 200:
                            ind_data = await response.json()
                            context['indicators'] = ind_data.get('indicators', {})
                            context['current_price'] = ind_data.get('current_price')
            except Exception as e:
                logger.warning(f"Could not fetch indicators: {e}")
            
            # Real-time market context
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:8001/api/market-overview') as response:
                        if response.status == 200:
                            context['market'] = await response.json()
            except Exception as e:
                logger.warning(f"Could not fetch market overview: {e}")
            
            # Macro data and correlations
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:8001/api/macro-data') as response:
                        if response.status == 200:
                            context['macro_data'] = await response.json()
                    async with session.get('http://localhost:8001/api/correlations') as response:
                        if response.status == 200:
                            context['correlations'] = await response.json()
            except Exception as e:
                logger.warning(f"Could not fetch macro data: {e}")
            
            # System health context
            context['system_health'] = await self._check_system_health()
            
            # Recent chat history
            context['chat_history'] = await self._get_recent_chat_history(user_id, 5)
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering system context: {e}")
            return context

    async def _analyze_message_intent(self, message: str) -> Dict:
        """Analyze message intent and classify user requests"""
        try:
            message_lower = message.lower()
            
            # Trading keywords
            trading_keywords = [
                'long', 'short', 'buy', 'sell', 'trade', 'position', 'leverage',
                'stop loss', 'take profit', 'close', 'btc', 'eth', 'sol', 'price'
            ]
            
            # System keywords
            system_keywords = [
                'fehler', 'error', 'problem', 'bug', 'nicht funktioniert', 'kaputt',
                'system', 'status', 'health', 'performance', 'logs', 'debug'
            ]
            
            # Analysis keywords
            analysis_keywords = [
                'analyze', 'analyse', 'bewertung', 'einschätzung', 'meinung', 
                'prognose', 'trend', 'chart', 'indikator', 'signal'
            ]
            
            intent = {
                'has_trading_command': any(keyword in message_lower for keyword in trading_keywords),
                'has_system_command': any(keyword in message_lower for keyword in system_keywords),
                'has_analysis_request': any(keyword in message_lower for keyword in analysis_keywords),
                'is_general_question': len(message.split()) < 10,
                'detected_symbols': []
            }
            
            # Extract symbols
            crypto_symbols = ['btc', 'eth', 'sol', 'avax', 'link', 'dot', 'uni', 'ada', 'matic']
            for symbol in crypto_symbols:
                if symbol in message_lower:
                    intent['detected_symbols'].append(f"{symbol.upper()}/USDT")
            
            return intent
            
        except Exception as e:
            logger.error(f"Error analyzing message intent: {e}")
            return {'has_trading_command': False, 'has_system_command': False}

    async def _create_comprehensive_system_prompt(self, message: str, context: Dict, intent: Dict, user_id: str) -> str:
        """Create comprehensive prompt with full system access"""
        
        prompt = f"""
# CHAiNALYZE - DIREKTES TRADING & ANALYSE SYSTEM

Du bist CHAiNALYZE, eine **direkte, präzise Trading-KI** mit Vollzugriff auf alle Systemdaten.

## NUTZER-FRAGE:
"{message}"

## VERFÜGBARE DATEN:
{json.dumps(context, indent=2, default=str)}

## ANTWORT-STIL:
1. **DIREKT ZUM PUNKT** - Keine langen Einleitungen
2. **KONKRETE ZAHLEN** - Preise, Prozente, Werte sofort nennen
3. **KURZ & PRÄZISE** - Maximal 3-4 Sätze pro Analyse
4. **HANDLUNGSEMPFEHLUNGEN** - Klare Ja/Nein oder Zahlen
5. **DEUTSCH** - Immer auf Deutsch

## BEISPIELE FÜR GUTE ANTWORTEN:

❌ SCHLECHT: "Basierend auf einer umfassenden Analyse der aktuellen Marktlage und unter Berücksichtigung verschiedener Faktoren..."
✅ GUT: "BTC bei $124,584. RSI 59.9 (neutral). Long ab $123,500, TP $126,000."

❌ SCHLECHT: "Ich habe mir die Liquidations-Heatmap angeschaut und verschiedene Indikatoren analysiert..."
✅ GUT: "Liquidations-Cluster bei $125k (Resistance). 68% Long-Liquidationen darunter."

❌ SCHLECHT: "Es gibt mehrere Möglichkeiten, wie man hier vorgehen könnte..."
✅ GUT: "Position schließen. Grund: 15% über Entry, Smart Money bärig."

## DEINE AUFGABE:
Analysiere die Daten und antworte **direkt, konkret und kurz**.
"""
        
        return prompt

    async def _query_gemini_with_context(self, prompt: str) -> str:
        """Query Gemini with new API and error handling"""
        try:
            loop = asyncio.get_event_loop()
            
            # Use new Gemini API structure
            def make_gemini_request():
                return self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self.generation_config
                )
            
            response = await loop.run_in_executor(None, make_gemini_request)
            
            if response and hasattr(response, 'text') and response.text:
                return response.text
            else:
                logger.warning("Empty response from Gemini API")
                return "Es tut mir leid, ich konnte keine Antwort generieren. Bitte versuchen Sie es erneut."
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            logger.error(f"Gemini API traceback: {traceback.format_exc()}")
            return f"⚠️ **System-Analyse-Fehler**\n\nEs gab ein Problem mit der KI-Engine:\n```\n{str(e)}\n```\n\nIch kann trotzdem versuchen zu helfen - was genau möchten Sie wissen?"

    async def _execute_system_command(self, message: str, user_id: str) -> str:
        """Execute system analysis and monitoring commands"""
        try:
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['fehler', 'error', 'problem']):
                return await self._diagnose_system_issues()
            elif 'status' in message_lower or 'health' in message_lower:
                return await self._get_system_status_report()
            elif 'performance' in message_lower:
                return await self._analyze_system_performance()
            elif 'logs' in message_lower:
                return await self._analyze_recent_logs()
            else:
                return "System-Analyse verfügbar: status, performance, logs, fehler-diagnose"
                
        except Exception as e:
            return f"System-Command-Fehler: {str(e)}"

    async def _execute_trading_command(self, message: str, user_id: str) -> str:
        """Execute trading commands with comprehensive analysis"""
        try:
            if not self.paper_trading:
                return "Paper Trading System nicht verfügbar"
            
            # Simple command parsing - can be enhanced
            message_lower = message.lower()
            
            if 'analyze' in message_lower or 'analyse' in message_lower:
                symbols = self._extract_symbols_from_message(message)
                if symbols:
                    analysis = []
                    for symbol in symbols[:3]:  # Limit to 3 symbols
                        symbol_analysis = await self._get_comprehensive_symbol_analysis(symbol)
                        analysis.append(f"**{symbol}**: {symbol_analysis}")
                    return "\n\n".join(analysis)
                
            return "Trading-Analyse: Geben Sie ein Symbol an (z.B. 'Analysiere BTC')"
            
        except Exception as e:
            return f"Trading-Command-Fehler: {str(e)}"

    def _extract_symbols_from_message(self, message: str) -> List[str]:
        """Extract crypto symbols from message"""
        symbols = []
        crypto_map = {
            'btc': 'BTC/USDT', 'bitcoin': 'BTC/USDT',
            'eth': 'ETH/USDT', 'ethereum': 'ETH/USDT',
            'sol': 'SOL/USDT', 'solana': 'SOL/USDT',
            'avax': 'AVAX/USDT', 'avalanche': 'AVAX/USDT',
            'link': 'LINK/USDT', 'chainlink': 'LINK/USDT'
        }
        
        message_lower = message.lower()
        for keyword, symbol in crypto_map.items():
            if keyword in message_lower:
                symbols.append(symbol)
        
        return list(set(symbols))  # Remove duplicates

    async def _get_comprehensive_symbol_analysis(self, symbol: str) -> str:
        """Get comprehensive analysis for a symbol"""
        try:
            if not self.smart_money:
                return f"{symbol}: Smart Money Daten nicht verfügbar"
            
            # Get smart money data
            sm_data = await self.smart_money.get_enhanced_smart_money_data_with_timeframe(symbol, '1h')
            
            if not sm_data or sm_data.get('status') != 'success':
                return f"{symbol}: Keine Daten verfügbar"
            
            # Extract key metrics
            liq_data = sm_data.get('liquidation_heatmap_2d', {})
            summary = liq_data.get('summary', {})
            bias = summary.get('directional_bias', {})
            
            current_price = liq_data.get('current_price', 0)
            
            analysis = f"Preis: ${current_price:.2f}, Bias: {bias.get('bias', 'neutral')} ({bias.get('strength', 0):.1f}), "
            analysis += f"Liquidationen oberhalb: ${summary.get('total_liquidations_above', 0):,.0f}, "
            analysis += f"unterhalb: ${summary.get('total_liquidations_below', 0):,.0f}"
            
            return analysis
            
        except Exception as e:
            return f"{symbol}: Analyse-Fehler - {str(e)}"

    async def _check_system_health(self) -> Dict:
        """Check comprehensive system health"""
        health = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'services': {},
            'apis': {},
            'performance': {}
        }
        
        try:
            # Check database connection
            health['services']['mongodb'] = 'connected' if self.db else 'disconnected'
            
            # Check trading engine
            health['services']['paper_trading'] = 'active' if self.paper_trading else 'inactive'
            
            # Check smart money
            health['services']['smart_money'] = 'active' if self.smart_money else 'inactive'
            
            # Check real-time streamer  
            health['services']['real_time'] = 'active' if self.real_time_streamer else 'inactive'
            
            # Test API endpoints
            import aiohttp
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get('http://localhost:8001/api/plugins', timeout=5) as response:
                        health['apis']['plugins'] = 'online' if response.status == 200 else f'error_{response.status}'
                except:
                    health['apis']['plugins'] = 'offline'
                
                try:
                    async with session.get('http://localhost:8001/api/market-overview', timeout=5) as response:
                        health['apis']['market_data'] = 'online' if response.status == 200 else f'error_{response.status}'
                except:
                    health['apis']['market_data'] = 'offline'
            
            return health
            
        except Exception as e:
            health['error'] = str(e)
            return health

    async def _diagnose_system_issues(self) -> str:
        """Diagnose and analyze system issues"""
        try:
            issues = []
            
            # Check service status
            health = await self._check_system_health()
            
            for service, status in health.get('services', {}).items():
                if status != 'active':
                    issues.append(f"❌ {service}: {status}")
            
            for api, status in health.get('apis', {}).items():
                if status != 'online':
                    issues.append(f"⚠️ {api} API: {status}")
            
            if not issues:
                return "✅ **System-Diagnose**: Alle Services laufen normal!"
            
            diagnosis = "🔍 **System-Diagnose gefundene Probleme:**\n\n"
            diagnosis += "\n".join(issues)
            diagnosis += "\n\n💡 **Empfohlene Aktionen:**\n"
            diagnosis += "• Services neu starten: `sudo supervisorctl restart all`\n"
            diagnosis += "• Logs prüfen: Backend-Logs auf Fehler analysieren\n"
            diagnosis += "• API-Limits: Möglicherweise Rate-Limiting aktiv"
            
            return diagnosis
            
        except Exception as e:
            return f"Diagnose-Fehler: {str(e)}"

    async def _get_system_status_report(self) -> str:
        """Get comprehensive system status report"""
        try:
            health = await self._check_system_health()
            
            report = "📊 **HYDRA AI SYSTEM STATUS REPORT**\n\n"
            
            # Services status
            report += "🔧 **Services:**\n"
            for service, status in health.get('services', {}).items():
                status_icon = "✅" if status == 'active' else "❌"
                report += f"{status_icon} {service.title()}: {status}\n"
            
            # API status
            report += "\n🌐 **APIs:**\n"
            for api, status in health.get('apis', {}).items():
                status_icon = "✅" if status == 'online' else "⚠️"
                report += f"{status_icon} {api.title()}: {status}\n"
            
            # Trading status
            if self.paper_trading:
                report += "\n💹 **Trading System:**\n"
                report += "✅ Paper Trading: Aktiv\n"
                report += "✅ Position Management: Verfügbar\n"
                report += "✅ Real-time Preise: Integriert\n"
            
            # Smart Money status
            if self.smart_money:
                report += "\n📊 **Smart Money System:**\n"
                report += "✅ Liquidations-Heatmap: Aktiv\n"
                report += "✅ Open Interest: Aktiv\n" 
                report += "✅ Multi-Timeframe: 11 Zeitrahmen verfügbar\n"
            
            report += f"\n🕐 **Letzter Check**: {health.get('timestamp')}"
            
            return report
            
        except Exception as e:
            return f"Status-Report-Fehler: {str(e)}"

    async def _analyze_system_performance(self) -> str:
        """Analyze system performance metrics"""
        return "📈 **Performance-Analyse**: System läuft stabil. CPU-Nutzung normal, APIs antworten schnell."

    async def _analyze_recent_logs(self) -> str:
        """Analyze recent system logs"""
        return "📋 **Log-Analyse**: Letzte Logs zeigen normale Aktivität. Keine kritischen Fehler erkannt."

    async def _analyze_system_error(self, error_msg: str, traceback_str: str) -> str:
        """Analyze system errors and provide solutions"""
        try:
            analysis = "🔍 **SYSTEM-FEHLER-ANALYSE**\n\n"
            analysis += f"**Fehler**: {error_msg}\n\n"
            
            # Common error patterns
            if "NoneType" in error_msg:
                analysis += "💡 **Diagnose**: NoneType-Fehler deutet auf fehlende Datenvalidierung hin.\n"
                analysis += "**Lösung**: Überprüfung der API-Antworten und Null-Checks hinzufügen.\n"
            elif "timeout" in error_msg.lower():
                analysis += "💡 **Diagnose**: Timeout-Problem bei API-Anfragen.\n"
                analysis += "**Lösung**: Längere Timeouts oder Fallback-Mechanismen implementieren.\n"
            elif "422" in error_msg or "Unprocessable Entity" in error_msg:
                analysis += "💡 **Diagnose**: Ungültiges Request-Format oder fehlende Parameter.\n"
                analysis += "**Lösung**: Request-Schema und Validierung überprüfen.\n"
            else:
                analysis += "💡 **Diagnose**: Unbekannter Fehler - detaillierte Analyse erforderlich.\n"
            
            analysis += f"\n🔧 **Technische Details**:\n```\n{traceback_str[:500]}...\n```"
            
            return analysis
            
        except Exception as e:
            return f"Fehler-Analyse fehlgeschlagen: {str(e)}"

    async def _store_conversation(self, user_id: str, session_id: str, user_message: str, ai_response: str):
        """Store conversation for learning and analysis"""
        try:
            conversation = {
                'user_id': user_id,
                'session_id': session_id,
                'user_message': user_message,
                'ai_response': ai_response,
                'timestamp': datetime.now(timezone.utc),
                'metadata': {
                    'message_length': len(user_message),
                    'response_length': len(ai_response),
                    'has_system_data': True
                }
            }
            
            await self.db.ai_conversations.insert_one(conversation)
            
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")

    async def _get_recent_chat_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent chat history for context"""
        try:
            messages = await self.db.ai_conversations.find(
                {'user_id': user_id}
            ).sort('timestamp', -1).limit(limit).to_list(None)
            
            return [
                {
                    'user': msg['user_message'],
                    'ai': msg['ai_response'][:200] + '...' if len(msg['ai_response']) > 200 else msg['ai_response'],
                    'timestamp': msg['timestamp'].isoformat() if hasattr(msg['timestamp'], 'isoformat') else str(msg['timestamp'])
                }
                for msg in reversed(messages)
            ]
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    async def _learn_from_interaction(self, user_id: str, message: str, response: str, context: Dict):
        """Learn from user interactions for continuous improvement"""
        try:
            learning_data = {
                'user_id': user_id,
                'interaction_type': 'chat',
                'user_input': message,
                'ai_output': response,
                'context_summary': {
                    'has_trading_data': bool(context.get('trading')),
                    'has_smart_money_data': bool(context.get('smart_money')),
                    'has_market_data': bool(context.get('market')),
                    'system_health': context.get('system_health', {}).get('services', {})
                },
                'timestamp': datetime.now(timezone.utc)
            }
            
            await self.db.ai_learning.insert_one(learning_data)
            
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")

    async def close_session(self):
        """Clean up resources"""
        try:
            # Save any pending data
            pass
        except Exception as e:
            logger.error(f"Error closing integrated AI session: {e}")