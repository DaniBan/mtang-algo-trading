import numpy as np
import talib
from backtesting import Strategy
import logging

class TrendFollowingEMAADX(Strategy):
	"""
	Trend Following Strategy using 50 & 200 EMA + ADX for confirmation.

	BUY:
		- 50 EMA > 200 EMA (uptrend)
		- ADX(14) > 25 and rising
		- Price pulls back near 50 EMA
		- Bullish engulfing or bullish pin bar at/near 50 EMA
		- SL: Below recent swing low
		- TP: 2:1 risk/reward OR trailing stop under higher lows

	SELL:
		- 50 EMA < 200 EMA (downtrend)
		- ADX(14) > 25 and rising
		- Price pulls back near 50 EMA
		- Bearish engulfing or bearish pin bar at/near 50 EMA
		- SL: Above recent swing high
		- TP: 2:1 risk/reward OR trailing stop above lower highs

	EXIT:
		- Trailing stops under each higher low (up) or above each lower high (down)
		- ADX reversal (ADX falling and price closes beyond 50 EMA in an opposite direction)
	"""
	risk_per_trade_pct = 2  # Risk per trade as % of the account
	ema_fast = 50
	ema_slow = 200
	adx_period = 14
	min_adx = 25
	flat_adx = 20
	reward_risk_ratio = 2.0
	ema_touch_tol = 0.01  # 0.5% within EMA50 == "touch"

	def __init__(self, broker, data, params):
		super().__init__(broker, data, params)
		self.ema_50 = None
		self.ema_200 = None
		self.adx = None

	def init(self):
		self.ema_50 = self.I(talib.EMA, self.data.Close, self.ema_fast)
		self.ema_200 = self.I(talib.EMA, self.data.Close, self.ema_slow)
		self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, self.adx_period)

	def _is_bullish_engulfing(self, i):
		"""Check for bullish engulfing pattern at index i."""
		if i < 1:
			return False
		prev_open = self.data.Open[i - 1]
		prev_close = self.data.Close[i - 1]
		curr_open = self.data.Open[i]
		curr_close = self.data.Close[i]

		# Previous candle bearish, current is bullish, AND the current body engulfs previous
		return curr_close > prev_open > prev_close > curr_open and curr_close > curr_open

	def _is_bullish_pin_bar(self, i):
		"""Check for bullish pin bar at index i."""
		if i < 1:
			return False
		body = abs(self.data.Close[i] - self.data.Open[i])
		lower_wick = min(self.data.Open[i], self.data.Close[i]) - self.data.Low[i]
		candle_range = self.data.High[i] - self.data.Low[i]

		# Pin bar: small body, long lower wick, closes in upper half
		return (
				body < (0.33 * candle_range)
				and lower_wick > (0.5 * candle_range)
				and self.data.Close[i] > self.data.Open[i]
				and self.data.Close[i] > (self.data.Low[i] + 0.66 * candle_range)
		)

	def _recent_swing_low(self, i, lookback=10):
		"""Finds the recent swing low for stop loss."""
		return float(np.min(self.data.Low[max(0, i - lookback):i + 1]))

	def next(self):
		i = len(self.data.Close) - 1

		price = float(self.data.Close[i])
		ema50_now = self.ema_50[i]
		ema200_now = self.ema_200[i]
		adx_now = self.adx[i]

		# Check for long setup
		bullish_trend = ema50_now > ema200_now
		adx_strong = adx_now > self.min_adx
		adx_rising = self.adx[i] > self.adx[i - 1] if i > 0 else False
		near_ema50 = abs(price - ema50_now) / ema50_now < self.ema_touch_tol

		# No trade if ADX too flat
		if adx_now < self.flat_adx:
			return

		# --- LONG ENTRY ---
		if bullish_trend and adx_rising and adx_strong and near_ema50:
			# Check for bullish signal (engulfing or pin bar)
			if self._is_bullish_engulfing(i) or self._is_bullish_pin_bar(i):
				# Compute stop loss: recent swing low
				sl_price = self._recent_swing_low(i)
				risk_per_unit = (price - sl_price) / price
				if risk_per_unit <= 0:
					return  # avoid negative/0 risk

				# Risk-based position sizing
				risk_amount = self.equity * (self.risk_per_trade_pct / 100.0)
				position_size = float(round(risk_amount / risk_per_unit))
				# print(f"Position size: {position_size}")
				# position_size = max(position_size, 0.01)
				# position_size = 200_000

				# Take profit: 2:1 RR
				tp_price = price + self.reward_risk_ratio * risk_per_unit

				if position_size > 0 and sl_price < price < tp_price:
					logging.info(f"({self.data.index[i]}) LONG: {position_size} @ {price}")
					self.buy(sl=sl_price, tp=tp_price)

		# # --- Exit Conditions for Trailing Stop (Long) ---
		# if self.position.is_long:
		# 	# Trailing stop below higher lows
		# 	lookback = 10
		# 	trailing_sl = self._recent_swing_low(i, lookback)
		# 	if trailing_sl > 0 and trailing_sl > self.position.sl:
		# 		self.position.sl = trailing_sl
		#
		# 	# ADX reverses & price closes below EMA50
		# 	if adx_now < self.adx[i - 1] and price < ema50_now:
		# 		self.position.close()
