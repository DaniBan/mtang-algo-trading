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
    upper_bound = 75
    lower_bound = 20
    rsi_window = 10

    # Risk-management parameters
    trade_risk_pct = 2  # Percentage of the account to risk (2%)
    sl_pct = 0.4  # Stop loss in percentage (0.4%)
    tp_pct = 0.4  # Take profit in percentage (0.4%)

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
            sl_price = price - self.sl_pct / 100 * price
            tp_price = price + self.tp_pct / 100 * price

            # Compute position size
            risk_amount = self.equity * (self.trade_risk_pct / 100)
            risk_per_unit = (price - sl_price) / price
            position_size = risk_amount / risk_per_unit / 100_000

            self.buy(size=position_size, sl=sl_price, tp=tp_price)

        if crossover(self.upper_rsi, self.rsi):
            # Compute stop-loss and take-profit prices
            sl_price = price + self.sl_pct / 100 * price
            tp_price = price - self.tp_pct / 100 * price

            # Compute position size
            risk_amount = self.equity * (self.trade_risk_pct / 100)
            risk_per_unit = (sl_price - price) / price
            position_size = risk_amount / risk_per_unit / 100_000

            self.sell(size=position_size, sl=sl_price, tp=tp_price)
