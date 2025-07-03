# main.py

from data_loader import DataLoader
from backtester import Backtester
from strategy import Strategy
# import matplotlib.pyplot as plt # <- Убираем Matplotlib
import plotly.graph_objects as go # <- Добавляем Plotly
from plotly.subplots import make_subplots
import pandas as pd 
import datetime 
#from IPython.display import display # Для красивого вывода DataFrame в некоторых средах, опционально

def main():
    print("Starting Backtesting Application...")

    # --- 0. User Input for Parameters ---
    exchange_id = 'bybit' 
    symbol = input("Enter trading symbol (e.g., BTC/USDT): ")
    timeframe = input("Enter TF (1m, 5m, 1h, 4h, 1d): ")

    while True:
        start_date_str = input("Add start date (YYYY-MM-DD): ")
        try:
            datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            break
        except ValueError:
            print("Invalid start date format. Please use YYYY-MM-DD.")
    
    while True:
        end_date_str = input("Add end date (YYYY-MM-DD): ")
        try:
            datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
            if datetime.datetime.strptime(end_date_str, "%Y-%m-%d") < datetime.datetime.strptime(start_date_str, "%Y-%m-%d"):
                print("End date cannot be before start date. Please re-enter.")
            else:
                break
        except ValueError:
            print("Invalid end date format. Please use YYYY-MM-DD.")

    while True:
        try:
            initial_balance = float(input("Enter initial balance (e.g., 10000): "))
            if initial_balance <= 0:
                print("Initial balance must be positive.")
            else:
                break
        except ValueError:
            print("Invalid balance. Please enter a number.")
            
    while True:
        try:
            trade_entry_percent = float(input("Enter percentage of balance to use for each trade (e.g., 10 for 10%): ")) / 100
            if not (0.01 <= trade_entry_percent <= 1.0): 
                print("Trade entry percentage must be between 1 and 100.")
            else:
                break
        except ValueError:
            print("Invalid percentage. Please enter a number.")


    # --- 1. Data Loading ---
    data_loader = DataLoader(
        exchange_id=exchange_id, 
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date_str, 
        end_date=end_date_str      
    )
    df = data_loader.load_data()

    if df is None or df.empty:
        print("Failed to load data or data is empty. Exiting.")
        return

    print(f"Data loaded successfully. Number of candles: {len(df)}")

    # --- 2. Backtester Initialization ---
    transaction_fee = 0.00075 
    backtester = Backtester(df, initial_balance=initial_balance, fee=transaction_fee) 

    # --- 3. Strategy Initialization ---
    strategy = Strategy(trade_entry_percent=trade_entry_percent) 

    # --- 4. Run Backtest ---
    backtester.run_backtest(strategy)

    # --- 5. Enhanced Visualization with Plotly and Results Table ---

    if backtester.equity_log:
        equity_df = pd.DataFrame(backtester.equity_log)
        equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp']) 
        equity_df.set_index('timestamp', inplace=True)

        # Prepare for plotting trades on the chart
        buy_long_signals = [t for t in backtester.trade_log if t['type'] == 'BUY_LONG']
        close_long_signals = [t for t in backtester.trade_log if t['type'] == 'CLOSE_LONG']
        sell_short_signals = [t for t in backtester.trade_log if t['type'] == 'SELL_SHORT']
        close_short_signals = [t for t in backtester.trade_log if t['type'] == 'CLOSE_SHORT']

        # Create Plotly figure with subplots (candles and equity)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # Subplot 1: Candlestick Chart (OHLCV data)
        fig.add_trace(go.Candlestick(x=df.index,
                                     open=df['open'],
                                     high=df['high'],
                                     low=df['low'],
                                     close=df['close'],
                                     name='Candles'), row=1, col=1)

        # Add trade markers on the candlestick chart
        if buy_long_signals:
            fig.add_trace(go.Scatter(x=[t['timestamp'] for t in buy_long_signals],
                                     y=[t['price'] for t in buy_long_signals],
                                     mode='markers',
                                     marker=dict(symbol='triangle-up', size=10, color='green'),
                                     name='Buy Long'), row=1, col=1)
        if close_long_signals:
            fig.add_trace(go.Scatter(x=[t['timestamp'] for t in close_long_signals],
                                     y=[t['price'] for t in close_long_signals],
                                     mode='markers',
                                     marker=dict(symbol='triangle-down', size=10, color='red'),
                                     name='Close Long'), row=1, col=1)
        if sell_short_signals:
            fig.add_trace(go.Scatter(x=[t['timestamp'] for t in sell_short_signals],
                                     y=[t['price'] for t in sell_short_signals],
                                     mode='markers',
                                     marker=dict(symbol='triangle-down', size=10, color='purple'),
                                     name='Sell Short'), row=1, col=1)
        if close_short_signals:
            fig.add_trace(go.Scatter(x=[t['timestamp'] for t in close_short_signals],
                                     y=[t['price'] for t in close_short_signals],
                                     mode='markers',
                                     marker=dict(symbol='triangle-up', size=10, color='orange'),
                                     name='Close Short'), row=1, col=1)

        # --- CORRECTED LINE FOR Candlestick Chart Update ---
        fig.update_xaxes(rangeslider_visible=False, row=1, col=1) # Apply rangeslider to specific X axis
        fig.update_yaxes(title_text='Price (USDT)', row=1, col=1) # Apply Y axis title to specific Y axis


        # Subplot 2: Equity Curve
        fig.add_trace(go.Scatter(x=equity_df.index, y=equity_df['equity'], 
                                 mode='lines', name='Equity Curve', line=dict(color='blue')), row=2, col=1)
        
        fig.update_yaxes(title_text='Equity (USDT)', row=2, col=1)
        fig.update_xaxes(title_text='Date', row=2, col=1)

        # --- CORRECTED LINE FOR OVERALL LAYOUT TITLE ---
        fig.update_layout(title_text=f'Backtest Results for {symbol} - {timeframe} (Equity Curve & Trades)',
                          height=800, showlegend=True, hovermode='x unified') # Title for the entire figure, no row/col here!
        
        fig.show()

    else:
        print("Equity log is empty. Cannot plot equity curve.")

    # --- 6. Display Performance Metrics Table ---
    print("\n--- Performance Metrics ---")
    
    final_equity = backtester.current_balance
    last_price = df['close'].iloc[-1] if not df.empty else 0
    if backtester.position != 0: 
        final_equity += backtester.position * last_price
    
    total_pnl = final_equity - backtester.initial_balance
    pnl_percent = (total_pnl / backtester.initial_balance) * 100 if backtester.initial_balance > 0 else 0

    closed_pnl = sum([t['pnl_usdt'] for t in backtester.trade_log if t['type'] in ['CLOSE_LONG', 'CLOSE_SHORT']])
    
    total_trades = len([t for t in backtester.trade_log if t['type'] in ['BUY_LONG', 'SELL_SHORT']])
    winning_trades = sum(1 for t in backtester.trade_log if t['type'] in ['CLOSE_LONG', 'CLOSE_SHORT'] and t['pnl_usdt'] > 0)
    losing_trades = sum(1 for t in backtester.trade_log if t['type'] in ['CLOSE_LONG', 'CLOSE_SHORT'] and t['pnl_usdt'] < 0)

    # Prevent ZeroDivisionError for win_rate if no trades
    win_rate = (winning_trades / (winning_trades + losing_trades)) * 100 if (winning_trades + losing_trades) > 0 else 0

    metrics_data = {
        'Metric': [
            'Initial Balance', 
            'Final Equity', 
            'Total P&L (USDT)', 
            'Total P&L (%)', 
            'Closed P&L (USDT)',
            'Total Trades Opened',
            'Winning Trades',
            'Losing Trades',
            'Win Rate (%)'
        ],
        'Value': [
            f'{backtester.initial_balance:.2f}', 
            f'{final_equity:.2f}', 
            f'{total_pnl:.2f}', 
            f'{pnl_percent:.2f}',
            f'{closed_pnl:.2f}',
            total_trades,
            winning_trades,
            losing_trades,
            f'{win_rate:.2f}'
        ]
    }
    metrics_df = pd.DataFrame(metrics_data)
    print(metrics_df.to_string(index=False)) # Use to_string for better console output

    # Alternatively, for Jupyter/IPython:
    # display(metrics_df)

if __name__ == "__main__":
    main()