"""
Paper Trading System - Complete Exchange-like Trading Simulation
Supports leverage trading, position management, and realistic fee simulation
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import random

logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class PaperTradingEngine:
    def __init__(self, db, enhanced_smart_money=None):
        self.db = db
        self._enhanced_smart_money = enhanced_smart_money
        
        # Trading Fees (similar to Binance futures)
        self.maker_fee = 0.0002  # 0.02%
        self.taker_fee = 0.0004  # 0.04%
        
        # Slippage configuration - Realistic for crypto
        self.base_slippage = 0.0001  # 0.01% base slippage (much more realistic)
        self.max_slippage = 0.0005   # 0.05% max slippage (realistic for BTC)
        
        # Leverage limits
        self.min_leverage = 1
        self.max_leverage = 100
        
        # Minimum order sizes (USDT value)
        self.min_order_size = 5.0
        
        # Risk limits
        self.max_position_size_ratio = 0.95  # Max 95% of balance per position
        
        # Cache for real-time prices
        self.price_cache = {}
        
        logger.info("Paper Trading Engine initialized")

    async def create_user_account(self, user_id: str, initial_balance: float = 10000.0) -> Dict:
        """Create a new paper trading account for user"""
        try:
            account = {
                'user_id': user_id,
                'balance': initial_balance,
                'initial_balance': initial_balance,
                'equity': initial_balance,
                'margin_used': 0.0,
                'free_margin': initial_balance,
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'created_at': datetime.now(timezone.utc),
                'last_updated': datetime.now(timezone.utc)
            }
            
            # Insert account
            result = await self.db.paper_trading_accounts.insert_one(account)
            account['_id'] = str(result.inserted_id)
            
            logger.info(f"Created paper trading account for user {user_id} with ${initial_balance}")
            return account
            
        except Exception as e:
            logger.error(f"Error creating user account: {e}")
            raise

    async def get_user_account(self, user_id: str) -> Optional[Dict]:
        """Get user's paper trading account"""
        try:
            account = await self.db.paper_trading_accounts.find_one({'user_id': user_id})
            if account:
                account['_id'] = str(account['_id'])
                # Update unrealized PnL
                await self._update_unrealized_pnl(account)
            return account
            
        except Exception as e:
            logger.error(f"Error getting user account: {e}")
            return None

    async def place_order(self, user_id: str, symbol: str, side: str, order_type: str, 
                         quantity: float, price: float = None, leverage: int = 1,
                         stop_loss: float = None, take_profit: float = None,
                         reduce_only: bool = False) -> Dict:
        """Place a new order"""
        try:
            # Validate inputs
            if leverage < self.min_leverage or leverage > self.max_leverage:
                return {'success': False, 'error': f'Leverage must be between {self.min_leverage}-{self.max_leverage}x'}
            
            # Get user account
            account = await self.get_user_account(user_id)
            if not account:
                return {'success': False, 'error': 'Account not found'}
            
            # Get current price
            current_price = await self._get_current_price(symbol)
            if not current_price:
                return {'success': False, 'error': f'Price not available for {symbol}'}
            
            # Calculate order value
            order_price = price if order_type == 'limit' else current_price
            order_value = quantity * order_price
            
            # Check minimum order size
            if order_value < self.min_order_size:
                return {'success': False, 'error': f'Minimum order size is ${self.min_order_size}'}
            
            # Calculate required margin
            required_margin = order_value / leverage
            
            # Check available balance for new positions
            if not reduce_only and account['free_margin'] < required_margin:
                return {'success': False, 'error': 'Insufficient margin'}
            
            # Create order
            order = {
                'order_id': str(uuid.uuid4()),
                'user_id': user_id,
                'symbol': symbol,
                'side': side,
                'order_type': order_type,
                'quantity': quantity,
                'price': price,
                'leverage': leverage,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reduce_only': reduce_only,
                'status': 'pending',
                'filled_quantity': 0.0,
                'filled_price': 0.0,
                'fee_paid': 0.0,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            
            # Execute order immediately for market orders
            if order_type == 'market':
                execution_result = await self._execute_order(order, current_price)
                order.update(execution_result)
            
            # Store order
            await self.db.paper_trading_orders.insert_one(order)
            order['_id'] = str(order['_id'])
            
            logger.info(f"Order placed: {order['order_id']} - {side} {quantity} {symbol} @{order_price}")
            
            return {'success': True, 'order': order}
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}

    async def _execute_order(self, order: Dict, execution_price: float) -> Dict:
        """Execute an order and update positions"""
        try:
            # Calculate slippage
            slippage = self._calculate_slippage(order['quantity'] * execution_price)
            
            if order['side'] == 'buy':
                final_price = execution_price * (1 + slippage)
            else:
                final_price = execution_price * (1 - slippage)
            
            # Calculate fee
            fee = order['quantity'] * final_price * self.taker_fee
            
            # Update order
            result = {
                'status': 'filled',
                'filled_quantity': order['quantity'],
                'filled_price': final_price,
                'fee_paid': fee,
                'updated_at': datetime.now(timezone.utc)
            }
            
            # Update or create position
            await self._update_position(order, final_price, fee)
            
            # Update account balance
            await self._update_account_after_execution(order['user_id'], fee)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {'status': 'rejected', 'error': str(e)}

    async def _update_position(self, order: Dict, execution_price: float, fee: float):
        """Update or create position after order execution"""
        try:
            user_id = order['user_id']
            symbol = order['symbol']
            
            # Find existing position
            position = await self.db.paper_trading_positions.find_one({
                'user_id': user_id,
                'symbol': symbol,
                'status': 'open'
            })
            
            if not position:
                # Create new position
                position_side = 'long' if order['side'] == 'buy' else 'short'
                
                position = {
                    'position_id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'symbol': symbol,
                    'side': position_side,
                    'size': order['quantity'] if order['side'] == 'buy' else -order['quantity'],
                    'entry_price': execution_price,
                    'mark_price': execution_price,
                    'leverage': order['leverage'],
                    'margin': (order['quantity'] * execution_price) / order['leverage'],
                    'unrealized_pnl': 0.0,
                    'realized_pnl': 0.0,
                    'total_fees': fee,
                    'liquidation_price': self._calculate_liquidation_price(
                        execution_price, order['leverage'], position_side
                    ),
                    'stop_loss': order.get('stop_loss'),
                    'take_profit': order.get('take_profit'),
                    'status': 'open',
                    'created_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc)
                }
                
                await self.db.paper_trading_positions.insert_one(position)
                
            else:
                # Update existing position (adding to position or closing)
                await self._modify_existing_position(position, order, execution_price, fee)
            
        except Exception as e:
            logger.error(f"Error updating position: {e}")

    async def _modify_existing_position(self, position: Dict, order: Dict, execution_price: float, fee: float):
        """Modify existing position based on new order"""
        try:
            current_size = position['size']
            order_size = order['quantity'] if order['side'] == 'buy' else -order['quantity']
            
            # Check if this closes or reduces position
            if (current_size > 0 and order_size < 0) or (current_size < 0 and order_size > 0):
                # Closing or reducing position
                if abs(order_size) >= abs(current_size):
                    # Full close + potential new position
                    await self._close_position_fully(position, execution_price, fee, abs(current_size))
                    
                    remaining_size = abs(order_size) - abs(current_size)
                    if remaining_size > 0:
                        # Create new position in opposite direction
                        await self._create_new_position_after_close(
                            order, execution_price, remaining_size, fee
                        )
                else:
                    # Partial close
                    await self._close_position_partially(position, execution_price, fee, abs(order_size))
            else:
                # Adding to existing position
                await self._add_to_position(position, order, execution_price, fee)
                
        except Exception as e:
            logger.error(f"Error modifying existing position: {e}")

    async def close_position(self, user_id: str, position_id: str, close_percentage: float = 100.0) -> Dict:
        """Close position partially or fully"""
        try:
            # Get position
            position = await self.db.paper_trading_positions.find_one({
                'position_id': position_id,
                'user_id': user_id,
                'status': 'open'
            })
            
            if not position:
                return {'success': False, 'error': 'Position not found'}
            
            # Get current price
            current_price = await self._get_current_price(position['symbol'])
            if not current_price:
                return {'success': False, 'error': 'Cannot get current price'}
            
            # Calculate close size
            close_percentage = min(max(close_percentage, 0), 100)  # Ensure 0-100%
            close_size = abs(position['size']) * (close_percentage / 100)
            
            # Calculate PnL
            if position['side'] == 'long':
                pnl = (current_price - position['entry_price']) * close_size
            else:
                pnl = (position['entry_price'] - current_price) * close_size
            
            # Calculate fees
            fee = close_size * current_price * self.taker_fee
            net_pnl = pnl - fee
            
            if close_percentage >= 100:
                # Full close
                await self.db.paper_trading_positions.update_one(
                    {'position_id': position_id},
                    {
                        '$set': {
                            'status': 'closed',
                            'realized_pnl': position.get('realized_pnl', 0) + net_pnl,
                            'total_fees': position.get('total_fees', 0) + fee,
                            'closed_at': datetime.now(timezone.utc),
                            'updated_at': datetime.now(timezone.utc)
                        }
                    }
                )
            else:
                # Partial close
                remaining_size = position['size'] * (1 - close_percentage / 100)
                
                await self.db.paper_trading_positions.update_one(
                    {'position_id': position_id},
                    {
                        '$set': {
                            'size': remaining_size,
                            'realized_pnl': position.get('realized_pnl', 0) + net_pnl,
                            'total_fees': position.get('total_fees', 0) + fee,
                            'updated_at': datetime.now(timezone.utc)
                        }
                    }
                )
            
            # Update account with realized PnL
            await self._update_account_pnl(user_id, net_pnl)
            
            logger.info(f"Position {position_id} closed {close_percentage}% - PnL: ${net_pnl:.2f}")
            
            return {
                'success': True,
                'close_percentage': close_percentage,
                'close_size': close_size,
                'pnl': pnl,
                'fee': fee,
                'net_pnl': net_pnl,
                'close_price': current_price
            }
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}

    async def _close_position_partially(self, position: Dict, close_price: float, fee: float, close_size: float):
        """Partially close a position"""
        try:
            entry_price = position['entry_price']
            position_size = abs(position['size'])
            
            # Calculate PnL for closed portion
            if position['side'] == 'long':
                pnl = (close_price - entry_price) * close_size
            else:
                pnl = (entry_price - close_price) * close_size
            
            # Update position
            new_size = position['size'] * (1 - close_size / position_size)
            
            await self.db.paper_trading_positions.update_one(
                {'_id': position['_id']},
                {
                    '$set': {
                        'size': new_size,
                        'realized_pnl': position['realized_pnl'] + pnl - fee,
                        'total_fees': position['total_fees'] + fee,
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            
            # Update account with realized PnL
            await self._update_account_pnl(position['user_id'], pnl - fee)
            
        except Exception as e:
            logger.error(f"Error partially closing position: {e}")

    async def add_margin_to_position(self, user_id: str, position_id: str, margin_amount: float) -> Dict:
        """Add margin to an existing position"""
        try:
            # Get position
            position = await self.db.paper_trading_positions.find_one({
                'position_id': position_id,
                'user_id': user_id,
                'status': 'open'
            })
            
            if not position:
                return {'success': False, 'error': 'Position not found'}
            
            # Get account
            account = await self.get_user_account(user_id)
            if not account or account['free_margin'] < margin_amount:
                return {'success': False, 'error': 'Insufficient free margin'}
            
            # Update position margin
            new_margin = position['margin'] + margin_amount
            new_leverage = (abs(position['size']) * position['entry_price']) / new_margin
            
            # Recalculate liquidation price
            new_liquidation_price = self._calculate_liquidation_price(
                position['entry_price'], new_leverage, position['side']
            )
            
            await self.db.paper_trading_positions.update_one(
                {'position_id': position_id},
                {
                    '$set': {
                        'margin': new_margin,
                        'leverage': new_leverage,
                        'liquidation_price': new_liquidation_price,
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            
            # Update account
            await self._update_account_margin(user_id, -margin_amount)
            
            logger.info(f"Added ${margin_amount} margin to position {position_id}")
            
            return {'success': True, 'new_margin': new_margin, 'new_leverage': new_leverage}
            
        except Exception as e:
            logger.error(f"Error adding margin: {e}")
            return {'success': False, 'error': str(e)}

    async def reduce_margin_from_position(self, user_id: str, position_id: str, margin_amount: float) -> Dict:
        """Remove margin from an existing position"""
        try:
            position = await self.db.paper_trading_positions.find_one({
                'position_id': position_id,
                'user_id': user_id,
                'status': 'open'
            })
            
            if not position:
                return {'success': False, 'error': 'Position not found'}
            
            current_margin = position['margin']
            
            # Check if we can reduce this much margin
            min_margin = (abs(position['size']) * position['entry_price']) / self.max_leverage
            
            if current_margin - margin_amount < min_margin:
                return {
                    'success': False, 
                    'error': f'Cannot reduce margin below minimum (${min_margin:.2f})'
                }
            
            new_margin = current_margin - margin_amount
            new_leverage = (abs(position['size']) * position['entry_price']) / new_margin
            
            # Recalculate liquidation price
            new_liquidation_price = self._calculate_liquidation_price(
                position['entry_price'], new_leverage, position['side']
            )
            
            await self.db.paper_trading_positions.update_one(
                {'position_id': position_id},
                {
                    '$set': {
                        'margin': new_margin,
                        'leverage': new_leverage,
                        'liquidation_price': new_liquidation_price,
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            
            # Update account
            await self._update_account_margin(user_id, margin_amount)
            
            logger.info(f"Reduced ${margin_amount} margin from position {position_id}")
            
            return {'success': True, 'new_margin': new_margin, 'new_leverage': new_leverage}
            
        except Exception as e:
            logger.error(f"Error reducing margin: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_slippage(self, order_value: float) -> float:
        """Calculate realistic slippage based on order size"""
        # Realistic slippage for crypto markets
        size_factor = min(order_value / 1000000, 1.0)  # Max at $1M orders
        slippage = self.base_slippage + (size_factor * (self.max_slippage - self.base_slippage))
        
        # Minimal random component for more predictable execution
        random_factor = random.uniform(0.8, 1.2)  # Much smaller range
        return slippage * random_factor

    def _calculate_liquidation_price(self, entry_price: float, leverage: float, side: str) -> float:
        """Calculate liquidation price for position"""
        # Simplified liquidation calculation (maintenance margin = 0.5%)
        maintenance_margin_ratio = 0.005
        
        if side == 'long':
            return entry_price * (1 - (1/leverage) + maintenance_margin_ratio)
        else:
            return entry_price * (1 + (1/leverage) - maintenance_margin_ratio)

    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current LIVE price with robust fallback system for trading"""
        try:
            # Try Binance first (if available)
            from .binance_data import binance_provider
            
            # Get LIVE price directly from Binance 24h stats
            stats_24h = await binance_provider.get_24h_stats(symbol, 'spot')
            
            if stats_24h and stats_24h['price'] > 0:
                logger.debug(f"💰 Binance live price for trading: {symbol} = ${stats_24h['price']:,.2f}")
                return stats_24h['price']
            
            # If Spot fails, try Futures
            futures_stats = await binance_provider.get_24h_stats(symbol, 'futures')
            if futures_stats and futures_stats['price'] > 0:
                logger.debug(f"💰 Binance futures price for trading: {symbol} = ${futures_stats['price']:,.2f}")
                return futures_stats['price']
            
            # FALLBACK 1: CoinGecko API (no geographic restrictions)
            logger.warning(f"⚠️ Binance unavailable for {symbol}, trying CoinGecko fallback...")
            price = await self._get_coingecko_price(symbol)
            if price:
                logger.info(f"🔄 CoinGecko fallback price for {symbol} = ${price:,.2f}")
                return price
            
            # FALLBACK 2: Mock realistic price for critical trading functions
            logger.error(f"❌ All price sources failed for {symbol}, using emergency fallback")
            return await self._get_emergency_price_fallback(symbol)
            
        except Exception as e:
            logger.error(f"❌ Critical price error for {symbol}: {e}")
            return await self._get_emergency_price_fallback(symbol)

    async def _update_unrealized_pnl(self, account: Dict):
        """Update unrealized PnL for all open positions"""
        try:
            positions = await self.db.paper_trading_positions.find({
                'user_id': account['user_id'],
                'status': 'open'
            }).to_list(None)
            
            total_unrealized_pnl = 0.0
            total_margin_used = 0.0
            
            for position in positions:
                current_price = await self._get_current_price(position['symbol'])
                if current_price:
                    # Calculate unrealized PnL
                    if position['side'] == 'long':
                        unrealized_pnl = (current_price - position['entry_price']) * abs(position['size'])
                    else:
                        unrealized_pnl = (position['entry_price'] - current_price) * abs(position['size'])
                    
                    total_unrealized_pnl += unrealized_pnl
                    total_margin_used += position['margin']
                    
                    # Update position mark price
                    await self.db.paper_trading_positions.update_one(
                        {'_id': position['_id']},
                        {
                            '$set': {
                                'mark_price': current_price,
                                'unrealized_pnl': unrealized_pnl,
                                'updated_at': datetime.now(timezone.utc)
                            }
                        }
                    )
            
            # Update account
            equity = account['balance'] + total_unrealized_pnl
            free_margin = equity - total_margin_used
            
            await self.db.paper_trading_accounts.update_one(
                {'user_id': account['user_id']},
                {
                    '$set': {
                        'unrealized_pnl': total_unrealized_pnl,
                        'equity': equity,
                        'margin_used': total_margin_used,
                        'free_margin': free_margin,
                        'last_updated': datetime.now(timezone.utc)
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating unrealized PnL: {e}")

    async def get_positions(self, user_id: str) -> List[Dict]:
        """Get all open positions for user"""
        try:
            positions = await self.db.paper_trading_positions.find({
                'user_id': user_id,
                'status': 'open'
            }).sort('created_at', -1).to_list(None)
            
            # Convert ObjectId to string
            for position in positions:
                position['_id'] = str(position['_id'])
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    async def get_trade_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get trade history for user"""
        try:
            orders = await self.db.paper_trading_orders.find({
                'user_id': user_id,
                'status': {'$in': ['filled', 'partially_filled']}
            }).sort('created_at', -1).limit(limit).to_list(None)
            
            # Convert ObjectId to string
            for order in orders:
                order['_id'] = str(order['_id'])
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []

    async def _update_account_after_execution(self, user_id: str, fee: float):
        """Update account balance after order execution"""
        try:
            await self.db.paper_trading_accounts.update_one(
                {'user_id': user_id},
                {
                    '$inc': {
                        'total_trades': 1
                    },
                    '$set': {
                        'last_updated': datetime.now(timezone.utc)
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating account after execution: {e}")

    async def _update_account_pnl(self, user_id: str, realized_pnl: float):
        """Update account with realized PnL"""
        try:
            update_data = {
                'realized_pnl': realized_pnl,
                'last_updated': datetime.now(timezone.utc)
            }
            
            if realized_pnl > 0:
                update_data['winning_trades'] = 1
            else:
                update_data['losing_trades'] = 1
            
            await self.db.paper_trading_accounts.update_one(
                {'user_id': user_id},
                {
                    '$inc': update_data,
                    '$inc': {'balance': realized_pnl}
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating account PnL: {e}")

    async def _update_account_margin(self, user_id: str, margin_change: float):
        """Update account free margin"""
        try:
            await self.db.paper_trading_accounts.update_one(
                {'user_id': user_id},
                {
                    '$inc': {'free_margin': margin_change},
                    '$set': {'last_updated': datetime.now(timezone.utc)}
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating account margin: {e}")

    async def _add_to_position(self, position: Dict, order: Dict, execution_price: float, fee: float):
        """Add to existing position (increase position size)"""
        try:
            current_size = abs(position['size'])
            order_size = order['quantity']
            
            # Calculate new weighted average entry price
            current_value = current_size * position['entry_price']
            order_value = order_size * execution_price
            total_size = current_size + order_size
            new_entry_price = (current_value + order_value) / total_size
            
            # Update position size (maintain direction)
            new_size = position['size'] + (order_size if position['size'] > 0 else -order_size)
            
            # Calculate new margin requirement
            new_margin = (total_size * new_entry_price) / order['leverage']
            
            # Recalculate liquidation price
            new_liquidation_price = self._calculate_liquidation_price(
                new_entry_price, order['leverage'], position['side']
            )
            
            await self.db.paper_trading_positions.update_one(
                {'_id': position['_id']},
                {
                    '$set': {
                        'size': new_size,
                        'entry_price': new_entry_price,
                        'margin': new_margin,
                        'leverage': order['leverage'],
                        'liquidation_price': new_liquidation_price,
                        'total_fees': position['total_fees'] + fee,
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Added to position: new size {new_size}, new entry ${new_entry_price:.2f}")
            
        except Exception as e:
            logger.error(f"Error adding to position: {e}")

    async def _close_position_fully(self, position: Dict, close_price: float, fee: float, close_size: float):
        """Fully close a position"""
        try:
            entry_price = position['entry_price']
            position_size = abs(position['size'])
            
            # Calculate PnL for full position
            if position['side'] == 'long':
                pnl = (close_price - entry_price) * position_size
            else:
                pnl = (entry_price - close_price) * position_size
            
            # Update position to closed
            await self.db.paper_trading_positions.update_one(
                {'_id': position['_id']},
                {
                    '$set': {
                        'size': 0,
                        'status': 'closed',
                        'realized_pnl': position['realized_pnl'] + pnl - fee,
                        'total_fees': position['total_fees'] + fee,
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            
            # Update account with realized PnL and free up margin
            await self._update_account_pnl(position['user_id'], pnl - fee)
            await self._update_account_margin(position['user_id'], position['margin'])
            
            logger.info(f"Closed position fully: PnL ${pnl - fee:.2f}")
            
        except Exception as e:
            logger.error(f"Error closing position fully: {e}")

    async def _create_new_position_after_close(self, order: Dict, execution_price: float, remaining_size: float, fee: float):
        """Create new position after closing existing one"""
        try:
            position_side = 'long' if order['side'] == 'buy' else 'short'
            
            position = {
                'position_id': str(uuid.uuid4()),
                'user_id': order['user_id'],
                'symbol': order['symbol'],
                'side': position_side,
                'size': remaining_size if order['side'] == 'buy' else -remaining_size,
                'entry_price': execution_price,
                'mark_price': execution_price,
                'leverage': order['leverage'],
                'margin': (remaining_size * execution_price) / order['leverage'],
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'total_fees': fee,
                'liquidation_price': self._calculate_liquidation_price(
                    execution_price, order['leverage'], position_side
                ),
                'stop_loss': order.get('stop_loss'),
                'take_profit': order.get('take_profit'),
                'status': 'open',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
            
            await self.db.paper_trading_positions.insert_one(position)
            
            logger.info(f"Created new position after close: {remaining_size} {order['symbol']}")
            
        except Exception as e:
            logger.error(f"Error creating new position after close: {e}")