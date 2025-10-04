"""
CME Futures Gap Detection Module
"""
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

class GapDetector:
    def __init__(self, db):
        self.db = db
    
    def detect_gaps(self, ohlcv_data):
        """
        Detect CME gaps in price data
        CME closes Friday and opens Monday, gaps occur between these times
        """
        gaps = []
        
        if not ohlcv_data or len(ohlcv_data) < 2:
            return gaps
        
        for i in range(1, len(ohlcv_data)):
            prev_candle = ohlcv_data[i-1]
            curr_candle = ohlcv_data[i]
            
            # Check if there's a gap (current open != previous close)
            prev_close = prev_candle['close']
            curr_open = curr_candle['open']
            
            gap_size = curr_open - prev_close
            gap_percentage = (gap_size / prev_close) * 100
            
            # Only consider significant gaps (> 0.5%)
            if abs(gap_percentage) > 0.5:
                # Determine if it's likely a weekend gap
                prev_time = datetime.fromtimestamp(prev_candle['timestamp'] / 1000, tz=timezone.utc)
                curr_time = datetime.fromtimestamp(curr_candle['timestamp'] / 1000, tz=timezone.utc)
                
                time_diff_hours = (curr_time - prev_time).total_seconds() / 3600
                
                # Weekend gaps typically have 48+ hours between candles
                is_weekend_gap = time_diff_hours > 40
                
                gap_type = 'up' if gap_size > 0 else 'down'
                
                gap = {
                    'timestamp': curr_candle['timestamp'],
                    'gap_start': prev_close,
                    'gap_end': curr_open,
                    'gap_size': abs(gap_size),
                    'gap_percentage': abs(gap_percentage),
                    'gap_type': gap_type,
                    'is_weekend_gap': is_weekend_gap,
                    'is_filled': False
                }
                
                # Check if gap is filled in subsequent candles
                gap['is_filled'] = self.check_gap_filled(ohlcv_data[i:], gap)
                
                gaps.append(gap)
        
        return gaps
    
    def check_gap_filled(self, subsequent_data, gap):
        """Check if a gap has been filled by price action"""
        gap_start = gap['gap_start']
        gap_end = gap['gap_end']
        
        # Check next 50 candles for gap fill
        for candle in subsequent_data[:50]:
            if gap['gap_type'] == 'up':
                # For up gap, check if price went back down to gap_start
                if candle['low'] <= gap_start:
                    return True
            else:
                # For down gap, check if price went back up to gap_start
                if candle['high'] >= gap_start:
                    return True
        
        return False
    
    async def store_gaps(self, symbol, timeframe, gaps):
        """Store detected gaps in database"""
        try:
            for gap in gaps:
                doc = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': gap['timestamp'],
                    'gap_start': gap['gap_start'],
                    'gap_end': gap['gap_end'],
                    'gap_size': gap['gap_size'],
                    'gap_percentage': gap['gap_percentage'],
                    'gap_type': gap['gap_type'],
                    'is_weekend_gap': gap['is_weekend_gap'],
                    'is_filled': gap['is_filled'],
                    'detected_at': datetime.now(timezone.utc).isoformat()
                }
                
                await self.db.gaps.update_one(
                    {
                        'symbol': symbol,
                        'timestamp': gap['timestamp']
                    },
                    {'$set': doc},
                    upsert=True
                )
            
            logger.info(f"Stored {len(gaps)} gaps for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error storing gaps: {str(e)}")
            return False
    
    async def get_gaps(self, symbol, limit=50):
        """Retrieve stored gaps from database"""
        try:
            cursor = self.db.gaps.find(
                {'symbol': symbol}
            ).sort('timestamp', -1).limit(limit)
            
            gaps = await cursor.to_list(length=limit)
            
            # Remove MongoDB _id
            for gap in gaps:
                if '_id' in gap:
                    del gap['_id']
            
            return gaps
        except Exception as e:
            logger.error(f"Error retrieving gaps: {str(e)}")
            return []
