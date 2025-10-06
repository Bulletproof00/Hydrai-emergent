"""
Dynamic Plugin: Erstelle eine erweiterte Scalping-Strategie mit RSI (14), Volume-Indikatoren, Liquidations-Cluster-Analyse, Entry/Exit-Logic für Long-Positionen, 5000€ Kapital, Ziel 300 USD Gewinn
Generated: 2025-10-06 11:00:47.452201
"""

class DynamicPlugin:
    def __init__(self):
        self.name = "Advanced_Scalping_Strategy"
        self.version = "1.0.0"
        self.description = "Advanced scalping strategy with RSI, volume, and liquidation cluster analysis for long positions."
        self.capital = 5000.00  # Initial capital in EUR
        self.target_profit_usd = 300.00
        self.current_position = None  # Stores active position details: {'entry_price': float, 'size': float, 'entry_time': datetime}
        self.profit_usd_achieved = 0.0
        self.trade_history = []
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    async def execute(self, data: dict) -> dict:
        try:
            # HIER: Implementierung der Trading-Logik
            self.logger.info(f"Executing strategy with data: {data}")

            # --- Data Extraction and Validation ---
            current_price_usd = data.get('real_time_crypto_prices', {}).get('price_usd', None)
            if current_price_usd is None:
                self.logger.warning("Missing 'price_usd' in real_time_crypto_prices. Cannot execute.")
                return {
                    "signal": None,
                    "analysis": "Missing required price data.",
                    "confidence": 0.0,
                    "success": False
                }

            # Assume 'technical_indicators' contains RSI and Volume
            technical_indicators = data.get('technical_indicators', {})
            rsi_14 = technical_indicators.get('rsi_14', 50.0)
            volume_24h = technical_indicators.get('volume_24h', 0.0) # Example volume, adjust as per actual data structure
            
            # Assume 'smart_money_indicators' contains liquidation clusters
            smart_money_indicators = data.get('smart_money_indicators', {})
            liquidation_clusters = smart_money_indicators.get('liquidation_clusters', []) # List of {'price': float, 'amount_usd': float}

            # --- Strategy Parameters ---
            RSI_OVERSOLD_THRESHOLD = 30
            RSI_OVERBOUGHT_THRESHOLD = 70
            MIN_VOLUME_FOR_ENTRY = 100_000_000 # Example: Minimum 24h volume in USD for a liquid asset
            LIQUIDATION_CLUSTER_IMPACT_THRESHOLD = 5_000_000 # Example: Cluster size in USD to consider significant
            STOP_LOSS_PERCENT = 0.015 # 1.5% stop loss
            TAKE_PROFIT_PERCENT = 0.008 # 0.8% take profit for scalping
            POSITION_SIZE_PERCENT_OF_CAPITAL = 0.05 # Use 5% of capital per trade

            # --- Convert Capital to USD for position sizing (assuming 1 EUR = 1.08 USD for simplicity) ---
            eur_to_usd_rate = 1.08 # This should ideally come from real-time data
            capital_usd = self.capital * eur_to_usd_rate

            signal = None
            analysis_message = "No action taken."
            confidence = 0.5
            success = True

            # --- Check for existing position and manage exits ---
            if self.current_position:
                entry_price = self.current_position['entry_price']
                position_size_usd = self.current_position['size'] * entry_price # Size is in crypto units
                current_profit_loss_percent = (current_price_usd - entry_price) / entry_price

                # Calculate stop loss and take profit prices
                stop_loss_price = entry_price * (1 - STOP_LOSS_PERCENT)
                take_profit_price = entry_price * (1 + TAKE_PROFIT_PERCENT)

                # Check for Take Profit
                if current_price_usd >= take_profit_price:
                    signal = {"action": "sell", "size": self.current_position['size'], "price": current_price_usd, "type": "take_profit"}
                    profit_usd = (current_price_usd - entry_price) * self.current_position['size']
                    self.profit_usd_achieved += profit_usd
                    self.trade_history.append({"type": "exit", "action": "sell", "price": current_price_usd, "size": self.current_position['size'], "profit_usd": profit_usd, "timestamp": datetime.datetime.now().isoformat()})
                    self.current_position = None
                    analysis_message = f"Exiting long position at {current_price_usd:.2f} USD (Take Profit). Profit: {profit_usd:.2f} USD. Total profit: {self.profit_usd_achieved:.2f} USD."
                    self.logger.info(analysis_message)
                    confidence = 0.9
                # Check for Stop Loss
                elif current_price_usd <= stop_loss_price:
                    signal = {"action": "sell", "size": self.current_position['size'], "price": current_price_usd, "type": "stop_loss"}
                    loss_usd = (current_price_usd - entry_price) * self.current_position['size']
                    self.profit_usd_achieved += loss_usd # Loss is negative
                    self.trade_history.append({"type": "exit", "action": "sell", "price": current_price_usd, "size": self.current_position['size'], "profit_usd": loss_usd, "timestamp": datetime.datetime.now().isoformat()})
                    self.current_position = None
                    analysis_message = f"Exiting long position at {current_price_usd:.2f} USD (Stop Loss). Loss: {loss_usd:.2f} USD. Total profit: {self.profit_usd_achieved:.2f} USD."
                    self.logger.warning(analysis_message)
                    confidence = 0.9
                # Check for RSI Overbought as an early exit signal (if not yet at TP)
                elif rsi_14 > RSI_OVERBOUGHT_THRESHOLD:
                    # Consider partial or full exit if RSI is overbought and profit is positive
                    if current_profit_loss_percent > 0:
                        signal = {"action": "sell", "size": self.current_position['size'], "price": current_price_usd, "type": "rsi_overbought_exit"}
                        profit_usd = (current_price_usd - entry_price) * self.current_position['size']
                        self.profit_usd_achieved += profit_usd
                        self.trade_history.append({"type": "exit", "action": "sell", "price": current_price_usd, "size": self.current_position['size'], "profit_usd": profit_usd, "timestamp": datetime.datetime.now().isoformat()})
                        self.current_position = None
                        analysis_message = f"Exiting long position at {current_price_usd:.2f} USD (RSI Overbought). Profit: {profit_usd:.2f} USD. Total profit: {self.profit_usd_achieved:.2f} USD."
                        self.logger.info(analysis_message)
                        confidence = 0.8
                    else:
                        analysis_message = f"RSI overbought ({rsi_14:.2f}) but position is in loss. Holding for now."
                        confidence = 0.6
                else:
                    analysis_message = f"Holding long position. Current P/L: {current_profit_loss_percent:.2%}. RSI: {rsi_14:.2f}."
                    confidence = 0.7

            # --- Check for entry conditions if no active position and target profit not met ---
            elif self.profit_usd_achieved < self.target_profit_usd:
                should_enter_long = False
                entry_reason = []

                # Condition 1: RSI Oversold
                if rsi_14 < RSI_OVERSOLD_THRESHOLD:
                    should_enter_long = True
                    entry_reason.append(f"RSI ({rsi_14:.2f}) is oversold (< {RSI_OVERSOLD_THRESHOLD}).")

                # Condition 2: Sufficient Volume
                if volume_24h < MIN_VOLUME_FOR_ENTRY:
                    should_enter_long = False # Override if volume is too low
                    entry_reason.append(f"Volume ({volume_24h:.2f}) is too low (< {MIN_VOLUME_FOR_ENTRY}).")
                    self.logger.info(f"Volume too low for entry: {volume_24h:.2f}")

                # Condition 3: Liquidation Cluster Analysis (looking for support below current price)
                significant_liquidation_support = False
                for cluster in liquidation_clusters:
                    cluster_price = cluster.get('price')
                    cluster_amount_usd = cluster.get('amount_usd')
                    if cluster_price and cluster_amount_usd and \
                       cluster_amount_usd > LIQUIDATION_CLUSTER_IMPACT_THRESHOLD and \
                       cluster_price < current_price_usd * (1 - STOP_LOSS_PERCENT / 2) and \
                       cluster_price > current_price_usd * (1 - STOP_LOSS_PERCENT * 2): # Cluster slightly below current price, within a reasonable range
                        significant_liquidation_support = True
                        entry_reason.append(f"Significant liquidation cluster ({cluster_amount_usd:.2f} USD) found at {cluster_price:.2f} USD providing potential support.")
                        break
                
                if should_enter_long and not significant_liquidation_support:
                    # If RSI is oversold but no strong liquidation support, be more cautious
                    # For this strategy, we'll make liquidation clusters a strong reinforcing factor, not strictly mandatory
                    # However, if we want to be more conservative, we could set should_enter_long = False here
                    self.logger.info("RSI oversold but no significant liquidation support found. Proceeding with caution.")
                    pass # Allow entry but with lower confidence or adjust sizing

                # --- Execute Entry ---
                if should_enter_long and volume_24h >= MIN_VOLUME_FOR_ENTRY:
                    position_size_usd = capital_usd * POSITION_SIZE_PERCENT_OF_CAPITAL
                    if position_size_usd <= 0:
                        analysis_message = "Calculated position size is zero or negative. Cannot enter trade."
                        self.logger.error(analysis_message)
                        success = False
                    else:
                        size_in_crypto_units = position_size_usd / current_price_usd
                        signal = {"action": "buy", "size": size_in_crypto_units, "price": current_price_usd, "type": "long_entry"}
                        self.current_position = {
                            'entry_price': current_price_usd,
                            'size': size_in_crypto_units,
                            'entry_time': datetime.datetime.now()
                        }
                        self.trade_history.append({"type": "entry", "action": "buy", "price": current_price_usd, "size": size_in_crypto_units, "timestamp": datetime.datetime.now().isoformat()})
                        analysis_message = f"Entering long position at {current_price_usd:.2f} USD. Size: {size_in_crypto_units:.4f} units. Reason: {'; '.join(entry_reason)}"
                        self.logger.info(analysis_message)
                        confidence = 0.9
                else:
                    analysis_message = f"Conditions not met for long entry. RSI: {rsi_14:.2f}, Volume: {volume_24h:.2f}. Reasons: {'; '.join(entry_reason) if entry_reason else 'None'}"
                    self.logger.info(analysis_message)
            
            # --- Check if target profit is met ---
            if self.profit_usd_achieved >= self.target_profit_usd:
                if self.current_position:
                    # Close any open position to secure profit
                    signal = {"action": "sell", "size": self.current_position['size'], "price": current_price_usd, "type": "target_profit_reached_exit"}
                    profit_usd = (current_price_usd - self.current_position['entry_price']) * self.current_position['size']
                    self.profit_usd_achieved += profit_usd
                    self.trade_history.append({"type": "exit", "action": "sell", "price": current_price_usd, "size": self.current_position['size'], "profit_usd": profit_usd, "timestamp": datetime.datetime.now().isoformat()})
                    self.current_position = None
                    analysis_message = f"Target profit of {self.target_profit_usd:.2f} USD reached! Exiting all positions. Final profit: {self.profit_usd_achieved:.2f} USD."
                    self.logger.info(analysis_message)
                    confidence = 1.0
                else:
                    analysis_message = f"Target profit of {self.target_profit_usd:.2f} USD reached! No active positions. Total profit: {self.profit_usd_achieved:.2f} USD."
                    self.logger.info(analysis_message)
                    confidence = 1.0
                    success = False # No further trading actions needed for this goal

            return {
                "signal": signal,
                "analysis": analysis_message,
                "confidence": confidence,
                "success": success,
                "current_profit_usd": self.profit_usd_achieved,
                "target_profit_usd": self.target_profit_usd,
                "current_position": self.current_position
            }

        except Exception as e:
            self.logger.exception(f"Error during strategy execution: {e}")
            return {
                "signal": None,
                "analysis": f"Error: {str(e)}",
                "confidence": 0.0,
                "success": False
            }
            
    def validate_input(self, data: dict) -> bool:
        """
        Validates the input data structure.
        Ensures 'real_time_crypto_prices', 'technical_indicators', and 'smart_money_indicators' are present.
        """
        if not isinstance(data, dict):
            self.logger.error("Input data is not a dictionary.")
            return False
        
        required_top_level_keys = ["real_time_crypto_prices", "technical_indicators", "smart_money_indicators"]
        for key in required_top_level_keys:
            if key not in data or not isinstance(data[key], dict):
                self.logger.error(f"Missing or invalid top-level key: '{key}' in input data.")
                return False

        # Validate specific data points within the nested dictionaries
        if 'price_usd' not in data['real_time_crypto_prices'] or not isinstance(data['real_time_crypto_prices']['price_usd'], (int, float)):
            self.logger.error("Missing or invalid 'price_usd' in 'real_time_crypto_prices'.")
            return False
        
        if 'rsi_14' not in data['technical_indicators'] or not isinstance(data['technical_indicators']['rsi_14'], (int, float)):
            self.logger.error("Missing or invalid 'rsi_14' in 'technical_indicators'.")
            return False
            
        if 'volume_24h' not in data['technical_indicators'] or not isinstance(data['technical_indicators']['volume_24h'], (int, float)):
            self.logger.error("Missing or invalid 'volume_24h' in 'technical_indicators'.")
            return False

        if 'liquidation_clusters' not in data['smart_money_indicators'] or not isinstance(data['smart_money_indicators']['liquidation_clusters'], list):
            self.logger.error("Missing or invalid 'liquidation_clusters' in 'smart_money_indicators'.")
            return False
        
        for cluster in data['smart_money_indicators']['liquidation_clusters']:
            if not isinstance(cluster, dict) or 'price' not in cluster or 'amount_usd' not in cluster or \
               not isinstance(cluster['price'], (int, float)) or not isinstance(cluster['amount_usd'], (int, float)):
                self.logger.error("Invalid format for a liquidation cluster entry.")
                return False