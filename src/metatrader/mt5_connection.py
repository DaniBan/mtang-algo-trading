import logging
from datetime import datetime

import MetaTrader5 as mt5
import pandas as pd


class MT5Connection:
    def __init__(self, account: int, password: str, server: str):
        self.account = account
        self.password = password
        self.server = server

    def __enter__(self):
        if mt5.initialize():
            logging.info("MT5 initialized successfully")

            authorized = mt5.login(self.account, self.password, self.server)
            if authorized:
                logging.info("Logged in successfully")
            else:
                logging.error("Login failed")
                logging.error(f"Error code: {mt5.last_error()}")
                quit()
        else:
            logging.error(f"MT5 failed to initialize. Error code: {mt5.last_error()}")
            raise ConnectionError("Failed to initialize MT5")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        mt5.shutdown()
        logging.info("MT5 shutdown successfully")
        if exc_type is not None:
            logging.error(f"An exception occurred: {exc_val}")
        return True

    @staticmethod
    def fetch_rates(symbol: str, timeframe: int, start_pos: int, count: int):
        rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        if rates is None:
            logging.error("Failed to fetch rates")
            return None
        df = pd.DataFrame(rates)

        # Convert timestamp to datetime
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df

    @staticmethod
    def fetch_rates_range(symbol: str, timeframe: int, date_from: datetime, date_to: datetime):
        rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        if rates is None:
            logging.error("Failed to fetch rates")
            return None
        df = pd.DataFrame(rates)

        # Convert timestamp to datetime
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df
