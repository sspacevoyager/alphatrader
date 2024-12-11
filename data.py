import os
import pickle
import logging
import pandas as pd
import ccxt.async_support as ccxt_async
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    def __init__(self, exchange_name='binance'):
        try:
            self.exchange = getattr(ccxt_async, exchange_name)()
            logging.info(f"Connected to {exchange_name} exchange.")
        except AttributeError:
            logging.error(f"Exchange {exchange_name} not found in ccxt.")
            raise ValueError(f"Exchange {exchange_name} not found.")

    def validate_parameters(self, pair: str, timeframes: list, start_date: str, end_date: str):
        # Validate pair format
        if not isinstance(pair, str) or '/' not in pair:
            raise ValueError("Invalid pair format. Expected format: 'BASE/QUOTE' (e.g., 'BTC/USDT').")
        
        # Validate timeframes
        valid_timeframes = self.exchange.timeframes.keys()
        for timeframe in timeframes:
            if timeframe not in valid_timeframes:
                raise ValueError(f"Invalid timeframe {timeframe}. Valid options are: {', '.join(valid_timeframes)}")
        
        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid date format. Expected format: 'YYYY-MM-DD'.")

    async def fetch_data(self, pair: str, timeframes: list, start_date: str, end_date: str) -> dict:
        self.validate_parameters(pair, timeframes, start_date, end_date)
        data_dict = {}
        for timeframe in timeframes:
            data_dict[timeframe] = await self._fetch_single_timeframe_data(pair, timeframe, start_date, end_date)
        return data_dict

    async def _fetch_single_timeframe_data(self, pair: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
        # Ensure cache directory exists
        cache_dir = 'cache'
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        # Construct cache file path
        cache_file = os.path.join(cache_dir, f"cache_{pair.replace('/', '_')}_{timeframe}_{start_date}_{end_date}.pkl")
        
        # Attempt to load from cache
        if os.path.exists(cache_file):
            logging.info(f"Loading data from cache: {cache_file}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        # Fetch data if cache is not available
        since = self.exchange.parse8601(f'{start_date}T00:00:00Z')
        end_timestamp = self.exchange.parse8601(f'{end_date}T00:00:00Z')
        all_data = []
        logging.info(f"Fetching data for {pair} from {start_date} to {end_date} with timeframe {timeframe}.")
        
        while since < end_timestamp:
            try:
                data = await self.exchange.fetch_ohlcv(pair, timeframe=timeframe, since=since, limit=1000)
                if not data:
                    logging.warning("No more data available.")
                    break
                since = data[-1][0] + 1
                all_data.extend(data)
            except ccxt_async.NetworkError as e:
                logging.error(f"Network error: {e}")
                break
            except ccxt_async.ExchangeError as e:
                logging.error(f"Exchange error: {e}")
                break
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                break

        if not all_data:
            logging.error("Failed to fetch any data.")
            raise ValueError("No data fetched.")

        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        logging.info("Data fetching complete.")

        # Cache the data
        with open(cache_file, 'wb') as f:
            pickle.dump(df, f)
            logging.info(f"Data cached to {cache_file}")

        return df

    def preprocess_data(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        logging.info("Preprocessing data.")
        try:
            raw_data['date'] = pd.to_datetime(raw_data['timestamp'], unit='ms')
            raw_data.set_index('date', inplace=True)
            raw_data.drop(columns=['timestamp'], inplace=True)
            raw_data.sort_index(inplace=True)
            raw_data = raw_data.apply(pd.to_numeric, errors='coerce')
            raw_data.dropna(inplace=True)
            raw_data = raw_data[~raw_data.index.duplicated(keep='first')]  # Remove duplicates
            logging.info("Data preprocessing complete.")
        except Exception as e:
            logging.error(f"Error during data preprocessing: {e}")
            raise

        return raw_data

    def validate_data(self, data: pd.DataFrame) -> bool:
        logging.info("Validating data.")
        if data.isnull().values.any():
            logging.error("Data contains null values.")
            return False
        if not data.index.is_monotonic_increasing:
            logging.error("Data index is not monotonic increasing.")
            return False
        logging.info("Data validation successful.")
        return True