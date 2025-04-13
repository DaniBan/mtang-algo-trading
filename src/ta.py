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


def check_rsi_signal(rates: pd.DataFrame,
                     timeperiod: int = 14,
                     lower_bound: int = RSI_OVERSOLD,
                     upper_bound: int = RSI_OVERBOUGHT) -> str:
    """Generate trading signals ("BUY", "SELL", or "HOLD") based on RSI indicator crossovers.

    This function calculates the Relative Strength Index (RSI) over a provided period and
    generates signals based on RSI crossing predefined threshold values. A BUY signal is
    produced when RSI crosses above the lower bound (indicating an oversold condition),
    while a SELL signal occurs when the RSI crosses below the upper bound (indicating an
    overbought condition). If no crossover event is detected, the function returns HOLD.

    Args:
        rates (pd.DataFrame): DataFrame containing historical closing prices in a column named "Close".
        timeperiod (int, optional): The number of periods used to calculate RSI. Defaults to 14.
        lower_bound (int, optional): The lower RSI threshold indicating oversold conditions. Defaults to RSI_OVERSOLD.
        upper_bound (int, optional): The upper RSI threshold indicating overbought conditions. Defaults to RSI_OVERBOUGHT.

    Returns:
        str: A signal indicating recommended trading action:
            - "BUY": RSI has crossed above the lower bound (suggesting a buy opportunity).
            - "SELL": RSI has crossed below the upper bound (suggesting a sell opportunity).
            - "HOLD": No RSI crossover detected; no immediate trading action recommended.

    """
    rsi_values = talib.RSI(rates["Close"], timeperiod=timeperiod)  # Calculate RSI

    # Get the last two RSI values to detect crossovers
    latest_rsi = rsi_values.iloc[-1]  # most recent RSI value
    prev_rsi = rsi_values.iloc[-2]  # previous RSI value

    signal = "HOLD"

    # Check for crossover above lower bound (buy signal)
    if prev_rsi < lower_bound < latest_rsi:
        signal = "BUY"
    # Check for crossover below upper bound (sell signal)
    elif prev_rsi > upper_bound > latest_rsi:
        signal = "SELL"

    return signal
