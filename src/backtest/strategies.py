import numpy as np
import talib
from backtesting import Strategy
from backtesting.lib import crossover


class SupportResistance(Strategy):
    _window = 50
    _risk_reward_ratio = 2

    def init(self):
        self.support = self.I(lambda x: x.rolling(self._window).min(), self.data.Low)
        self.resistance = self.I(lambda x: x.rolling(self._window).max(), self.data.High)

    def next(self):
        # Buy Signal: Price breaks above resistance
        if self.data.Close[-1] > self.resistance[-1]:
            stop_loss = self.support[-1]
            take_profit = self.data.Close[-1] + self._risk_reward_ratio * (self.data.Close[-1] - stop_loss)
            self.buy(sl=stop_loss, tp=take_profit)

        # Sell Signal: Price breaks below support
        elif self.data.Close[-1] < self.support[-1]:
            stop_loss = self.resistance[-1]
            take_profit = self.data.Close[-1] - self._risk_reward_ratio * (stop_loss - self.data.Close[-1])
            self.sell(sl=stop_loss, tp=take_profit)


class RsiOscillator(Strategy):
    """
       A trading strategy based on the Relative Strength Index (RSI) Oscillator.

       The strategy involves taking long and short positions based on RSI trends:
       - A buy signal is generated when the RSI crosses above its lower bound.
       - A sell signal is generated when the RSI crosses below its upper bound.

       The trader can configure risk management parameters such as:
       - `trade_risk_pct`: Percentage of account equity to risk on each trade.
       - `sl_pct`: Stop-loss as a percentage of the entry price.
       - `tp_pct`: Take-profit as a percentage of the entry price.

       Key Attributes:
       - `upper_bound`: The RSI value above which the market is considered overbought.
       - `lower_bound`: The RSI value below which the market is considered oversold.
       - `rsi_window`: The window (number of periods) used to calculate the RSI.

       Methods:
       - `init()`: Initializes the RSI indicator and the upper and lower boundaries.
       - `next()`: Evaluates conditions for buy or sell signals on each new data point,
         calculates stop-loss (SL), take-profit (TP), and position size, and executes trades.

       Risk Management:
       - Trades are limited to a fixed percentage of account equity (`trade_risk_pct`).
       - Stop-loss (SL) and take-profit (TP) levels are dynamically calculated.
       - Position size is computed based on the risk per unit.

       Example Usage:
       Suitable in trending or oscillating markets to identify overbought or oversold conditions
       for entry and exit points.
       """
    # Rsi-specific parameters
    upper_bound = 75
    lower_bound = 20
    rsi_window = 10

    # Risk-management parameters
    risk_per_trade_pct = 2  # Percentage of the account to risk (2%)
    sl_pct = 0.1  # Stop loss in percentage
    tp_pct = 0.1  # Take profit in percentage

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        self.rsi = None
        self.upper_rsi = None
        self.lower_rsi = None

    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)
        self.upper_rsi = np.full_like(self.rsi, self.upper_bound)
        self.lower_rsi = np.full_like(self.rsi, self.lower_bound)

    def next(self):
        price = float(self.data.Close[-1])

        if crossover(self.rsi, self.lower_rsi):
            # Compute stop-loss and take-profit prices
            sl_price = price - self.sl_pct / 100.0 * price
            tp_price = price + self.tp_pct / 100.0 * price

            # Compute position size
            risk_amount = self.equity * (self.risk_per_trade_pct / 100.0)
            risk_per_unit = (price - sl_price) / price
            position_size = round(risk_amount / risk_per_unit / 100_000)

            self.buy(size=position_size, sl=sl_price, tp=tp_price)

        if crossover(self.upper_rsi, self.rsi):
            # Compute stop-loss and take-profit prices
            sl_price = price + self.sl_pct / 100.0 * price
            tp_price = price - self.tp_pct / 100.0 * price

            # Compute position size
            risk_amount = self.equity * (self.risk_per_trade_pct / 100.0)
            risk_per_unit = (sl_price - price) / price
            position_size = round(risk_amount / risk_per_unit / 100_000)

            self.sell(size=position_size, sl=sl_price, tp=tp_price)
