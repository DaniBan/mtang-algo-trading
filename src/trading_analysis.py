import MetaTrader5 as mt5
import pandas as pd
import talib

# Constants
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70


def calculate_support_resistance(rates: pd.DataFrame, window: int = 50, inplace: bool = False) -> pd.DataFrame:
    """
    Compute support and resistance levels using rolling min and max.
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


def moving_average_crossover(symbol: str, timeframe: int, short_window: int, long_window: int) -> str:
    """
    Check for moving average crossover signals.
    """
    # Fetch historical rates
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, long_window + 1)
    df = pd.DataFrame(rates)

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


def check_rsi_signal(rates: pd.DataFrame) -> str:
    """
    Analyze RSI values and return trading signals based on thresholds.

    Args:
        rates (pd.DataFrame): Historical rate data containing a 'close' column.

    Returns:
        str: "BUY" if RSI < 30, "SELL" if RSI > 70, "HOLD" otherwise.
    """
    rsi_values = talib.RSI(rates["close"], timeperiod=14)  # Calculate RSI
    latest_rsi = rsi_values.iloc[-1]  # Get the most recent RSI value

    if latest_rsi < RSI_OVERSOLD:
        return "BUY"
    elif latest_rsi > RSI_OVERBOUGHT:
        return "SELL"
    else:
        return "HOLD"
