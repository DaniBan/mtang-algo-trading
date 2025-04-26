import numpy as np
from backtesting import Strategy
from scipy.signal import find_peaks


class SupportResistance(Strategy):
	"""
	Support & Resistance Strategy

	BUY:
	Price hits support and bounces back above a set threshold (parametrizable)
	TP: under the next resistance; if None => x:1 win / lose ratio (parametrizable)
	SL: under the hit support

	SELL:
	Price hits resistance and bounces back beneath a set threshold (parametrizable)
	TP: above the next support; if None => x:1 win / lose ration (parametrizable)
	SL: above the hit resistance

	What do we need?
	A set of supports and resistances.

	How?
	Identify the support and resistance the price lies between.
	Apply the above rules for placing orders when the price hits the identified support or resistance.
	TBD: Use the same candle that hits the levels OR use the next candle?
	"""
	window = 30
	level_pad = 0.015
	prominence = 0.035

	# Risk-management parameters
	risk_per_trade_pct = 3  # Percentage of the account to risk (2%)

	def __init__(self, broker, data, params):
		super().__init__(broker, data, params)
		self.support_lines = None
		self.resistance_lines = None
		self.levels = None

	def init(self):
		self.support_lines = self._compute_support_lines(self.data, self.window, self.prominence)
		self.resistance_lines = self._compute_resistance_lines(self.data, self.window, self.prominence)
		self.levels = np.concatenate((self.support_lines, self.resistance_lines))
		self.levels.sort()

	def next(self):
		price = float(self.data.Close[-1])
		prev_price = float(self.data.Close[-2])

		# Find the levels the price lies between
		idx = np.searchsorted(self.levels, price)
		if idx == 0:
			if price < self.levels[idx] - self.level_pad:
				sl_price = self.levels[idx] + self.level_pad
				tp_price = self.levels[idx] - 4 * self.level_pad

				# Compute position size
				risk_amount = self.equity * (self.risk_per_trade_pct / 100.0)
				risk_per_unit = (sl_price - price) / price
				position_size = round(risk_amount / risk_per_unit / 100_000)

				if tp_price < price < sl_price:
					self.sell(size=position_size, sl=sl_price, tp=tp_price)
		elif idx == len(self.levels):
			if price > self.levels[idx - 1] + self.level_pad:
				sl_price = self.levels[idx - 1] - self.level_pad
				tp_price = self.levels[idx - 1] + 4 * self.level_pad

				# Compute position size
				risk_amount = self.equity * (self.risk_per_trade_pct / 100.0)
				risk_per_unit = (sl_price - price) / price
				position_size = round(risk_amount / risk_per_unit / 100_000)

				if tp_price < price < sl_price:
					self.sell(size=position_size, sl=sl_price, tp=tp_price)
		else:
			low = self.levels[idx - 1]
			high = self.levels[idx]

			if price > high - self.level_pad and (
					high - self.level_pad <= prev_price <= high + self.level_pad):
				tp_price = low + self.level_pad
				sl_price = high + self.level_pad

				# Compute position size
				risk_amount = self.equity * (self.risk_per_trade_pct / 100.0)
				risk_per_unit = (sl_price - price) / price
				position_size = round(risk_amount / risk_per_unit / 100_000)

				if tp_price < price < sl_price:
					self.sell(size=position_size, sl=sl_price, tp=tp_price)
			if price < low + self.level_pad and (
					low - self.level_pad <= prev_price <= low + self.level_pad):
				tp_price = high - self.level_pad
				sl_price = low - self.level_pad

				# Compute position size
				risk_amount = self.equity * (self.risk_per_trade_pct / 100.0)
				risk_per_unit = (price - sl_price) / price
				position_size = round(risk_amount / risk_per_unit / 100_000)

				if sl_price < price < tp_price:
					self.buy(size=position_size, sl=sl_price, tp=tp_price)

	@staticmethod
	def _compute_support_lines(data, window: int, prominence: float = 0.002):
		peaks, _ = find_peaks(-data.Low, distance=window, prominence=prominence)
		peaks_values = data.Close[peaks]
		return peaks_values

	@staticmethod
	def _compute_resistance_lines(data, window: int, prominence: float = 0.002):
		peaks, _ = find_peaks(data.High, distance=window, prominence=prominence)
		peaks_values = data.Close[peaks]
		return peaks_values
