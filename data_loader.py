# data_loader.py

import pandas as pd
import ccxt
import datetime
import time 

class DataLoader:
    def __init__(self, exchange_id: str = 'bybit', symbol: str = 'BTC/USDT', timeframe: str = '1h', 
                 start_date: str = None, end_date: str = None, since_days: int = None):
        """
        Initializes the DataLoader to fetch OHLCV data from a cryptocurrency exchange.

        :param exchange_id: ID of the exchange (e.g., 'bybit', 'binance').
        :param symbol: Trading pair symbol (e.g., 'BTC/USDT').
        :param timeframe: Candlestick timeframe (e.g., '1m', '5m', '1h', '4h', '1d').
        :param start_date: Start date for data loading in 'YYYY-MM-DD' format. If None, uses since_days.
        :param end_date: End date for data loading in 'YYYY-MM-DD' format. If None, uses current date.
        :param since_days: Number of days back from today to load data. Used if start_date is None.
        """
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date_str = start_date
        self.end_date_str = end_date
        self.since_days = since_days

        try:
            self.exchange = getattr(ccxt, self.exchange_id)()
        except AttributeError:
            raise ValueError(f"Exchange '{self.exchange_id}' not found or not supported by ccxt.")
        
        # Check if symbol is supported
        self.exchange.load_markets()
        if self.symbol not in self.exchange.symbols:
            raise ValueError(f"Symbol '{self.symbol}' not supported on {self.exchange_id}.")
        
        # Check if timeframe is supported
        if self.timeframe not in self.exchange.timeframes:
            raise ValueError(f"Timeframe '{self.timeframe}' not supported on {self.exchange_id}.")

        print(f"DataLoader initialized for {self.symbol} on {self.exchange_id}.")


    def load_data(self) -> pd.DataFrame:
        """
        Loads historical OHLCV data based on the DataLoader's configuration.

        :return: A pandas DataFrame with OHLCV data, indexed by timestamp.
                 Returns an empty DataFrame or None if data loading fails.
        """
        all_ohlcv_data = []
        limit_per_request = 1000 # Max candles per request for most exchanges

        # Determine start and end timestamps
        if self.start_date_str:
            start_date_dt = datetime.datetime.strptime(self.start_date_str, "%Y-%m-%d")
        elif self.since_days is not None:
            start_date_dt = datetime.datetime.utcnow() - datetime.timedelta(days=self.since_days)
        else:
            raise ValueError("Either 'start_date' or 'since_days' must be provided for data loading.")

        start_date_ms = int(start_date_dt.timestamp() * 1000)

        if self.end_date_str:
            end_date_dt = datetime.datetime.strptime(self.end_date_str, "%Y-%m-%d")
            # Adjust end_date_ms to include the entire end day
            end_date_ms = int((end_date_dt + datetime.timedelta(days=1)).timestamp() * 1000) - 1
        else:
            end_date_ms = int(datetime.datetime.utcnow().timestamp() * 1000) # Load up to current time if no end date

        current_since = start_date_ms

        print(f"Loading... {self.symbol} from {datetime.datetime.fromtimestamp(start_date_ms/1000).strftime('%Y-%m-%d')} till {datetime.datetime.fromtimestamp(end_date_ms/1000).strftime('%Y-%m-%d')} ({self.timeframe} TF)...")

        while True:
            try:
                # Fetch data batch from current_since
                ohlcv_batch = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=current_since, limit=limit_per_request)

                if not ohlcv_batch:
                    break

                # Filter out data that is beyond the end_date_ms immediately
                filtered_batch = [candle for candle in ohlcv_batch if candle[0] <= end_date_ms]
                all_ohlcv_data.extend(filtered_batch)

                # Update current_since for the next request
                # It's the timestamp of the last candle + 1 ms to avoid duplicates
                current_since = ohlcv_batch[-1][0] + 1 

                if current_since > end_date_ms:
                    break

                time.sleep(self.exchange.rateLimit / 1000 + 0.1) # Respect exchange rate limits + small buffer

            except ccxt.RateLimitExceeded:
                print("Rate limit exceeded. Waiting 5 seconds...")
                time.sleep(5)
            except Exception as e:
                print(f"Error fetching data: {e}")
                return pd.DataFrame() # Return empty DataFrame on error

        if not all_ohlcv_data:
            print("No data loaded. Check parameters or try a different date range/timeframe.")
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Remove duplicates based on timestamp (can happen with multiple requests)
        df.drop_duplicates(subset=['timestamp'], inplace=True)

        # Convert timestamp to datetime objects and set as index
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # Filter the DataFrame to ensure it's within the exact requested date range
        # This handles cases where fetch_ohlcv might return slightly outside the strict range
        df = df.loc[(df.index >= start_date_dt) & (df.index <= end_date_dt + datetime.timedelta(days=1, seconds=-1))] # Adjust to include end of end_date_dt

        print(f"Loaded {len(df)} candles.")
        print(f"\nTotal candles in DataFrame: {len(df)}")
        return df
    
    