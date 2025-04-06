from backtesting import Strategy
from backtesting.lib import crossover

import talib
import pandas as pd


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
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)

    def next(self):
        if crossover(self.rsi, self.upper_bound):
            self.position.close()
        elif crossover(self.lower_bound, self.rsi):
            self.buy()
