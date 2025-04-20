import logging
import os
import time

import MetaTrader5 as mt5
import matplotlib
import matplotlib.pyplot as plt
import schedule
from dotenv import load_dotenv
from pandas.plotting import register_matplotlib_converters

from metatrader import MT5Connection, place_order
from ta import check_rsi_signal

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


def plot_data(rates_df, support_lines=None, resistance_lines=None):
    plt.figure(figsize=(12, 6))
    plt.plot(rates_df["time"], rates_df["close"], label="Close Price", color="blue")
    if support_lines:
        [plt.plot(rates_df["time"], resistance, color="red", linestyle="--") for resistance in resistance_lines]
    if resistance_lines:
        [plt.plot(rates_df["time"], support, color="green", linestyle="--") for support in support_lines]
    # plt.plot(rates_df["time"], rates_df["support"], label="Support", color="green", linestyle="--")
    # plt.plot(rates_df["time"], rates_df["resistance"], label="Resistance", color="red", linestyle="--")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.legend()
    plt.grid()
    plt.show()


def rsi_strategy(connection: MT5Connection, symbol: str, timeframe: int, risk_per_trade: float,
                 reward_to_risk_ratio: int, timeperiod: int, lower_bound: int, upper_bound: int):
    """
    Main trading logic to run at each scheduled interval.
    Fetches recent market data, checks for RSI signals, and places orders.
    """
    rates = connection.fetch_rates(symbol, timeframe, 0, 50)

    # Compute risk in pips
    tick = mt5.symbol_info_tick(symbol)
    risk_pct = 0.1

    # Check RSI signal
    signal = check_rsi_signal(rates, timeperiod, lower_bound, upper_bound)
    logger.info(f"Signal: {signal}")

    if signal == "BUY":
        price = tick.ask
        risk_in_pips = round((price - risk_pct / 100 * price) * 10)
        place_order(symbol, "BUY", risk_per_trade, risk_in_pips, reward_to_risk_ratio)
    elif signal == "SELL":
        price = tick.bid
        risk_in_pips = round((price + risk_pct / 100 * price) * 10)
        place_order(symbol, "SELL", risk_per_trade, risk_in_pips, reward_to_risk_ratio)


def main():
    symbol = "USDCAD"
    timeframe = mt5.TIMEFRAME_M1

    with MT5Connection(int(os.getenv("ACCOUNT_ID")), os.getenv("PASSWORD"), os.getenv("MT5_SERVER")) as mt_conn:
        # Schedule the RSI-based trading logic to run every minute
        schedule.every(1).minute.at(":01").do(
            rsi_strategy,
            connection=mt_conn,
            symbol=symbol,
            timeframe=timeframe,
            risk_per_trade=0.02,
            reward_to_risk_ratio=1,
            timeperiod=10,
            lower_bound=30,
            upper_bound=55
        )

        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    main()
