# backtester.py

import pandas as pd

class Backtester:
    def __init__(self, data: pd.DataFrame, initial_balance: float = 10000.0, fee: float = 0.00075):
        """
        Initializes the backtesting engine with support for long and short positions.

        :param data: Historical OHLCV data in pandas DataFrame format.
                     Expected DataFrame index is DatetimeIndex,
                     and columns are: 'open', 'high', 'low', 'close', 'volume'.
        :param initial_balance: Starting balance in USDT.
        :param fee: Transaction fee (e.g., 0.00075 for Bybit Spot Taker Fee).
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data for Backtester must be a pandas DataFrame.")
        if not isinstance(data.index, pd.DatetimeIndex):
            raise TypeError("DataFrame index must be a DatetimeIndex (date/time).")
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {', '.join(required_cols)}")
        
        self.data = data.copy()
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.fee = fee

        # self.position can now be > 0 (long), < 0 (short), or 0 (no position)
        self.position = 0.0 
        self.entry_price = 0.0 # Entry price of the current open position

        self.trade_log = []   # Log of all executed trades
        self.equity_log = []  # Log of overall capital changes (equity curve)

        print(f"Backtester initialized:")
        print(f"  Start balance: {self.initial_balance:.2f} USDT")
        print(f"  Fees: {self.fee * 100:.3f}%")
        print(f"  Loaded {len(self.data)} candles.")

    # --- Private methods for executing orders ---
    def _execute_order(self, order_type: str, price: float, timestamp, amount_usdt_percent: float = 1.0):
        """
        Private universal method for executing orders (buy/sell/close).
        Handles the logic for both long and short positions.

        :param order_type: Type of order ('BUY_LONG', 'SELL_SHORT', 'CLOSE_LONG', 'CLOSE_SHORT').
        :param price: Price at which the order is executed.
        :param timestamp: Timestamp of the current candle.
        :param amount_usdt_percent: Percentage of self.current_balance to use for opening a new position (only for opening).
                                    Used as 1.0 (100%) when closing a position.
        """
        MIN_ORDER_USDT = 5.0 # Minimum order size on Bybit Spot for BTC/USDT (example)

        # --- Long position opening/closing logic ---
        if order_type == 'BUY_LONG': # Opening a long position
            if self.position > 0: # Already in a long position
                # print(f"[{timestamp}] Error: Already in a long position ({self.position:.6f} BTC). Cannot open a new long.") # Can uncomment for more verbose logs
                return False
            if self.position < 0: # In a short position
                print(f"[{timestamp}] Error: In a short position ({self.position:.6f} BTC). Close short first or use 'CLOSE_SHORT'.")
                return False
            if self.current_balance <= 0:
                print(f"[{timestamp}] Error: Insufficient balance to buy (balance: {self.current_balance:.2f} USDT).")
                return False
            if not (0.0 < amount_usdt_percent <= 1.0):
                print(f"[{timestamp}] Error: 'amount_usdt_percent' must be between 0.0 and 1.0 (received: {amount_usdt_percent}).")
                return False
            
            usdt_to_spend = self.current_balance * amount_usdt_percent
            if usdt_to_spend < MIN_ORDER_USDT:
                # print(f"[{timestamp}] Error: Calculated amount for purchase ({usdt_to_spend:.2f} USDT) is too small. Min: {MIN_ORDER_USDT} USDT.") # Can uncomment
                return False

            amount_coins = (usdt_to_spend / price) * (1 - self.fee)
            cost_usdt = usdt_to_spend # The entire amount we decided to spend

            self.current_balance -= cost_usdt
            self.position = amount_coins
            self.entry_price = price
            
            trade_info = {
                'timestamp': timestamp, 'type': 'BUY_LONG', 'price': price,
                'amount_coins': amount_coins, 'cost_usdt': cost_usdt,
                'balance_after_trade': self.current_balance, 'current_position': self.position,
                'pnl_usdt': 0.0 # No PnL on opening
            }
            print(f"[{timestamp}] LONG OPENED: {amount_coins:.6f} BTC at {price:.2f} USDT. Spent: {cost_usdt:.2f} USDT ({amount_usdt_percent*100:.2f}%). Balance: {self.current_balance:.2f} USDT. Position: {self.position:.6f} BTC")

        elif order_type == 'CLOSE_LONG': # Closing a long position
            if self.position <= 0:
                print(f"[{timestamp}] Error: No open long position to close.")
                return False

            gross_revenue_usdt = self.position * price
            net_revenue_usdt = gross_revenue_usdt * (1 - self.fee)
            
            initial_position_cost_usdt = self.position * self.entry_price
            profit_loss = net_revenue_usdt - initial_position_cost_usdt

            self.current_balance += net_revenue_usdt
            self.position = 0.0 # Close position
            self.entry_price = 0.0 # Reset entry price

            trade_info = {
                'timestamp': timestamp, 'type': 'CLOSE_LONG', 'price': price,
                'amount_coins': 0.0, 'revenue_usdt': net_revenue_usdt,
                'balance_after_trade': self.current_balance, 'current_position': self.position,
                'pnl_usdt': profit_loss
            }
            print(f"[{timestamp}] LONG CLOSED: Realized {net_revenue_usdt:.2f} USDT. PnL: {profit_loss:.2f} USDT. Balance: {self.current_balance:.2f} USDT.")

        # --- Short position opening/closing logic ---
        elif order_type == 'SELL_SHORT': # Opening a short position
            if self.position < 0: # Already in a short position
                print(f"[{timestamp}] Error: Already in a short position ({self.position:.6f} BTC). Cannot open a new short.")
                return False
            if self.position > 0: # In a long position
                print(f"[{timestamp}] Error: In a long position ({self.position:.6f} BTC). Close long first or use 'CLOSE_LONG'.")
                return False
            
            # For short, we sell an asset we don't own (borrow it)
            # For simplicity, we use usdt_to_short_equivalent
            # In real life, margin and leverage are needed here.
            if not (0.0 < amount_usdt_percent <= 1.0):
                print(f"[{timestamp}] Error: 'amount_usdt_percent' must be between 0.0 and 1.0 (received: {amount_usdt_percent}).")
                return False

            # USDT equivalent amount to open a short (measure short size in USDT)
            usdt_to_short_equivalent = self.current_balance * amount_usdt_percent 

            if usdt_to_short_equivalent < MIN_ORDER_USDT:
                print(f"[{timestamp}] Error: Calculated amount for short ({usdt_to_short_equivalent:.2f} USDT) is too small. Min: {MIN_ORDER_USDT} USDT.")
                return False
            
            # Amount of coins we "short sell" (with a negative sign)
            amount_coins_short = (usdt_to_short_equivalent / price) * (1 - self.fee)
            
            # Add received funds from selling to balance
            self.current_balance += usdt_to_short_equivalent * (1 - self.fee) # Receive USDT from selling
            self.position = -amount_coins_short # Record position as negative
            self.entry_price = price # Price at which short was opened

            trade_info = {
                'timestamp': timestamp, 'type': 'SELL_SHORT', 'price': price,
                'amount_coins': -amount_coins_short, 'revenue_usdt': usdt_to_short_equivalent * (1 - self.fee),
                'balance_after_trade': self.current_balance, 'current_position': self.position,
                'pnl_usdt': 0.0 # No PnL on opening
            }
            print(f"[{timestamp}] SHORT OPENED: Sold {amount_coins_short:.6f} BTC at {price:.2f} USDT. Received: {usdt_to_short_equivalent * (1 - self.fee):.2f} USDT ({amount_usdt_percent*100:.2f}%). Balance: {self.current_balance:.2f} USDT. Position: {self.position:.6f} BTC")

        elif order_type == 'CLOSE_SHORT': # Closing a short position (buy back)
            if self.position >= 0: # No open short position
                print(f"[{timestamp}] Error: No open short position to close.")
                return False
            
            # Amount of coins to buy back to close the short
            amount_coins_to_buy_back = abs(self.position)
            
            # Cost of buying back
            cost_to_buy_back = (amount_coins_to_buy_back * price) * (1 + self.fee) # Fee is added to the cost of buying back

            # Check if there's enough balance to buy back the short
            if self.current_balance < cost_to_buy_back:
                # In real life, this could lead to liquidation
                print(f"[{timestamp}] CRITICAL ERROR: Insufficient balance to close short! Balance: {self.current_balance:.2f} USDT, Required: {cost_to_buy_back:.2f} USDT. Simulation aborted.")
                # Could add logic for liquidation, but for now, we'll just return False.
                return False

            # PnL for short: (short_open_price - short_close_price) * amount_coins
            # We received USDT when opening the short at self.entry_price
            # We spent USDT when closing the short at price
            # PnL = (revenue_from_short_open) - (cost_for_short_close)
            
            # Value received when opening short
            revenue_from_short_open = abs(self.position) * self.entry_price * (1 - self.fee) 
            # Cost incurred when closing short
            cost_for_short_close = abs(self.position) * price * (1 + self.fee) # When buying to close short, fee is added to expenses

            profit_loss = revenue_from_short_open - cost_for_short_close 

            self.current_balance -= cost_to_buy_back # Deduct buy-back cost from balance
            self.position = 0.0 # Close position
            self.entry_price = 0.0 # Reset entry price

            trade_info = {
                'timestamp': timestamp, 'type': 'CLOSE_SHORT', 'price': price,
                'amount_coins': 0.0, 'cost_usdt': cost_to_buy_back,
                'balance_after_trade': self.current_balance, 'current_position': self.position,
                'pnl_usdt': profit_loss
            }
            print(f"[{timestamp}] SHORT CLOSED: Bought back {amount_coins_to_buy_back:.6f} BTC at {price:.2f} USDT. Spent: {cost_to_buy_back:.2f} USDT. PnL: {profit_loss:.2f} USDT. Balance: {self.current_balance:.2f} USDT.")
        
        else:
            print(f"Unknown order type: {order_type}")
            return False

        # Add trade info to the general log
        self.trade_log.append(trade_info)
        return True

    # --- Public methods for strategy interaction ---
    # The strategy will now call these methods, and they will use the universal _execute_order
    def open_long(self, timestamp, price, amount_usdt_percent: float = 1.0):
        """Opens a long position."""
        return self._execute_order('BUY_LONG', price, timestamp, amount_usdt_percent)

    def close_long(self, timestamp, price):
        """Closes an open long position."""
        return self._execute_order('CLOSE_LONG', price, timestamp)

    def open_short(self, timestamp, price, amount_usdt_percent: float = 1.0):
        """Opens a short position."""
        return self._execute_order('SELL_SHORT', price, timestamp, amount_usdt_percent)

    def close_short(self, timestamp, price):
        """Closes an open short position."""
        return self._execute_order('CLOSE_SHORT', price, timestamp)

    def get_current_position(self) -> float:
        """
        Returns the current volume of the open position.
        Positive value for long, negative for short, 0 for no position.
        """
        return self.position

    def get_current_balance(self) -> float:
        """
        Returns the current available balance (in USDT).
        """
        return self.current_balance
    
    def get_entry_price(self) -> float:
        """
        Returns the entry price of the current open position.
        """
        return self.entry_price

    def get_position_type(self) -> str:
        """
        Returns the type of the current position ('LONG', 'SHORT', 'NONE').
        """
        if self.position > 0:
            return 'LONG'
        elif self.position < 0:
            return 'SHORT'
        else:
            return 'NONE'

    # --- Main method to run the backtest ---
    def run_backtest(self, strategy):
        """
        Main method to run the backtest.
        Iterates through the data, applying the strategy's logic.

        :param strategy: A trading strategy object that must have an 'on_candle' method.
                         The strategy should also have a 'set_backtester' method.
        """
        print("\nStarting backtest...")
        
        # 1. Pass a reference to this Backtester object to the strategy.
        #    The strategy uses this reference to call buy(), sell(), get_*.
        strategy.set_backtester(self) 

        # 2. Iterate through all candles in self.data
        for timestamp, row in self.data.iterrows():
            # Get current candle data
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            volume = row['volume']

            # Call the on_candle method of the strategy, passing it the current candle data.
            # The strategy makes trading decisions based on this data.
            strategy.on_candle(timestamp, open_price, high_price, low_price, close_price, volume)

            # 3. Update equity_log for the current candle.
            #    Equity (capital) is the sum of current balance and the market value of the open position.
            current_equity = self.current_balance
            if self.position != 0: # If there's an open position (long or short)
                current_equity += self.position * close_price # Add/subtract its value (position is negative for short)
            
            self.equity_log.append({'timestamp': timestamp, 'equity': current_equity})

        print("\nBacktest completed.")
        self.display_results()

    def display_results(self):
        """
        Displays the main results of the backtest.
        """
        print("\n--- Backtest Results ---")
        
        final_equity = self.current_balance
        last_price = self.data['close'].iloc[-1]
        
        if self.position != 0: # If there's an open position at the end
            final_equity += self.position * last_price
            print(f"Final equity (including open position value at last price {last_price:.2f} USDT): {final_equity:.2f} USDT")
        else:
            print(f"Final equity: {final_equity:.2f} USDT")

        total_pnl = final_equity - self.initial_balance
        print(f"Total Profit/Loss: {total_pnl:.2f} USDT")
        if self.initial_balance > 0:
            pnl_percent = (total_pnl / self.initial_balance) * 100
            print(f"Percentage P/L: {pnl_percent:.2f}%")

        long_trades = [t for t in self.trade_log if t['type'] in ['BUY_LONG', 'CLOSE_LONG']]
        short_trades = [t for t in self.trade_log if t['type'] in ['SELL_SHORT', 'CLOSE_SHORT']]
        
        print(f"\nTotal trades executed (open/close orders): {len(self.trade_log)}")
        print(f"  Long trades (open): {len([t for t in self.trade_log if t['type'] == 'BUY_LONG'])}")
        print(f"  Short trades (open): {len([t for t in self.trade_log if t['type'] == 'SELL_SHORT'])}")
        
        # Calculate PnL from closed trades
        closed_pnl = sum([t['pnl_usdt'] for t in self.trade_log if t['type'] in ['CLOSE_LONG', 'CLOSE_SHORT']])
        print(f"Total PnL from closed trades: {closed_pnl:.2f} USDT")

        # More metrics like Max Drawdown, Sharpe Ratio etc. can be added later using numpy and matplotlib.