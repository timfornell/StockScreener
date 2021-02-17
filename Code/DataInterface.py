from queue import Empty
import pandas as pd
import multiprocessing as mp
import time

from pathlib import Path
from Definitions import DATA_FOLDER, DATA_INTERFACE_MESSAGE_HEADER

class DataInterface():
    def __init__(self, event, lock: mp.Lock, queue: mp.Queue):
        self.stocklist = pd.DataFrame()
        self.working_stocklist = pd.DataFrame()
        self.lock = lock
        self.queue = queue
        self.event = event

        print("{} Data interface waiting for data gatherer...".format(DATA_INTERFACE_MESSAGE_HEADER))
        event.wait()
        print("{} Data interface continues".format(DATA_INTERFACE_MESSAGE_HEADER))
        self.update_stocklist(initialize=True)


    def update_stocklist(self, initialize=False) -> None:
        try:
            if not initialize:
                message = self.queue.get()
                print("{} Read message '{}'".format(DATA_INTERFACE_MESSAGE_HEADER, message))

            if initialize or DATA_INTERFACE_MESSAGE_HEADER in message:
                print("{} Update stocklist!".format(DATA_INTERFACE_MESSAGE_HEADER))
                self.stocklist = self.read_data()
                self.working_stocklist = self.stocklist.head()
        except Empty:
            print("{} No message found, sleeping...".format(DATA_INTERFACE_MESSAGE_HEADER))
            time.sleep(2)
        except Exception as e:
            print("{} Something went wrong, got: {}".format(DATA_INTERFACE_MESSAGE_HEADER, e))


    def get_stocklist(self) -> pd.DataFrame:
        return self.stocklist


    def get_working_stocklist(self) -> pd.DataFrame:
        return self.working_stocklist


    def set_working_stocklist(self, num_stocks: str) -> None:
        if num_stocks.lower() == "all":
            self.working_stocklist = self.stocklist
        else:
            try:
                num_stocks = int(num_stocks)
                self.working_stocklist = self.stocklist.head(num_stocks)
            except Exception as e:
                print("{} Could not convert {} to an integer. Got {} instead. Will not update stocklist.".format(DATA_INTERFACE_MESSAGE_HEADER, num_stocks, e))


    def sort_working_stocklist(self, sort_variable: str, sort_direction: bool) -> bool:
        list_was_sorted = False
        if sort_variable in self.working_stocklist.columns:
            print("{} Sorting stocklist based on '{}'.".format(DATA_INTERFACE_MESSAGE_HEADER, sort_variable))
            self.working_stocklist = self.working_stocklist.sort_values(by=[sort_variable], ascending=sort_direction)
            list_was_sorted = True

        return list_was_sorted


    def merge_sector_and_industry_columns(self, stock_df: pd.DataFrame) -> pd.DataFrame:
        stock_df["Sector"] = stock_df["Sector_x"].combine_first(stock_df["Sector_y"])
        stock_df = stock_df.drop(["Sector_x", "Sector_y"], axis=1)
        stock_df["Industry"] = stock_df["Industry_x"].combine_first(stock_df["Industry_y"])
        stock_df = stock_df.drop(["Industry_x", "Industry_y"], axis=1)
        return stock_df


    def read_data(self) -> pd.DataFrame:
        top_stocks = pd.DataFrame()
        try:
            with self.lock:
                print("{} Reading data...".format(DATA_INTERFACE_MESSAGE_HEADER))
                movers = pd.read_pickle(Path.joinpath(DATA_FOLDER, "movers.pkl"))
                company_info = pd.read_pickle(Path.joinpath(DATA_FOLDER, "company_info.pkl"))
                twitter_data_bull_bear = pd.read_pickle(Path.joinpath(DATA_FOLDER, "twitter.pkl"))
                twitter_momentum = pd.read_pickle(Path.joinpath(DATA_FOLDER, "momentum.pkl"))

                # Merge with "how='outer'" to not remove any symbols
                top_stocks = movers.merge(company_info, on='Symbol', how='outer')
                top_stocks = top_stocks.merge(twitter_data_bull_bear, on='Symbol', how='outer')
                top_stocks = top_stocks.merge(twitter_momentum, on='Symbol', how='outer')
                top_stocks.drop(['Market Cap'], axis=1, inplace=True)
                top_stocks = self.merge_sector_and_industry_columns(top_stocks)
                print("{} Finished reading data...".format(DATA_INTERFACE_MESSAGE_HEADER))
        except Exception as e:
            print("{} Failed to read data, got {}".format(DATA_INTERFACE_MESSAGE_HEADER, e))

        return top_stocks
