import logging
from datetime import datetime
from pathlib import Path

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
    def _process_rates(rates: pd.DataFrame) -> pd.DataFrame:
        # Convert timestamp to datetime
        rates = rates[["time", "open", "high", "low", "close", "tick_volume"]].rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "tick_volume": "Volume"
        })

        rates["time"] = pd.to_datetime(rates["time"], unit="s")
        rates.set_index("time", inplace=True)
        return rates

    def fetch_rates(self, symbol: str, timeframe: int, start_pos: int, count: int):
        rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        if rates is None:
            logging.error("Failed to fetch rates")
            return None
        df = pd.DataFrame(rates)
        return self._process_rates(df)

    def fetch_rates_range(self, symbol: str, timeframe: int, date_from: datetime, date_to: datetime):
        rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        if rates is None:
            logging.error("Failed to fetch rates")
            return None

        df = pd.DataFrame(rates)
        return self._process_rates(df)

    def download_rates(self, dst_path: Path, symbol: str, timeframe: int, start_pos: int, count: int):
        # Fetch rates
        rates_frame = self.fetch_rates(symbol=symbol, timeframe=timeframe, start_pos=start_pos, count=count)

        # Save as CSV to dst_path
        out_file = dst_path / f"{symbol}_{timeframe}_s{start_pos}_c{count}.csv"
        rates_frame.to_csv(out_file, index=True)
        logging.info(f"Rates saved to {out_file}")

    def download_rates_range(self, dst_path: Path, symbol: str, timeframe: int, date_from: datetime, date_to: datetime):
        # Fetch rates
        rates_frame = self.fetch_rates_range(symbol=symbol, timeframe=timeframe, date_from=date_from,
                                             date_to=date_to)

        # Save as CSV to dst_path
        file_name = f"{symbol}_{timeframe}_{date_from.strftime('%d_%m_%Y')}-{date_to.strftime('%d_%m_%Y')}.csv"
        out_file = dst_path / file_name
        rates_frame.to_csv(out_file, index=True)
        logging.info(f"Rates saved to {out_file}")
