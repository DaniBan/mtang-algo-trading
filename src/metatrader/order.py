import logging
import MetaTrader5 as mt5


def place_order(symbol: str, action: str, risk_per_trade: float = 0.01, risk_in_pips: int = 20,
                reward_to_risk_ratio: float = 2) -> bool:
    """
    Place a trading order (BUY or SELL) with proper risk management.

    Args:
        symbol (str): Trading instrument (e.g., "EURUSD").
        action (str): Trading action ("BUY" or "SELL").
        risk_per_trade (float): Fraction of account balance to risk per trade (e.g., 0.01 for 1%).
        risk_in_pips (int): Distance (in pips) between the entry price and the stop-loss (SL).
        reward_to_risk_ratio (float): Ratio of take-profit (TP) to stop-loss (e.g., 2 for 2:1 RR).

    Returns:
        bool: True if the order was successfully placed, False otherwise.
    """
    # Determine the order type (BUY or SELL)
    action_type = mt5.ORDER_TYPE_BUY if action.upper() == "BUY" else mt5.ORDER_TYPE_SELL

    # Fetch symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None or not symbol_info.visible:
        logging.error(f"Symbol {symbol} not available or visible.")
        return False

    # Fetch account information
    account_info = mt5.account_info()
    if account_info is None:
        logging.error("Failed to retrieve account information.")
        return False

    # Calculate lot size dynamically based on risk
    balance = account_info.balance
    tick_size = symbol_info.point
    tick_value = symbol_info.trade_tick_value or 1.0
    price_per_pip = tick_value / tick_size
    lot_size = (balance * risk_per_trade) / (risk_in_pips * price_per_pip)

    # Adjust for the symbol's minimum lot size
    lot_size = max(lot_size, symbol_info.volume_min)
    lot_size = round(lot_size, symbol_info.volume_step)

    # Fetch current price
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logging.error(f"Failed to fetch current price for {symbol}.")
        return False

    entry_price = tick.ask if action.upper() == "BUY" else tick.bid
    stop_loss = entry_price - (risk_in_pips * tick_size) if action.upper() == "BUY" else entry_price + (
            risk_in_pips * tick_size)
    take_profit = entry_price + (
            risk_in_pips * tick_size * reward_to_risk_ratio) if action.upper() == "BUY" else entry_price - (
            risk_in_pips * tick_size * reward_to_risk_ratio)

    # Ensure stop-loss and take-profit are valid
    if (action.upper() == "BUY" and stop_loss >= entry_price) or (
            action.upper() == "SELL" and stop_loss <= entry_price):
        logging.error("Invalid stop-loss level.")
        return False
    if (action.upper() == "BUY" and take_profit <= entry_price) or (
            action.upper() == "SELL" and take_profit >= entry_price):
        logging.error("Invalid take-profit level.")
        return False

    # Create a trade request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": action_type,
        "price": entry_price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 10,  # Maximum allowed deviation in points
        "magic": 234000,  # Custom magic number
        "comment": "Risk-managed trade",
        "type_time": mt5.ORDER_TIME_GTC,  # Good till cancel
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Send the trade request
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(
            f"Order executed: {action} {lot_size} {symbol}. Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}")
        return True
    else:
        logging.error(f"Order placement failed. Retcode: {result.retcode}")
        return False
