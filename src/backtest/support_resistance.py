import logging
import os
from datetime import datetime
from pathlib import Path

import MetaTrader5 as mt5
import matplotlib
from backtesting import Backtest
from dotenv import load_dotenv
from pandas.plotting import register_matplotlib_converters

from backtest.strategies import (
	SupportResistance
)
from metatrader import MT5Connection

# Load env vars
load_dotenv()

# Register matplotlib converters
register_matplotlib_converters()
matplotlib.use("TkAgg")

# Configure logging
level = logging.INFO
fmt = "[%(levelname)s]: %(asctime)s - %(message)s"
logging.basicConfig(level=level, format=fmt)
logger = logging.getLogger(__name__)


def main() -> None:
	symbol = "USDCAD"
	timeframe = mt5.TIMEFRAME_H4

	with (MT5Connection(int(os.getenv("ACCOUNT_ID")), os.getenv("PASSWORD"), os.getenv("MT5_SERVER")) as mt5_conn):
		rates = mt5_conn.fetch_rates_range(symbol=symbol,
										   timeframe=timeframe,
										   date_from=datetime(2024, 6, 1),
										   date_to=datetime.now())

		try:
			bt = Backtest(rates, SupportResistance, cash=100_000)
			stats = bt.run()
			# stats = bt.optimize(
			# 	window=range(30, 150, 10),
			# 	level_pad=[i * 0.0001 for i in range(1, 11)],
			# 	prominence=[i * 0.001 for i in range(1, 11)],
			# 	maximize=lambda s: s["Return [%]"] * 0.7 + s["Win Rate [%]"] * 0.3
			#
			# )
			logger.info(f"STATS\n=============================================\n{stats}")

			window = stats["_strategy"].window
			level_pad = stats["_strategy"].level_pad
			prominence = stats["_strategy"].prominence

			logger.info(f"window: {window}, level_pad: {level_pad}, prominence: {prominence}")

			# Plot backtest stats
			plot_subpath = Path("backtests", "supp_res", f"window{window}_level_pad{level_pad}_prominence{prominence}")
			plot_path: Path = Path(__file__).parent.parent.parent / plot_subpath
			plot_path.mkdir(parents=True, exist_ok=True)
			bt.plot(filename=str(plot_path))
		except Exception:
			logger.exception("Exception occurred while backtesting")


if __name__ == "__main__":
	main()
