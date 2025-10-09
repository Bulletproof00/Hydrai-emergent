"""
Self-Coding AI System for CHAiNALYZE
===========================================

This module implements a REAL self-coding AI that:
1. Generates and implements new code
2. Creates dynamic plugins  
3. Performs automated backtesting
4. Measures its own success
5. Actually improves the system autonomously
"""

import asyncio
import json
import os
import traceback
import tempfile
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import ast
import importlib.util
from pathlib import Path

from google import genai
from google.genai import types
import pymongo

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelfCodingAI:
    def __init__(self, db, paper_trading, enhanced_smart_money, real_time_streamer):
        self.db = db
        self.paper_trading = paper_trading
        self.smart_money = enhanced_smart_money
        self.real_time_streamer = real_time_streamer
        
        # Initialize Gemini for advanced coding
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.client = genai.Client()
        self.model_name = "gemini-2.5-flash"
        
        # Self-coding configuration
        self.plugins_dir = Path("/app/backend/dynamic_plugins")
        self.plugins_dir.mkdir(exist_ok=True)
        
        # Backtesting engine
        self.backtesting_results = {}
        self.implemented_improvements = {}
        
        # Code safety checks
        self.allowed_imports = [
            'pandas', 'numpy', 'asyncio', 'datetime', 'json', 'logging',
            'typing', 'math', 'statistics', 'collections', 're'
        ]
        
        logger.info("🤖 Self-Coding AI System initialized with code generation capabilities")

    async def generate_and_implement_code(self, improvement_request: str, max_retries: int = 3) -> Dict[str, Any]:
        """Generate and safely implement new code improvements with retry logic"""
        try:
            logger.info(f"🧠 Generating code for improvement: {improvement_request}")
            
            generated_code = None
            safety_check = None
            retry_count = 0
            
            # Phase 1: Generate code with retries for syntax errors
            while retry_count < max_retries:
                try:
                    generated_code = await self._generate_improvement_code(improvement_request, retry_count)
                    
                    # Phase 2: Safety validation
                    safety_check = await self._validate_code_safety(generated_code)
                    
                    if safety_check['is_safe']:
                        logger.info(f"✅ Code generation successful on attempt {retry_count + 1}")
                        break
                    elif safety_check.get('retry_recommended', False):
                        retry_count += 1
                        logger.warning(f"⚠️ Code generation attempt {retry_count} failed, retrying...")
                        logger.warning(f"Issues: {safety_check['issues']}")
                        
                        if retry_count < max_retries:
                            continue
                    else:
                        # Not retryable (e.g., dangerous code)
                        break
                        
                except Exception as e:
                    retry_count += 1
                    logger.error(f"Code generation attempt {retry_count} failed: {e}")
                    if retry_count >= max_retries:
                        break
            
            # Check final result
            if not safety_check or not safety_check['is_safe']:
                return {
                    'status': 'rejected',
                    'reason': 'Code safety validation failed after all retries',
                    'safety_issues': safety_check['issues'] if safety_check else ['Code generation failed'],
                    'attempts': retry_count + 1,
                    'max_retries': max_retries
                }
            
            # Phase 3: Create plugin
            plugin_result = await self._create_dynamic_plugin(generated_code, improvement_request)
            
            # Phase 4: Test implementation
            test_result = await self._test_plugin_implementation(plugin_result['plugin_name'])
            
            # Phase 5: Backtest if trading-related
            backtest_result = None
            if 'trading' in improvement_request.lower() or 'strategy' in improvement_request.lower() or 'scalping' in improvement_request.lower():
                backtest_result = await self._run_automated_backtest(plugin_result['plugin_name'])
            
            # Phase 6: Deploy if successful
            deployment_result = None
            if test_result['success'] and (not backtest_result or backtest_result['profitable']):
                deployment_result = await self._deploy_plugin(plugin_result['plugin_name'])
            
            return {
                'status': 'success',
                'improvement_request': improvement_request,
                'generated_code': generated_code,
                'safety_check': safety_check,
                'plugin_result': plugin_result,
                'test_result': test_result,
                'backtest_result': backtest_result,
                'deployment_result': deployment_result,
                'attempts': retry_count + 1,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Self-coding error: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _generate_improvement_code(self, improvement_request: str, retry_count: int = 0) -> Dict[str, Any]:
        """Generate Python code for specific improvements"""
        
        # Get current system context
        system_context = await self._get_system_context()
        
        # Adjust prompt based on retry count
        retry_instruction = ""
        if retry_count > 0:
            retry_instruction = f"""
            WICHTIG: Dies ist Versuch #{retry_count + 1}. Die vorherigen Versuche hatten Syntax-Fehler.
            Überprüfe EXTRA SORGFÄLTIG:
            - Alle Klammern sind geschlossen: (), [], {{}}
            - Alle Strings haben schließende Anführungszeichen
            - Korrekte Einrückung mit 4 Spaces
            - Keine unvollständigen Zeilen
            - Alle if/for/while Statements sind korrekt geschlossen
            """
        
        coding_prompt = f"""
        Du bist eine Expert-Level Python-Entwicklerin für Trading-Systeme. Generiere PERFEKTEN, syntaktisch korrekten Python-Code.
        
        {retry_instruction}
        
        AUFGABE: {improvement_request}
        
        VERFÜGBARE SYSTEME:
        {json.dumps(system_context, indent=2)}
        
        STRIKTE ANFORDERUNGEN:
        1. PERFEKTE Python-Syntax - ALLE Klammern müssen geschlossen sein
        2. NUR diese Imports erlaubt: {', '.join(self.allowed_imports)}
        3. Implementiere als Plugin-Klasse namens 'DynamicPlugin'
        4. Vollständige Funktionalität in execute() Methode
        5. Alle Strings in Anführungszeichen
        6. Korrekte Einrückung (4 Spaces)
        7. Keine unvollständigen Zeilen oder Syntax-Fehler
        
        EXAKT DIESES TEMPLATE VERWENDEN:
        
        class DynamicPlugin:
            def __init__(self):
                self.name = "Trading_Strategy_Plugin"
                self.version = "1.0.0"
                self.description = "Advanced trading strategy implementation"
                
            async def execute(self, data):
                try:
                    # HIER: Implementierung der Trading-Logik
                    
                    # Beispiel für Scalping-Strategie:
                    current_price = data.get('price', 0)
                    rsi = data.get('rsi', 50)
                    volume = data.get('volume', 0)
                    
                    # Entry-Bedingungen prüfen
                    should_enter = False
                    if rsi < 30 and volume > 1000:  # Überverkauft + hohe Liquidität
                        should_enter = True
                        
                    # Exit-Bedingungen
                    should_exit = False
                    if rsi > 70:  # Überkauft
                        should_exit = True
                    
                    # Trading-Signal generieren
                    signal = None
                    if should_enter:
                        signal = {{"action": "buy", "size": 1.0, "price": current_price}}
                    elif should_exit:
                        signal = {{"action": "sell", "size": 1.0, "price": current_price}}
                    
                    return {{
                        "signal": signal,
                        "analysis": "Strategy executed successfully",
                        "confidence": 0.8,
                        "success": True
                    }}
                    
                except Exception as e:
                    return {{
                        "signal": None,
                        "analysis": f"Error: {{str(e)}}",
                        "confidence": 0.0,
                        "success": False
                    }}
                    
            def validate_input(self, data):
                return isinstance(data, dict) and 'price' in data
                
            def get_metadata(self):
                return {{
                    "name": self.name,
                    "version": self.version,
                    "description": self.description
                }}
        
        ERSETZE NUR die Kommentar-Sektion "# HIER: Implementierung der Trading-Logik" mit der spezifischen Logik für die Anfrage.
        ANTWORTE NUR MIT SYNTAKTISCH PERFEKTEM PYTHON-CODE!
        """
        
        try:
            config = types.GenerateContentConfig(
                temperature=0.3,  # Lower for more consistent code
                top_p=0.9,
                top_k=40,
                max_output_tokens=4000,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=coding_prompt,
                config=config
            )
            
            if response and response.text:
                # Extract Python code from response
                code_text = self._extract_python_code(response.text)
                return {
                    'raw_response': response.text,
                    'extracted_code': code_text,
                    'language': 'python'
                }
            else:
                raise Exception("No code generated by AI")
                
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise

    def _extract_python_code(self, text: str) -> str:
        """Extract Python code from AI response with improved parsing"""
        # Look for code blocks with various markers
        code_markers = ['```python', '```py', '```']
        
        for marker in code_markers:
            if marker in text:
                start = text.find(marker) + len(marker)
                end = text.find('```', start)
                if end != -1:
                    code = text[start:end].strip()
                    
                    # Clean up the code
                    lines = code.split('\n')
                    clean_lines = []
                    
                    for line in lines:
                        # Skip empty lines at the beginning
                        if not clean_lines and not line.strip():
                            continue
                        # Skip obvious non-code lines
                        if line.strip().startswith('#') and ('HIER:' in line or 'TODO:' in line):
                            continue
                        clean_lines.append(line)
                    
                    # Remove trailing empty lines
                    while clean_lines and not clean_lines[-1].strip():
                        clean_lines.pop()
                    
                    return '\n'.join(clean_lines)
        
        # If no code blocks found, try to extract class definition
        if 'class DynamicPlugin' in text:
            start = text.find('class DynamicPlugin')
            # Find the end by looking for the next class or end of text
            remaining = text[start:]
            lines = remaining.split('\n')
            class_lines = []
            indent_level = None
            
            for line in lines:
                if line.strip().startswith('class DynamicPlugin'):
                    class_lines.append(line)
                    indent_level = len(line) - len(line.lstrip())
                elif class_lines:
                    # If we're inside the class
                    current_indent = len(line) - len(line.lstrip()) if line.strip() else 0
                    if line.strip() and current_indent <= indent_level and not line.strip().startswith('#'):
                        # We've reached the end of the class
                        break
                    class_lines.append(line)
            
            return '\n'.join(class_lines).strip()
        
        # Last resort: return cleaned text
        return text.strip()

    async def _validate_code_safety(self, generated_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate code safety before execution with detailed error reporting"""
        try:
            code_text = generated_code['extracted_code']
            
            # Clean up the code text
            code_text = code_text.strip()
            
            # Parse AST for safety analysis
            try:
                tree = ast.parse(code_text)
            except SyntaxError as e:
                # Provide more detailed syntax error information
                error_details = {
                    'line': getattr(e, 'lineno', 'unknown'),
                    'offset': getattr(e, 'offset', 'unknown'),
                    'text': getattr(e, 'text', '').strip() if getattr(e, 'text', None) else 'unknown',
                    'message': str(e)
                }
                
                return {
                    'is_safe': False,
                    'issues': [
                        f'Syntax error at line {error_details["line"]}: {error_details["message"]}',
                        f'Problematic code: "{error_details["text"]}"',
                        'Code generation needs to be retried with better syntax'
                    ],
                    'syntax_error_details': error_details,
                    'retry_recommended': True
                }
            
            safety_issues = []
            class_found = False
            execute_method_found = False
            
            # Enhanced safety and structure checking
            class SafetyChecker(ast.NodeVisitor):
                def visit_Import(self, node):
                    for alias in node.names:
                        if alias.name not in self.allowed_imports:
                            safety_issues.append(f'Disallowed import: {alias.name}')
                
                def visit_ImportFrom(self, node):
                    if node.module and node.module not in self.allowed_imports:
                        safety_issues.append(f'Disallowed import from: {node.module}')
                
                def visit_ClassDef(self, node):
                    nonlocal class_found
                    if node.name == 'DynamicPlugin':
                        class_found = True
                    self.generic_visit(node)
                
                def visit_FunctionDef(self, node):
                    nonlocal execute_method_found
                    if node.name == 'execute':
                        execute_method_found = True
                    self.generic_visit(node)
                    
                def visit_AsyncFunctionDef(self, node):
                    nonlocal execute_method_found
                    if node.name == 'execute':
                        execute_method_found = True
                    self.generic_visit(node)
                
                def visit_Call(self, node):
                    # Check for dangerous function calls
                    if hasattr(node.func, 'id'):
                        if node.func.id in ['exec', 'eval', 'open', '__import__']:
                            safety_issues.append(f'Dangerous function call: {node.func.id}')
                    self.generic_visit(node)
            
            checker = SafetyChecker()
            checker.visit(tree)
            
            # Structure validation
            if not class_found:
                safety_issues.append('Missing DynamicPlugin class definition')
            if not execute_method_found:
                safety_issues.append('Missing execute method in DynamicPlugin class')
            
            # Additional keyword checks
            dangerous_keywords = ['subprocess', 'os.system', 'file', 'delete', 'remove']
            for keyword in dangerous_keywords:
                if keyword in code_text:
                    safety_issues.append(f'Potentially dangerous keyword: {keyword}')
            
            return {
                'is_safe': len(safety_issues) == 0,
                'issues': safety_issues,
                'ast_valid': True,
                'structure_valid': class_found and execute_method_found,
                'retry_recommended': False
            }
            
        except Exception as e:
            return {
                'is_safe': False,
                'issues': [f'Safety validation failed: {e}'],
                'ast_valid': False,
                'retry_recommended': True
            }

    async def _create_dynamic_plugin(self, generated_code: Dict[str, Any], description: str) -> Dict[str, Any]:
        """Create a dynamic plugin from generated code"""
        try:
            # Generate plugin name
            plugin_name = f"dynamic_plugin_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            plugin_file = self.plugins_dir / f"{plugin_name}.py"
            
            # Prepare plugin code
            code_text = generated_code['extracted_code']
            
            # Write plugin file
            with open(plugin_file, 'w') as f:
                f.write(f'"""\nDynamic Plugin: {description}\nGenerated: {datetime.now()}\n"""\n\n')
                f.write(code_text)
            
            # Store plugin metadata
            await self.db.dynamic_plugins.insert_one({
                'plugin_name': plugin_name,
                'description': description,
                'file_path': str(plugin_file),
                'generated_code': code_text,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'created',
                'test_results': None,
                'backtest_results': None
            })
            
            return {
                'plugin_name': plugin_name,
                'file_path': str(plugin_file),
                'status': 'created'
            }
            
        except Exception as e:
            logger.error(f"Plugin creation failed: {e}")
            raise

    async def _test_plugin_implementation(self, plugin_name: str) -> Dict[str, Any]:
        """Test the plugin implementation"""
        try:
            plugin_file = self.plugins_dir / f"{plugin_name}.py"
            
            # Try to import and instantiate
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if DynamicPlugin class exists
            if not hasattr(module, 'DynamicPlugin'):
                return {
                    'success': False,
                    'error': 'DynamicPlugin class not found'
                }
            
            # Instantiate plugin
            plugin = module.DynamicPlugin()
            
            # Test basic functionality
            test_data = {'test': True, 'timestamp': datetime.now().isoformat()}
            
            if hasattr(plugin, 'execute'):
                result = await plugin.execute(test_data)
                success = isinstance(result, dict)
            else:
                success = False
                result = 'execute method not found'
            
            # Update database
            await self.db.dynamic_plugins.update_one(
                {'plugin_name': plugin_name},
                {'$set': {
                    'test_results': {
                        'success': success,
                        'result': str(result),
                        'tested_at': datetime.now(timezone.utc).isoformat()
                    },
                    'status': 'tested'
                }}
            )
            
            return {
                'success': success,
                'result': result,
                'plugin_metadata': plugin.get_metadata() if hasattr(plugin, 'get_metadata') else None
            }
            
        except Exception as e:
            error_msg = f"Plugin test failed: {e}"
            logger.error(error_msg)
            
            # Update database with error
            await self.db.dynamic_plugins.update_one(
                {'plugin_name': plugin_name},
                {'$set': {
                    'test_results': {
                        'success': False,
                        'error': error_msg,
                        'tested_at': datetime.now(timezone.utc).isoformat()
                    },
                    'status': 'failed'
                }}
            )
            
            return {
                'success': False,
                'error': error_msg
            }

    async def _run_automated_backtest(self, plugin_name: str) -> Dict[str, Any]:
        """Run automated backtest for trading plugins"""
        try:
            logger.info(f"🔄 Running backtest for plugin: {plugin_name}")
            
            # Load plugin
            plugin_file = self.plugins_dir / f"{plugin_name}.py"
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            plugin = module.DynamicPlugin()
            
            # Get historical data for backtesting
            backtest_data = await self._get_backtest_data()
            
            # Initialize backtest metrics
            total_trades = 0
            profitable_trades = 0
            total_pnl = 0.0
            max_drawdown = 0.0
            current_drawdown = 0.0
            peak_balance = 10000.0
            current_balance = 10000.0
            
            # Run backtest
            for i, data_point in enumerate(backtest_data):
                try:
                    # Execute plugin with historical data
                    signal = await plugin.execute(data_point)
                    
                    if signal and isinstance(signal, dict):
                        # Simulate trade execution
                        if signal.get('action') in ['buy', 'sell', 'long', 'short']:
                            total_trades += 1
                            
                            # Simulate PnL (simplified)
                            price_change = data_point.get('price_change', 0)
                            position_size = signal.get('size', 1.0)
                            
                            if signal['action'] in ['buy', 'long']:
                                pnl = price_change * position_size
                            else:
                                pnl = -price_change * position_size
                            
                            current_balance += pnl
                            total_pnl += pnl
                            
                            if pnl > 0:
                                profitable_trades += 1
                            
                            # Update drawdown
                            if current_balance > peak_balance:
                                peak_balance = current_balance
                                current_drawdown = 0
                            else:
                                current_drawdown = (peak_balance - current_balance) / peak_balance
                                max_drawdown = max(max_drawdown, current_drawdown)
                
                except Exception as e:
                    logger.warning(f"Backtest execution error at step {i}: {e}")
                    continue
            
            # Calculate metrics
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            avg_pnl_per_trade = total_pnl / total_trades if total_trades > 0 else 0
            total_return = (current_balance - 10000) / 10000
            is_profitable = total_pnl > 0
            
            backtest_result = {
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'avg_pnl_per_trade': avg_pnl_per_trade,
                'final_balance': current_balance,
                'profitable': is_profitable,
                'backtest_period': len(backtest_data),
                'tested_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Store results
            await self.db.dynamic_plugins.update_one(
                {'plugin_name': plugin_name},
                {'$set': {
                    'backtest_results': backtest_result,
                    'status': 'backtested'
                }}
            )
            
            logger.info(f"✅ Backtest completed for {plugin_name}: {win_rate:.2%} win rate, {total_return:.2%} return")
            
            return backtest_result
            
        except Exception as e:
            error_msg = f"Backtest failed: {e}"
            logger.error(error_msg)
            return {
                'profitable': False,
                'error': error_msg,
                'tested_at': datetime.now(timezone.utc).isoformat()
            }

    async def _deploy_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Deploy successful plugin to production"""
        try:
            # Update plugin status to deployed
            await self.db.dynamic_plugins.update_one(
                {'plugin_name': plugin_name},
                {'$set': {
                    'status': 'deployed',
                    'deployed_at': datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Add to implemented improvements
            self.implemented_improvements[plugin_name] = {
                'deployed_at': datetime.now(timezone.utc),
                'status': 'active'
            }
            
            logger.info(f"🚀 Plugin {plugin_name} deployed successfully")
            
            return {
                'deployed': True,
                'plugin_name': plugin_name,
                'deployment_time': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Plugin deployment failed: {e}")
            return {
                'deployed': False,
                'error': str(e)
            }

    async def _get_system_context(self) -> Dict[str, Any]:
        """Get current system context for code generation"""
        return {
            'available_data_sources': [
                'real_time_crypto_prices',
                'smart_money_indicators', 
                'technical_indicators',
                'paper_trading_engine',
                'market_data_history'
            ],
            'current_plugins': list(self.implemented_improvements.keys()),
            'system_capabilities': [
                'price_prediction',
                'trend_analysis', 
                'risk_management',
                'portfolio_optimization',
                'backtesting'
            ]
        }

    async def _get_backtest_data(self) -> List[Dict[str, Any]]:
        """Generate backtest data for testing"""
        # Simplified backtest data generation
        import random
        
        backtest_data = []
        base_price = 50000
        
        for i in range(100):  # 100 data points
            price_change = random.uniform(-0.05, 0.05)  # ±5% change
            current_price = base_price * (1 + price_change)
            
            data_point = {
                'timestamp': (datetime.now() - timedelta(hours=100-i)).isoformat(),
                'price': current_price,
                'price_change': price_change,
                'volume': random.uniform(1000, 10000),
                'rsi': random.uniform(20, 80),
                'moving_average': base_price * random.uniform(0.95, 1.05)
            }
            
            backtest_data.append(data_point)
            base_price = current_price
        
        return backtest_data

    async def chat_with_evolution_ai(self, user_message: str) -> str:
        """Chat interface with the evolution AI"""
        try:
            # Get current evolution context
            evolution_context = await self._get_evolution_context()
            
            chat_prompt = f"""
            Du bist CHAiNALYZE in deinem Self-Evolution Modus. Du kannst:
            - Code generieren und implementieren
            - Neue Trading-Strategien entwickeln
            - Plugins erstellen
            - Backtests durchführen
            - Dich selbst verbessern
            
            EVOLUTION CONTEXT:
            {json.dumps(evolution_context, indent=2)}
            
            USER MESSAGE: {user_message}
            
            Antworte als die sich selbst entwickelnde AI und erkläre:
            1. Was du zu der Anfrage denkst
            2. Welche Code-Verbesserungen du implementieren könntest  
            3. Wie du es testen würdest
            4. Welche Ergebnisse zu erwarten sind
            
            Sei technisch präzise aber verständlich.
            """
            
            config = types.GenerateContentConfig(
                temperature=0.6,
                top_p=0.9,
                max_output_tokens=2000,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=chat_prompt,
                config=config
            )
            
            return response.text if response and response.text else "Entschuldigung, ich konnte keine Antwort generieren."
            
        except Exception as e:
            logger.error(f"Evolution AI chat error: {e}")
            return f"❌ Chat-Fehler: {str(e)}"

    async def _get_evolution_context(self) -> Dict[str, Any]:
        """Get current evolution context"""
        try:
            # Get recent plugins
            recent_plugins = await self.db.dynamic_plugins.find().sort("created_at", -1).limit(5).to_list(5)
            
            return {
                'implemented_plugins': len(self.implemented_improvements),
                'recent_plugins': [p.get('plugin_name', 'unknown') for p in recent_plugins],
                'total_generated_code': await self.db.dynamic_plugins.count_documents({}),
                'successful_backtests': await self.db.dynamic_plugins.count_documents({'backtest_results.profitable': True}),
                'system_improvements': list(self.implemented_improvements.keys())
            }
            
        except Exception as e:
            logger.error(f"Evolution context error: {e}")
            return {'error': str(e)}

    async def get_plugin_status(self) -> Dict[str, Any]:
        """Get status of all dynamic plugins"""
        try:
            plugins = []
            stats = {
                'total_plugins': 0,
                'deployed_plugins': 0,
                'successful_backtests': 0,
                'failed_plugins': 0
            }
            
            if self.db is not None:
                plugins = await self.db.dynamic_plugins.find().sort("created_at", -1).to_list(50)
                
                # Remove MongoDB ObjectIds
                for plugin in plugins:
                    if '_id' in plugin:
                        del plugin['_id']
                
                stats = {
                    'total_plugins': len(plugins),
                    'deployed_plugins': len([p for p in plugins if p.get('status') == 'deployed']),
                    'successful_backtests': len([p for p in plugins if p.get('backtest_results', {}).get('profitable', False)]),
                    'failed_plugins': len([p for p in plugins if p.get('status') == 'failed'])
                }
            else:
                logger.warning("Database connection not available for plugin status")
            
            return {
                'plugins': plugins,
                'statistics': stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Plugin status error: {e}")
            return {
                'plugins': [],
                'statistics': {
                    'total_plugins': 0,
                    'deployed_plugins': 0,
                    'successful_backtests': 0,
                    'failed_plugins': 0
                },
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

# Global instance
self_coding_ai = None

async def initialize_self_coding_ai(db, paper_trading, enhanced_smart_money, real_time_streamer):
    """Initialize the global self-coding AI instance"""
    global self_coding_ai
    self_coding_ai = SelfCodingAI(db, paper_trading, enhanced_smart_money, real_time_streamer)
    logger.info("🤖 Self-Coding AI System initialized and ready for autonomous development")
    return self_coding_ai