# 📈 Crypto Backtester Engine

This project provides a simple yet functional backtesting engine for cryptocurrency trading strategies. It allows you to load historical data from various exchanges via `ccxt`, apply custom trading strategies, and visualize the results using `Plotly`.

---

## ✨ Features

* **Flexible Data Loading:** Fetch OHLCV data from popular cryptocurrency exchanges (e.g., Bybit, Binance) for various trading pairs and timeframes.
* **Customizable Strategy:** A straightforward structure to define and test your own trading strategies.
* **Detailed Backtesting:** Simulates trading operations, accounting for transaction fees, tracking balance, and open positions.
* **Results Visualization:** Interactive candlestick charts with trade markers and an equity curve, powered by `Plotly`.
* **Performance Metrics Report:** A summary table of key strategy performance indicators (P&L, win rate, etc.).

---

## 🚀 Getting Started

Follow these instructions to get the project up and running on your local machine.

### 📋 Prerequisites

Ensure you have Python 3.x installed.

Then, install the necessary libraries:

```bash
pip install pandas ccxt plotly
```

### 📦 Project Structure

```
backtester_engine/
├── data_loader.py      # Module for fetching historical data from exchanges.
├── backtester.py       # Core backtesting engine, handles trade logic.
├── strategy.py         # Example trading strategy (can be modified or extended).
└── main.py             # Entry point for the application, runs backtest and visualization.
```

### ⚙️ How to Run

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Xyxl1kalgo/Backtester-engine.git
    ```

2.  **Navigate into the project directory:**

    ```bash
    cd backtester_engine
    ```

3.  **Run the main application:**

    ```bash
    python main.py
    ```

4.  **Follow the prompts in the terminal:**
    The program will ask you for the following parameters:
    * **Trading Symbol:** E.g., `BTC/USDT`
    * **Timeframe:** E.g., `1h`, `4h`, `1d`
    * **Start Date:** In `YYYY-MM-DD` format
    * **End Date:** In `YYYY-MM-DD` format
    * **Initial Balance:** E.g., `10000`
    * **Percentage of balance to use for each trade:** E.g., `10` (for 10%)

After entering all the details, the engine will load the data, run the backtest, and display an interactive Plotly chart in your browser, as well as print performance metrics to the terminal.

---

## 📝 Strategy Customization

Your trading logic is defined within the `strategy.py` file.

* **`Strategy` class:** Contains the `on_candle` method, which is called for each new candle in the historical data.
* **`on_candle(self, timestamp, open_price, high_price, low_price, close_price, volume)`:**
    * Implement your trading logic here.
    * You can get the current position type using `self.backtester.get_position_type()`.
    * Call trading operations:
        * `self.backtester.open_long(timestamp, price, amount_usdt_percent)`
        * `self.backtester.close_long(timestamp, price)`
        * `self.backtester.open_short(timestamp, price, amount_usdt_percent)`
        * `self.backtester.close_short(timestamp, price)`

**Example (from current implementation):**
A simple strategy that opens a long position on a bullish candle and a short position on a bearish candle, closing any existing position first.

```python
# strategy.py (example)
class Strategy:
    def __init__(self, trade_entry_percent: float = 0.1):
        self.backtester = None
        self.trade_entry_percent = trade_entry_percent

    def on_candle(self, timestamp, open_price, high_price, low_price, close_price, volume):
        position_type = self.backtester.get_position_type()

        if position_type == 'NONE':
            if close_price > open_price: # Bullish candle
                self.backtester.open_long(timestamp, close_price, amount_usdt_percent=self.trade_entry_percent)
            elif close_price < open_price: # Bearish candle
                self.backtester.open_short(timestamp, close_price, amount_usdt_percent=self.trade_entry_percent)
        elif position_type == 'LONG':
            if close_price < open_price: # Bearish candle, close long
                self.backtester.close_long(timestamp, close_price)
        elif position_type == 'SHORT':
            if close_price > open_price: # Bullish candle, close short
                self.backtester.close_short(timestamp, close_price)
```

---

## 📊 Backtest Results

Upon completion of the backtest, you will see the results presented in two ways:

1.  **Interactive Plotly Chart (in your browser):**
    * **Top Panel:** Candlestick chart of the selected asset with markers indicating trade entry and exit points.
    * **Bottom Panel:** Equity curve showing the change in your balance throughout the backtesting period.
    <!-- You can add an image here later, e.g., ![Plotly Chart Example](https://placehold.co/600x300/EFEFEF/AAAAAA?text=Plotly+Chart+Example) -->
2.  **Performance Metrics Table (in the terminal):**
    A summary table will be printed directly in your terminal, including key performance indicators like initial/final balance, total P&L (profit and loss), number of trades, win rate, and more.

---

## 🤝 Contributing

Contributions are welcome! If you have ideas for improvements, new features, or find a bug, please feel free to open an [Issue](https://github.com/Xyxl1kalgo/Backtester-engine/issues) or submit a [Pull Request](https://github.com/Xyxl1kalgo/Backtester-engine/pulls).

---

## 📞 Contact

If you have any questions, you can reach the author via GitHub.
