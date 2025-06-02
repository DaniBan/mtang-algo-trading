import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from memory_profiler import profile
from itertools import islice
import pandas as pd
from collections import deque
from dataclasses import dataclass
from enum import Enum
import matplotlib.pyplot as plt

from tqdm import tqdm

load_dotenv()


# TODO: add orders and results to the backtest besides computing the RSI + other statistics
class OrderType(Enum):
    BUY = 0
    SELL = 1


@dataclass()
class Order:
    type: OrderType
    price: float
    sl: float
    tp: float

    def __eq__(self, other):
        return self.type == other.type and self.sl == other.sl and self.tp == other.tp and self.price == other.price


def load_rates(src: Path) -> pd.DataFrame:
    return pd.read_csv(src).set_index("time")


def cross_over(points: list[float], target: float) -> bool:
    if len(points) < 2:
        raise ValueError("Not enough points to compute crossover")
    return points[-1] > target > points[-2] or points[-1] < target < points[-2]


def backtrade_rsi_1(rates: pd.DataFrame, rsi_window: int, lower_bound: int, upper_bound: int):
    sl_pct = 0.1
    tp_pct = 0.1

    rsi_list = []

    orders = []
    losses = 0
    wins = 0

    buffer = np.empty(rsi_window)
    buffer[:] = np.nan
    buffer_idx = 0
    c = 0

    a = 2 / (rsi_window + 1)
    for idx, row in tqdm(enumerate(rates.itertuples()), total=len(rates)):
        current_price = row.Close
        if idx >= rsi_window:
            avg_u = 0
            avg_d = 0
            for pi, price in enumerate(buffer):
                if pi > 0:
                    avg_u = a * max(0, price - buffer[pi - 1]) + (1 - a) * avg_u
                    avg_d = a * max(0, buffer[pi - 1] - price) + (1 - a) * avg_d

            rsi = 100
            if avg_d > 0:
                rs = avg_u / avg_d
                rsi = 100 - 100 / (1 + rs)

            # Check for SELL orders
            if len(rsi_list) > 0 and rsi < upper_bound < rsi_list[-1]:
                sl = current_price + sl_pct * current_price
                tp = current_price - tp_pct * current_price
                orders.append(Order(OrderType.SELL, price=current_price, sl=sl, tp=tp))

            # Check for BUY orders
            if len(rsi_list) > 0 and rsi < lower_bound < rsi_list[-1]:
                sl = current_price - sl_pct * current_price
                tp = current_price + tp_pct * current_price
                orders.append(Order(OrderType.BUY, price=current_price, sl=sl, tp=tp))

            complete_orders = []
            for entry in orders:
                if entry.type == OrderType.SELL:
                    if current_price >= entry.sl:
                        losses += 1
                        complete_orders.append(entry)
                    elif current_price <= entry.tp:
                        wins += 1
                        complete_orders.append(entry)
                if entry.type == OrderType.BUY:
                    if current_price <= entry.sl:
                        losses += 1
                        complete_orders.append(entry)
                    elif current_price >= entry.tp:
                        wins += 1
                        complete_orders.append(entry)

            for entry in complete_orders:
                orders.remove(entry)

            rsi_list.append(rsi)
        buffer[buffer_idx % rsi_window] = current_price
        buffer_idx += 1

    print(f"Wins: {wins}, Losses: {losses}")
    print(f"Win Rate: {wins / (wins + losses):.2f}")


def backtrade_rsi_2(rates: pd.DataFrame, rsi_window: int, upper_bound: int, lower_bound: int):
    sl_pct = 0.1
    tp_pct = 0.1

    delta = rates["Close"].diff()
    avg_u = delta.where(delta > 0, 0).ewm(span=rsi_window).mean()
    avg_d = (-delta.where(delta < 0, 0)).ewm(span=rsi_window).mean()

    losses = 0
    wins = 0

    print(f"Wins: {wins}, Losses: {losses}")
    print(f"Win Rate: {wins / (wins + losses):.2f}")


def main():
    path_to_csv = Path(__file__).parent.parent.parent / "resources" / "USDCAD_15_01_01_2023-24_05_2025.csv"
    rates: pd.DataFrame = load_rates(path_to_csv)
    print(len(rates))

    from time import perf_counter

    time_start = perf_counter()
    backtrade_rsi_1(rates, 14, 30, 70)
    # backtrade_rsi_2(rates, 14, 30, 70)
    time_end = perf_counter()
    print(f"Time elapsed: {time_end - time_start:.2f} seconds")

    # rsi_slice = rsi[-30:]
    # slice_time = rates.index[-30:]
    #
    # fig = plt.figure()
    # plt.plot(slice_time, rsi_slice, label="RSI")
    # plt.xlabel("Time")
    # plt.ylabel("RSI")
    # plt.xticks(rotation=30)
    #
    # plt.axhline(y=upper_bound, color="r", linestyle="--", label="Upper Bound")
    # plt.axhline(y=lower_bound, color="g", linestyle="--", label="Lower Bound")
    # plt.legend(loc="upper right")
    #
    # plt.show()


if __name__ == "__main__":
    # l = [
    #     {
    #         "status": 0,
    #     },
    #     {
    #         "status": 0,
    #     }
    # ]
    # for el in l:
    #     el["status"] = 1
    #
    # print(l)
    main()
