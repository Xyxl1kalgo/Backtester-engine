# strategy.py

import pandas as pd

class Strategy:
    def __init__(self, trade_entry_percent: float = 0.1): # Добавили параметр
        """
        Initializes the base trading strategy.
        :param trade_entry_percent: Percentage of balance to use for opening new trades (0.0 to 1.0).
        """
        self.backtester = None 
        self.trade_entry_percent = trade_entry_percent # Сохраняем его
        print(f"Base Strategy initialized with {trade_entry_percent*100:.2f}% trade entry size.")

    def set_backtester(self, backtester_instance):
        """
        Sets the reference to the Backtester object for interaction.
        """
        self.backtester = backtester_instance
        print("Strategy received Backtester reference.")

    def on_candle(self, timestamp, open_price, high_price, low_price, close_price, volume):
        """
        This method is called by the Backtester for each new candle.
        The trading logic of your strategy should be implemented here.
        """
        position_type = self.backtester.get_position_type()
        
        # Scenario 1: No open position
        if position_type == 'NONE':
            if close_price > open_price: # Bullish candle
                # Используем self.trade_entry_percent
                self.backtester.open_long(timestamp, close_price, amount_usdt_percent=self.trade_entry_percent) 
            elif close_price < open_price: # Bearish candle
                # Используем self.trade_entry_percent
                self.backtester.open_short(timestamp, close_price, amount_usdt_percent=self.trade_entry_percent) 
        
        # Scenario 2: In a LONG position
        elif position_type == 'LONG':
            if close_price < open_price: # Bearish candle, close long
                self.backtester.close_long(timestamp, close_price)
        
        # Scenario 3: In a SHORT position
        elif position_type == 'SHORT':
            if close_price > open_price: # Bullish candle, close short
                self.backtester.close_short(timestamp, close_price)