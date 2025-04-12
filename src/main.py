import logging
import os
from datetime import datetime

import MetaTrader5 as mt5
import matplotlib
import matplotlib.pyplot as plt
import schedule
import time
from dotenv import load_dotenv
from pandas.plotting import register_matplotlib_converters

from metatrader import MT5Connection
from trading_analysis import check_rsi_signal

# Load env vars
load_dotenv()

# Register matplotlib converters
register_matplotlib_converters()
matplotlib.use("TkAgg")

# Configure logging
level = logging.DEBUG
fmt = "[%(levelname)s]: %(asctime)s - %(message)s"
logging.basicConfig(level=level, format=fmt)


def download_rates(dst_path: str, symbol: str, timeframe: int, start_pos: int, count: int):
    # Fetch rates
    rates_frame = MT5Connection.fetch_rates(symbol=symbol, timeframe=timeframe, start_pos=start_pos, count=count)

    # Save as CSV to dst_path
    out_file = os.path.join(dst_path, f"{symbol}_{timeframe}_s{start_pos}_c{count}.csv")
    rates_frame.to_csv(out_file, index=False)
    logging.info(f"Rates saved to {out_file}")


def download_rates_range(dst_path: str, symbol: str, timeframe: int, date_from: datetime, date_to: datetime):
    # Fetch rates
    rates_frame = MT5Connection.fetch_rates_range(symbol=symbol, timeframe=timeframe, date_from=date_from,
                                                  date_to=date_to)

    # Save as CSV to dst_path
    file_name = f"{symbol}_{timeframe}_{date_from.strftime('%d_%m_%Y')}-{date_to.strftime('%d_%m_%Y')}.csv"
    out_file = os.path.join(dst_path, file_name)
    rates_frame.to_csv(out_file, index=False)
    logging.info(f"Rates saved to {out_file}")


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


def rsi_strategy(symbol: str, timeframe: int, risk_per_trade: float, risk_in_pips: int, reward_to_risk_ratio: int):
    """
    Main trading logic to run at each scheduled interval.
    Fetches recent market data, checks for RSI signals, and places orders.
    """
    logging.info("Executing RSI trading logic...")
    rates = MT5Connection.fetch_rates(symbol, timeframe, 0, 50)

    # Check RSI signal
    signal = check_rsi_signal(rates)
    # if signal == "BUY":
    # place_order(symbol, "BUY", risk_per_trade, risk_in_pips, reward_to_risk_ratio)
    # elif signal == "SELL":
    # place_order(symbol, "SELL", risk_per_trade, risk_in_pips, reward_to_risk_ratio)

    logging.info(f"Signal: {signal}")


def main():
    symbol = "EURAUD"
    timeframe = mt5.TIMEFRAME_M1

    with MT5Connection(int(os.getenv("ACCOUNT_ID")), os.getenv("PASSWORD"), os.getenv("MT5_SERVER")):
        # Schedule the RSI-based trading logic to run every minute
        schedule.every(1).minute.at(":01").do(
            rsi_strategy,
            symbol=symbol,
            timeframe=timeframe,
            risk_per_trade=0.02,
            risk_in_pips=30,
            reward_to_risk_ratio=2
        )

        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    main()
