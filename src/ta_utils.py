import pandas as pd
import MetaTrader5 as mt5


def calculate_support_resistance(rates: pd.DataFrame, window: int = 50, inplace: bool = False) -> pd.DataFrame:
    """
    Compute support and resistance levels using rolling min and max
    """
    if not inplace:
        rates = rates.copy()

    rates["resistance"] = rates["high"].rolling(window=window).max()
    rates["support"] = rates["low"].rolling(window=window).min()
    return rates


def calculate_pivot_points(rates: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
    """
    Calculate pivot points, support, and resistance levels.
    """
    if not inplace:
        rates = rates.copy()

    rates["PP"] = (rates["high"] + rates["low"] + rates["close"]) / 3
    rates["R1"] = (2 * rates["PP"]) - rates["low"]
    rates["S1"] = (2 * rates["PP"]) - rates["high"]
    return rates


def moving_average_crossover(symbol, timeframe, short_window, long_window):
    # Fetch historical rates
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, long_window + 1)
    df = pd.DataFrame(rates)
    print(df.head())
    df["time"] = pd.to_datetime(df["time"], unit="s")

    # Calculate moving averages
    df["short_ma"] = df["close"].rolling(window=short_window).mean()
    df["long_ma"] = df["close"].rolling(window=long_window).mean()

    # Check for crossover
    if df["short_ma"].iloc[-2] < df["long_ma"].iloc[-2] and df["short_ma"].iloc[-1] > df["long_ma"].iloc[-1]:
        return "BUY"
    elif df["short_ma"].iloc[-2] > df["long_ma"].iloc[-2] and df["short_ma"].iloc[-1] < df["long_ma"].iloc[-1]:
        return "SELL"
    else:
        return "HOLD"
