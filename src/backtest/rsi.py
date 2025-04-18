import logging
import multiprocessing
import os
from datetime import datetime
from pathlib import Path

import MetaTrader5 as mt5
import matplotlib
from backtesting import Backtest, backtesting
from dotenv import load_dotenv
from pandas.plotting import register_matplotlib_converters

from backtest.strategies import (
    RsiOscillator
)
from metatrader import MT5Connection

# Load env vars
load_dotenv()

# Register matplotlib converters
register_matplotlib_converters()
matplotlib.use("TkAgg")

# Configure logging
level = logging.DEBUG
fmt = "[%(levelname)s]: %(asctime)s - %(message)s"
logging.basicConfig(level=level, format=fmt)
logger = logging.getLogger(__name__)


def main() -> None:
    symbol = "USDCAD"
    timeframe = mt5.TIMEFRAME_M1

    with (MT5Connection(int(os.getenv("ACCOUNT_ID")), os.getenv("PASSWORD"), os.getenv("MT5_SERVER")) as mt5_conn):
        rates = mt5_conn.fetch_rates_range(symbol=symbol,
                                           timeframe=timeframe,
                                           date_from=datetime(2025, 4, 10),
                                           date_to=datetime.now())

        try:
            bt = Backtest(rates, RsiOscillator, cash=10_000)
            backtesting.Pool = multiprocessing.Pool
            # stats = bt.run()
            stats = bt.optimize(
                upper_bound=range(50, 90, 5),
                lower_bound=range(10, 45, 5),
                rsi_window=range(10, 20, 2),
                maximize="Return [%]"
            )
            logger.info(f"STATS\n=============================================\n{stats}")

            lb = stats["_strategy"].lower_bound
            ub = stats["_strategy"].upper_bound
            window = stats["_strategy"].rsi_window

            logger.info(f"LB: {lb}, UB: {ub}, WINDOW: {window}")

            # Plot backtest stats
            plot_path: Path = Path(__file__).parent.parent.parent / f"backtests/lb{lb}_ub{ub}_win{window}"
            bt.plot(filename=str(plot_path))
        except Exception:
            logger.exception("Exception occurred while backtesting")


if __name__ == "__main__":
    main()
