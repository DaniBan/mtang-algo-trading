import logging
import os
from datetime import datetime

import MetaTrader5 as mt5
import matplotlib
import matplotlib.pyplot as plt
from backtesting import Backtest
from dotenv import load_dotenv
from pandas.plotting import register_matplotlib_converters

from mt5_connection import MT5Connection
from strategies import (
    RsiOscillator
)

from pathlib import Path

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


def main():
    symbol = "EURAUD"
    timeframe = mt5.TIMEFRAME_M15

    with MT5Connection(int(os.getenv("ACCOUNT_ID")), os.getenv("PASSWORD"), os.getenv("MT5_SERVER")):
        rates_df = MT5Connection.fetch_rates_range(symbol=symbol,
                                                   timeframe=timeframe,
                                                   date_from=datetime(2024, 12, 1),
                                                   date_to=datetime.now())

        # peaks, _ = find_peaks(rates_df["high"], distance=20, prominence=.001)
        # peaks_values = rates_df.iloc[peaks]["high"].values
        # resistance_lines = [np.full(len(rates_df), val) for val in peaks_values]
        #
        # peaks, _ = find_peaks(-rates_df["low"], distance=20, prominence=.001)
        # peaks_values = rates_df.iloc[peaks]["high"].values
        # support_lines = [np.full(len(rates_df), val) for val in peaks_values]

        bt_data = rates_df[["time", "open", "high", "low", "close", "tick_volume"]]
        bt_data = bt_data.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "tick_volume": "Volume"
        })
        try:
            bt = Backtest(bt_data, RsiOscillator, cash=10_000)
            # stats = bt.optimize(
            #     upper_bound=range(50, 57, 5),
            #     lower_bound=range(10, 45, 5),
            #     rsi_window=range(10, 30, 2),
            #     maximize="Win Rate [%]"
            # )
            stats = bt.run()
            print(stats)
            lb = stats["_strategy"].lower_bound
            ub = stats["_strategy"].upper_bound
            window = stats["_strategy"].rsi_window

            # Plot backtest stats
            plot_path: Path = Path(f"../backtests/lb{lb}_ub{ub}_win{window}")
            plot_path.mkdir(exist_ok=True, parents=True)
            bt.plot(filename=str(plot_path))
        except Exception:
            logging.exception("Exception occurred while backtesting")


if __name__ == '__main__':
    main()
