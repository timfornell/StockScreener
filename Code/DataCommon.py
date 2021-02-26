import pandas as pd
import numpy as np
import multiprocessing as mp

from pathlib import Path
from pandas.core.reshape.merge import merge

from Definitions import *


class DataCommon():
    def __init__(self, lock: mp.Lock, queue: mp.Queue) -> None:
        self.lock = lock
        self.queue = queue


    def read_data(self) -> pd.DataFrame:
        """ To use this function the user must first acquire the file lock """
        stock_df = pd.DataFrame()
        try:
            print("{} Reading data...".format(DATA_COMMON_MESSAGE_HEADER))
            stock_df = pd.read_pickle(Path.joinpath(DATA_FOLDER, "{}.pkl".format(STOCKLIST_PICKLE_FILE)))
            print("{} Finished reading data...".format(DATA_COMMON_MESSAGE_HEADER))
        except Exception as e:
            print("{} Failed to read data, got {}".format(DATA_COMMON_MESSAGE_HEADER, e))

        return stock_df


    def write_data(self, stock_df: pd.DataFrame) -> None:
        try:
            print("{} Writing data...".format(DATA_COMMON_MESSAGE_HEADER))
            stock_df.to_pickle(Path.joinpath(DATA_FOLDER, "{}.pkl".format(STOCKLIST_PICKLE_FILE)))
            print("{} Finished writing data...".format(DATA_COMMON_MESSAGE_HEADER))
        except Exception as e:
            print("{} Failed to write data, got {}".format(DATA_COMMON_MESSAGE_HEADER, e))


    def update_data(self, updated_stock_df: pd.DataFrame) -> None:
        try:
            stock_df = self.read_data()

            for i, stock in updated_stock_df.iterrows():
                cols_with_values = stock.dropna()
                row_index = stock_df.index[stock_df["Symbol"] == stock["Symbol"]]
                for col, val in cols_with_values.iteritems():
                    if col != "Symbol":
                        stock_df.loc[row_index, col] = val

            self.write_data(stock_df)
        except Exception as e:
            print("{} Failed to update data, got {}".format(DATA_COMMON_MESSAGE_HEADER, e))